#!/usr/bin/env python3
"""arch-aggregate 增量变更检测：基于 SHA-1 内容哈希对比

用法：
  python3 check-changes.py detect   # 检测变更，输出详情
  python3 check-changes.py list     # 仅输出变更服务名（每行一个）
  python3 check-changes.py save     # 将当前哈希写入清单文件

清单文件位于 aggregate/.manifest.json，自动扫描 services/{服务名}/ 下所有 *.md 文件。
"""

import hashlib, json, sys
from pathlib import Path


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def build_current(services_dir: Path) -> dict:
    result = {}
    for svc in sorted(services_dir.iterdir()):
        if not svc.is_dir():
            continue
        hashes = {f.name: sha1(f) for f in sorted(svc.glob("*.md"))}
        if hashes:
            result[svc.name] = hashes
    return result


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_manifest(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def detect_changes(old: dict, new: dict) -> tuple[list, list]:
    changed, skipped = [], []
    for svc in sorted(new):
        if svc not in old or old[svc] != new[svc]:
            changed.append(svc)
        else:
            skipped.append(svc)
    for svc in sorted(set(old) - set(new)):
        changed.append(svc)
    return changed, skipped


def main():
    services_dir = Path("services")
    manifest_path = Path("aggregate/.manifest.json")

    if not services_dir.exists():
        print("错误：services/ 目录不存在", file=sys.stderr)
        sys.exit(1)

    old = load_manifest(manifest_path)
    new = build_current(services_dir)
    changed, skipped = detect_changes(old, new)

    mode = sys.argv[1] if len(sys.argv) > 1 else "detect"

    if mode == "detect":
        if not old:
            print("首次运行，无历史清单")
        print(f"变更服务({len(changed)})：{', '.join(changed) if changed else '无'}")
        print(f"跳过服务({len(skipped)})：{', '.join(skipped) if skipped else '无'}")
        for svc in changed:
            print(f"  ✓ {svc}")
        if not changed:
            print("所有服务文档无变更，无需重新聚合")
    elif mode == "list":
        for svc in changed:
            print(svc)
    elif mode == "save":
        save_manifest(manifest_path, new)
        print(f"清单已更新：{manifest_path}（{len(new)} 个服务）")
    else:
        print(f"用法: {sys.argv[0]} [detect|list|save]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
