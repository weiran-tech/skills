---
description: DDD 分层架构约束、设计原则、编码标准、完成检查清单
---

# Architecture & Design Rules

## DDD + Clean Architecture

The project follows **DDD + Clean Architecture**.

Dependency direction: Adapter → Application → Domain ← Infrastructure

- Domain layer MUST NOT import any framework. It only contains: entities, domain services, repository interfaces, domain events, enums, constants.
- Repository interfaces MUST live in domain; implementations MUST live in infrastructure.
- Application Services MUST only orchestrate use cases. MUST NOT contain business rules.
- Controllers MUST only do parameter conversion and auth. MUST NOT contain business logic.
- Each bounded context MUST maintain its own layering, MUST NOT reference other contexts' internal classes.

## Domain Model

Domain entities MUST contain behavior. MUST NOT create anemic models (data-only classes with logic in external services).

## Design Rules (MUST follow)

- Business logic MUST live inside domain objects.
- MUST NOT pass data between components using `Map`, `JSONObject`, or any generic key-value structure. Use explicit, named types.
- Single Responsibility: each class MUST have one and only one reason to change.
- Depend on abstractions, not implementations.
- MUST NOT navigate deep object graphs (Law of Demeter). Only talk to direct collaborators.
- Prefer polymorphism over complex conditional logic.
- MUST NOT use utility classes for business logic.

## Clean Code

- Prefer small functions (<30 lines), early return, avoid duplicated logic.
- Avoid nesting deeper than 2 levels.

## Mapper XML Safety Rules

1. **WHERE required** — Every `SELECT`, `UPDATE`, `DELETE` MUST have a `WHERE` clause. No full-table operations.
2. **LIMIT required** — Every `SELECT`, `UPDATE`, `DELETE` MUST have a `LIMIT`. Single-row operations use `limit 1`; list queries use a reasonable upper bound or parameterized limit; batch `DELETE` with `IN` clause uses `limit #{size}`.
3. **Idempotent INSERT** — Use `INSERT IGNORE` when leveraging unique keys for idempotency.
4. **Structure** — Define `<resultMap id="BaseResultMap">` and `<sql id="Base_Column_List">` in every mapper XML. Batch DELETE mapper method MUST accept `@Param("size") Integer size` for the parameterized limit.

## Development Workflow

Before implementing non-trivial logic, briefly design domain behavior and abstractions.

## Pre-completion Checklist

Before reporting any task as done, MUST verify:

- [ ] No framework imports in domain layer
- [ ] Domain entities contain behavior, not just data
- [ ] Controllers and application services contain no business rules
- [ ] No `Map`/`JSONObject` as data contract
- [ ] No Law of Demeter violations (no deep object navigation)
- [ ] Each class has single responsibility
- [ ] Repository interfaces in domain, implementations in infrastructure