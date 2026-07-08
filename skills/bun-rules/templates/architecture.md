---
description: 设计原则、编码原则、API约定、完成检查清单
---

# 架构与设计规则


## 设计规则

- 单一职责：每个类承担单一职责
- 依赖抽象，而非实现
- 优先使用多态，而非复杂条件逻辑
- 单文件大小不应超过 500 行
- **禁止**使用 `Map`、`JSONObject` 或任何通用键值结构在组件间传递数据。必须使用显式、具名的类型
- **禁止**导航深度对象图（迪米特法则）。只与直接协作者通信
- **禁止**对业务逻辑使用工具类

## API 约定

- `Bun.serve()` supports WebSockets, HTTPS, and routes. Don't use `express`.
- `bun:sqlite` for SQLite. Don't use `better-sqlite3`.
- `Bun.redis` for Redis. Don't use `ioredis`.
- `Bun.sql` for Postgres. Don't use `pg` or `postgres.js`.
- `WebSocket` is built-in. Don't use `ws`.
- Prefer `Bun.file` over `node:fs`'s readFile/writeFile
- Bun.$`ls` instead of execa.
