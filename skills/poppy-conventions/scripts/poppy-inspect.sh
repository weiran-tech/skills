#!/usr/bin/env bash
# poppy-inspect.sh — Bash-based pre-check for Poppy module code style.
#
# 镜像 `php artisan py-core:inspect` 中**纯静态**可判定的规则（命名、注释、文档块）。
# 不启动 Laravel/PHP runtime，可用于 pre-commit / 编辑器侧检查。
#
# 不覆盖的范围（必须跑原命令）：
#   - perms     需要路由表 + 菜单交叉对比
#   - seo       需要 \Route::getRoutes()
#   - trans     需要 trans() 实际取值
#   - validation 需要反射扫描 Rule 类方法
#
# 用法:
#   ./poppy-inspect.sh                          # 检查 ./poppy 下所有模块
#   ./poppy-inspect.sh -m poppy.system         # 仅 poppy.system 模块
#   ./poppy-inspect.sh -t file -t class        # 只跑指定类型
#   ./poppy-inspect.sh -r /path/to/poppy       # 指定 poppy 根目录
#
# 退出码: 0 = 全部通过, 1 = 有违规, 2 = 参数错误
set -uo pipefail

# ---------- defaults ----------
POPPY_ROOT="${POPPY_ROOT:-./poppy}"
SLUG=""
TYPES=()
EXIT_CODE=0

# ---------- color helpers ----------
if [[ -t 1 ]]; then
  RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; CYN=$'\033[36m'; BLD=$'\033[1m'; RST=$'\033[0m'
else
  RED=""; GRN=""; YLW=""; CYN=""; BLD=""; RST=""
fi

usage() {
  cat <<EOF
${BLD}poppy-inspect.sh${RST} — bash pre-check for Poppy module style

Usage: $0 [-r ROOT] [-m SLUG] [-t TYPE] [-h]

Options:
  -r ROOT   Poppy root directory (default: ./poppy)
  -m SLUG   Only check this module slug, e.g. poppy.system
  -t TYPE   Check type: file | class | controller | action | util
            (repeatable; default = all five)
  -h        Show this help

Check types:
  file        Events/Listeners/Policies 文件名后缀
  class       类/属性/方法 PHPDoc + camelCase 命名
  controller  Http/Request 下方法必须有 @api
  action      Action 类 public 业务方法必须有 PHPDoc
  util        Policy/Model 翻译键是否在 lang 文件中已注册
EOF
}

while getopts ":r:m:t:h" opt; do
  case "$opt" in
    r) POPPY_ROOT="$OPTARG" ;;
    m) SLUG="$OPTARG" ;;
    t) TYPES+=("$OPTARG") ;;
    h) usage; exit 0 ;;
    :) printf "${RED}option -%s 需要参数${RST}\n" "$OPTARG" >&2; usage; exit 2 ;;
    \?) printf "${RED}未知参数 -%s${RST}\n" "$OPTARG" >&2; usage; exit 2 ;;
  esac
done
[[ ${#TYPES[@]} -eq 0 ]] && TYPES=(file class controller action util)

# ---------- helpers ----------
slug_from_path() {
  # poppy/system -> poppy.system ; poppy/ext-alipay -> poppy.ext-alipay
  local rel="${1#$POPPY_ROOT/}"
  printf "%s" "${rel//\//.}"
}

slug_from_module_dir() {
  # 把 poppy 根下的模块目录 -> 对应 slug
  #   ./poppy/system       -> poppy.system
  #   ./poppy/ext-alipay   -> poppy.ext-alipay
  #   ./module/foo         -> module.foo (or 视具体仓库约定)
  local d="$1"
  local rest="${d#$POPPY_ROOT/}"
  rest="${rest#/}"
  if [[ -z "$rest" ]]; then printf ""; return; fi
  # 探测: 路径第一段是 poppy 还是 module
  local first="${rest%%/*}"
  local rest2=""
  if [[ "$rest" == */* ]]; then rest2="${rest#*/}"; fi
  case "$first" in
    poppy)
      printf "poppy.%s" "${rest2//\//.}"
      ;;
    module)
      printf "module.%s" "${rest2//\//.}"
      ;;
    *)
      # 不带 poppy/module 前缀的目录: 视为 poppy.<name>
      printf "poppy.%s" "${rest//\//.}"
      ;;
  esac
}

contains() { local needle="$1"; shift; for e in "$@"; do [[ "$e" == "$needle" ]] && return 0; done; return 1; }

is_camel_case() {
  local s="${1#\$}"
  [[ -z "$s" || "$s" =~ ^[0-9] ]] && return 1
  [[ "$s" =~ ^[a-z][a-zA-Z0-9]*$ ]]
}

violation() { printf "  ${RED}✗${RST} %s\n" "$1"; EXIT_CODE=1; }
passed()    { printf "  ${GRN}✓${RST} %s\n" "$1"; }
section()   { printf "\n${BLD}${YLW}── %s ──${RST}\n" "$1"; }
info()      { printf "  ${CYN}·${RST} %s\n" "$1"; }

# ---------- 1. file naming ----------
check_file_naming() {
  local module_dir="$1"
  local slug="$2"
  local dir suffix label bad_count
  while IFS='|' read -r dir suffix label; do
    [[ -z "$dir" ]] && continue
    local full="$module_dir/$dir"
    [[ -d "$full" ]] || continue
    bad_count=$(find "$full" -mindepth 1 -maxdepth 1 -type f -name '*.php' \
      ! -name "*${suffix}.php" | wc -l | tr -d ' ')
    if [[ "$bad_count" -gt 0 ]]; then
      violation "[${label}] ${bad_count} 个文件未以 '${suffix}.php' 结尾:"
      find "$full" -mindepth 1 -maxdepth 1 -type f -name '*.php' ! -name "*${suffix}.php" \
        | while IFS= read -r f; do printf "      %s\n" "${f#$POPPY_ROOT/}"; done
    else
      passed "${label}: 文件后缀规则通过 (${suffix}.php)"
    fi
  done <<'EOF'
src/Events|Event|Events
src/Listeners|Listener|Listeners
src/Models/Policies|Policy|Policies
EOF
}

# ---------- 2. class / property / method ----------
check_class() {
  local file="$1"
  local rel="${file#$POPPY_ROOT/}"

  # 跳过 ServiceProvider / functions.php / routes
  case "$file" in
    *functions.php|*/ServiceProvider.php|*/Http/Routes/*) return 0 ;;
  esac

  awk -v file="$rel" '
    function flush_method() {
      if (method_name != "") {
        if (!has_doc) printf "  [method-doc-missing] %s :: %s\n", file, method_name
      }
      method_name = ""; has_doc = 0
    }
    function flush_class() {
      if (class_name != "" && !class_has_doc) {
        printf "  [class-doc-missing] %s\n", file
      }
      class_name = ""; class_has_doc = 0
    }
    BEGIN { in_doc = 0; last_doc = "no" }
    # class declaration (BSD awk 不支持 \s, 用 [[:space:]])
    /^[[:space:]]*(abstract|final)?[[:space:]]*(class|interface|trait)[[:space:]]+[A-Za-z0-9_]/ {
      flush_method()
      class_name = $0
      class_has_doc = (last_doc == "yes")
      class_seen = 1
    }
    # method declaration
    /^[[:space:]]*(public|protected|private)?[[:space:]]*(static|abstract|final)*[[:space:]]+function[[:space:]]+[a-zA-Z0-9_]+/ {
      # extract function name from $NF or $0
      line = $0
      n = split(line, toks, /[[:space:]]+|\(/)
      mname = ""
      for (i = 1; i <= n; i++) if (toks[i] == "function") { mname = toks[i+1]; break }
      if (class_seen && mname != "__construct") {
        flush_class()
        method_name = mname
        has_doc = (last_doc == "yes")
      }
    }
    # docblock open
    /\/\*\*/ { in_doc = 1; last_doc = "yes"; next }
    in_doc && /\*\// { in_doc = 0; next }
    END { flush_class(); flush_method() }
  ' "$file"

  # @param 完整性: 紧邻 function 之前的 docblock
  awk -v file="$rel" '
    BEGIN { in_doc = 0 }
    {
      line = $0
      if (line ~ /\/\*\*/) { in_doc = 1; doc_buf = ""; next }
      if (in_doc && line ~ /\*\//) {
        in_doc = 0
        while ((getline nx) > 0) {
          if (nx ~ /^[[:space:]]*$/) continue
          if (nx ~ /function[[:space:]]+[a-zA-Z0-9_]+/) {
            n2 = split(nx, t2, /[[:space:]]+|\(/)
            mname = ""
            for (i = 1; i <= n2; i++) if (t2[i] == "function") { mname = t2[i+1]; break }
            if (mname !~ /^__/ && mname ~ /^[a-z]/) {
              m = split(doc_buf, dlines, "\n")
              for (i = 1; i <= m; i++) {
                if (dlines[i] ~ /@param/ && dlines[i] !~ /@param[[:space:]]+\??[A-Za-z\\|\\\\<>_]+[[:space:]]+\$[a-zA-Z0-9_]+[[:space:]]+\S+/) {
                  printf "  [param-incomplete] %s :: %s\n", file, mname
                  break
                }
              }
            }
          }
          break
        }
        next
      }
      if (in_doc) doc_buf = doc_buf "\n" line
    }
  ' "$file"
}

# ---------- 3. controller @api ----------
check_controller() {
  local file="$1"
  local rel="${file#$POPPY_ROOT/}"
  [[ "$file" == *"/Http/Request/"* ]] || return 0

  awk -v file="$rel" '
    BEGIN { in_doc = 0; has_api = 0 }
    /\/\*\*/ { in_doc = 1; has_api = 0; next }
    in_doc && /@api/ { has_api = 1 }
    in_doc && /\*\// {
      in_doc = 0
      while ((getline nx) > 0) {
        if (nx ~ /^[[:space:]]*$/) continue
        if (nx ~ /function[[:space:]]+/) {
          n = split(nx, p, /[[:space:]]+|\(/)
          mname = ""
          for (i = 1; i <= n; i++) if (p[i] == "function") { mname = p[i+1]; break }
          if (mname !~ /^__/ && !has_api) {
            printf "  [api-missing] %s :: %s\n", file, mname
          }
        }
        break
      }
      next
    }
  ' "$file"
}

# ---------- 4. action ----------
check_action() {
  local file="$1"
  local rel="${file#$POPPY_ROOT/}"
  [[ "$file" == *"/Action/"* ]] || return 0
  local base
  base=$(basename "$file")
  [[ "$base" == *Action.php ]] || return 0

  awk -v file="$rel" '
    BEGIN { in_doc = 0; has_doc = 0 }
    /\/\*\*/ { in_doc = 1; has_doc = 1; next }
    in_doc && /\*\// { in_doc = 0; next }
    /^[[:space:]]*public[[:space:]]+function[[:space:]]+[a-zA-Z0-9_]+/ {
      line = $0
      n = split(line, toks, /[[:space:]]+|\(/)
      mname = ""
      for (i = 1; i <= n; i++) if (toks[i] == "function") { mname = toks[i+1]; break }
      if (mname == "__construct" || mname ~ /^get[A-Z]/ || mname ~ /^set[A-Z]/) next
      if (!in_doc && !has_doc) {
        printf "  [action-doc-missing] %s :: %s\n", file, mname
      }
      has_doc = 0
    }
  ' "$file"
}

# ---------- 5. util trans keys ----------
check_util() {
  local module_dir="$1"
  local slug="$2"
  local lang_dir="$module_dir/resources/lang"
  [[ -d "$lang_dir" ]] || { info "util: 未找到 resources/lang (跳过)"; return 0; }

  local prefix
  if [[ "$slug" == poppy.* ]]; then
    local rest="${slug#poppy.}"
    prefix="py-$(echo "$rest" | tr '[:upper:]' '[:lower:]')"
  else
    prefix="${slug#module.}"
  fi

  # 收集 lang 文件中所有翻译键
  declare -A registered=()
  while IFS= read -r -d '' f; do
    while IFS= read -r line; do
      if [[ "$line" =~ ^[[:space:]]*[\'\"]?([a-zA-Z0-9_.-]+)[\'\"]?[[:space:]]*=\> ]]; then
        registered["${BASH_REMATCH[1]}"]=1
      fi
    done < "$f"
  done < <(find "$lang_dir" -type f -name '*.php' -print0)

  local missing=0
  local expected_keys=()

  # Policy 方法键
  local policies_dir="$module_dir/src/Models/Policies"
  if [[ -d "$policies_dir" ]]; then
    while IFS= read -r pf; do
      local base model snake
      base=$(basename "$pf" .php)
      model="${base%Policy}"
      snake=$(echo "$model" | sed -E 's/([a-z0-9])([A-Z])/\1_\2/g' | tr '[:upper:]' '[:lower:]')
      while IFS= read -r method; do
        [[ -z "$method" ]] && continue
        expected_keys+=("${prefix}::util.policy.${snake}.${method}")
      done < <(awk '
        BEGIN { in_doc = 0 }
        /\/\*\*/ { in_doc = 1; next }
        in_doc && /\*\// { in_doc = 0; next }
        /^\s*public\s+function\s+([a-zA-Z0-9_]+)/ {
          m = $0; sub(/.*function\s+/, "", m); sub(/\(.*/, "", m)
          if (m == "before" || m == "after" || m ~ /^__/) next
          print m
        }
      ' "$pf")
    done < <(find "$policies_dir" -mindepth 1 -maxdepth 1 -type f -name '*Policy.php')
  fi

  # Model 名称键
  local models_dir="$module_dir/src/Models"
  if [[ -d "$models_dir" ]]; then
    while IFS= read -r mf; do
      [[ "$mf" == *"/Policies/"* ]] && continue
      local base snake
      base=$(basename "$mf" .php)
      snake=$(echo "$base" | sed -E 's/([a-z0-9])([A-Z])/\1_\2/g' | tr '[:upper:]' '[:lower:]')
      expected_keys+=("${prefix}::util.classes.models.${snake}")
    done < <(find "$models_dir" -mindepth 1 -maxdepth 1 -type f -name '*.php')
  fi

  # 比对
  for key in "${expected_keys[@]:-}"; do
    [[ -z "$key" ]] && continue
    if [[ -z "${registered[$key]:-}" ]]; then
      violation "[util-missing] 翻译键缺失: $key"
      missing=$((missing + 1))
    fi
  done

  if [[ $missing -eq 0 && ${#expected_keys[@]} -gt 0 ]]; then
    passed "util: ${#expected_keys[@]} 个翻译键全部注册"
  elif [[ ${#expected_keys[@]} -eq 0 ]]; then
    info "util: 模块无 Policy/Model，跳过"
  fi
}

# ---------- run ----------
if [[ ! -d "$POPPY_ROOT" ]]; then
  printf "${RED}poppy 根目录不存在: %s${RST}\n" "$POPPY_ROOT" >&2
  exit 2
fi

# 识别模块: 找包含 src/*ServiceProvider.php 或 src/composer.json 的目录
mapfile -t module_dirs < <(find "$POPPY_ROOT" -mindepth 2 -maxdepth 2 -type d -name 'src' \
  ! -path '*/vendor/*' ! -path '*/node_modules/*' \
  | while read -r d; do
      # glob: 任何 *ServiceProvider.php 都算
      if compgen -G "$d/*ServiceProvider.php" > /dev/null \
         || compgen -G "$d/composer.json" > /dev/null; then
        dirname "$d"
      fi
    done | sort -u)

if [[ ${#module_dirs[@]} -eq 0 ]]; then
  printf "${RED}未在 %s 下找到任何 poppy 模块 (需要 src/ServiceProvider.php)${RST}\n" "$POPPY_ROOT" >&2
  exit 2
fi

printf "${BLD}${CYN}poppy-inspect${RST}  root=%s  module=%s  types=%s\n" \
  "$POPPY_ROOT" "${SLUG:-ALL}" "${TYPES[*]}"

for module_dir in "${module_dirs[@]}"; do
  slug=$(slug_from_module_dir "$module_dir")
  should_check() { [[ -z "$SLUG" || "$1" == "$SLUG" ]]; }
  should_check "$slug" || continue

  printf "\n${BLD}${CYN}┌─ %s ─┐${RST}\n" "$slug"

  if contains file "${TYPES[@]}"; then
    section "file naming"
    check_file_naming "$module_dir" "$slug"
  fi

  if contains class "${TYPES[@]}"; then
    section "class / property / method doc"
    local_module_dir="$module_dir"
    while IFS= read -r f; do
      check_class "$f"
    done < <(find "$module_dir/src" -type f -name '*.php' \
      ! -path '*/Http/Routes/*' ! -name 'functions.php')
  fi

  if contains controller "${TYPES[@]}"; then
    section "controller @api"
    while IFS= read -r f; do
      check_controller "$f"
    done < <(find "$module_dir/src/Http/Request" -type f -name '*.php' 2>/dev/null)
  fi

  if contains action "${TYPES[@]}"; then
    section "action method doc"
    while IFS= read -r f; do
      check_action "$f"
    done < <(find "$module_dir/src/Action" -type f -name '*Action.php' 2>/dev/null)
  fi

  if contains util "${TYPES[@]}"; then
    section "util trans keys"
    check_util "$module_dir" "$slug"
  fi
done

printf "\n${BLD}── Summary ──${RST}\n"
if [[ $EXIT_CODE -eq 0 ]]; then
  printf "${GRN}All passed.${RST}\n"
else
  printf "${RED}Violations found. 退出码 = %d${RST}\n" "$EXIT_CODE"
fi

exit "$EXIT_CODE"
