---
description: 项目构建、编译、测试命令
globs:
  - "**/*.[test|spec].ts[x]"
---

# Install & Build & Test


## Install & Run

Default to using Bun instead of Node.js.

- Use `bun <file>` instead of `node <file>` or `ts-node <file>`
- Use `bun build <file.html|file.ts|file.css>` instead of `webpack` or `esbuild`
- Use `bun install` instead of `npm install` or `yarn install` or `pnpm install`
- Use `bun run <script>` instead of `npm run <script>` or `yarn run <script>` or `pnpm run <script>`
- Use `bunx <package> <command>` instead of `npx <package> <command>`
- Bun automatically loads .env, so don't use dotenv.


```
# 安装
bun install

# 运行单个脚本
# bun run <script>
```

## Build

```bash
# 编译所有
bun run build

# 编译单个模块并删除中间文件
bun build ./src/git-commit.ts --compile --outfile ./bin/cmd.commit && rm -f .*.bun-build
```

## Test

编写测试文件需要

```ts
// index.test.ts
import { test, expect } from "bun:test";

test("hello world", () => {
  expect(1).toBe(1);
});
```

```bash
# 运行全部测试, 会查找 [test/tests] 目录下的测试文件 { *.[test|spec].ts[x]}
bun test
```


## Verify

```bash
# 检查编译是否通过（不跑测试）
mvn compile -DskipTests

# 检查是否有依赖冲突
mvn dependency:tree -pl {module-name}
```

