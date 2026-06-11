---
description: Layered architecture constraints, design principles, coding standards, pre-completion checklist
---

# Architecture & Design Rules

## Layered Architecture

The project follows a **Laravel pseudo-multi-module** architecture. All modules run within a single Laravel application and share the same database.

Dependency direction within each module: Http/Request → Action → Model → Event/Job

- **Http/Request layer**: Parameter validation and response formatting. MUST NOT contain business logic.
- **Action layer**: Business logic orchestration (equivalent to Service layer). All business rules MUST live here.
- **Model layer**: Eloquent models + relationships + Scopes + Accessor/Mutator. MUST NOT contain complex business logic. Simple attribute computation and state checks are acceptable.
- **Event/Listener layer**: Domain event decoupling. Listeners MUST delegate to Action classes, MUST NOT contain complex business logic.
- **Job layer**: Async tasks. The `handle()` method MUST delegate to Action classes. Jobs only handle parameter passing and retry configuration.

## Module Boundaries

- Modules MAY `use` classes from other modules, but MUST follow the principle of minimal dependency.
- Prefer referencing other modules' **Model** (read data) and **Action** (invoke business methods). MUST NOT reference other modules' **Request** classes.
- When calling cross-module Action methods, only invoke public methods. MUST NOT depend on internal implementation details.
- If module A's Listener needs to trigger module B's business logic, decouple via Event rather than direct invocation.

## Directory Convention

Each module lives under `modules/{module}/` with a standard layout. The exact subdirectories vary by project, but the layering principle is fixed:

| Layer | Typical directory | Responsibility |
|-------|------------------|----------------|
| Entry point | `src/ServiceProvider.php` | Module registration (routes, events, commands) |
| HTTP | `src/Http/Request/`, `src/Http/Routes/` | Parameter validation, routing, response formatting |
| Business logic | `src/Action/` | Core business rules (the ONLY place for business logic) |
| Domain model | `src/Models/` | Eloquent models, relationships, scopes |
| Events | `src/Events/`, `src/Listeners/` | Domain event definitions and handlers |
| Async | `src/Jobs/` | Queued tasks |
| CLI | `src/Commands/` | Artisan commands |
| Utilities | `src/Classes/` | Helpers, constants, third-party wrappers |
| Resources | `resources/` | Migrations, views, lang files |
| Tests | `tests/` | Test cases |

New files MUST be placed in the existing directory that matches their layer. MUST NOT create new subdirectories under `src/` without strong justification. When in doubt, scan the module's current structure first.

## Design Rules (MUST follow)

- MUST NOT use `array` as data contract between components. Use explicit DTO classes, Value Objects, or typed class properties. Plain arrays are unmaintainable — no IDE completion, no type safety, no documentation.
- MUST NOT pass data between components using generic key-value structures (`array`, `Collection` used as map, `stdClass`). Use explicit, named types.
- Single Responsibility: each class MUST have one and only one reason to change.
- Depend on abstractions, not implementations.
- MUST NOT navigate deep object graphs (Law of Demeter). Only talk to direct collaborators.
- If a conditional branch has more than 2 cases, MUST introduce polymorphism (Strategy pattern, match expression, or enum-based dispatch).
- MUST NOT use utility classes for business logic.
- MUST NOT use `instanceof` / type checking for behavior dispatch. Use polymorphism instead.

## Clean Code

- Prefer small functions (<30 lines), early return, avoid duplicated logic.
- Avoid nesting deeper than 2 levels.

## Coding Standards

- Database queries MUST avoid N+1 problems. Use `with()` for eager loading.
- Monetary calculations MUST use `bcmath` functions (`bcadd`, `bcmul`, etc.). MUST NOT use float arithmetic.
- Date/time MUST use Carbon. MUST NOT use `date()` or `strtotime()` directly.
- User input MUST go through Eloquent parameter binding or Query Builder parameterized queries. MUST NOT concatenate strings into SQL.

## Database Safety

- Every `UPDATE` and `DELETE` MUST have a `WHERE` clause. No full-table operations.
- Batch `DELETE` MUST have a `LIMIT` to prevent table locking.

## Pre-completion Checklist

Before reporting any task as done, MUST verify:

- [ ] No `array` used as data contract between components
- [ ] No direct coupling between modules (no Request/Listener/Middleware cross-references)
- [ ] No Law of Demeter violations (no deep object navigation)
- [ ] Each class has single responsibility
- [ ] Conditional branches > 2 cases use polymorphism, not if/else chains
- [ ] No utility classes containing business logic
- [ ] No N+1 query problems
- [ ] Monetary calculations use bcmath
- [ ] UPDATE/DELETE have WHERE clause
- [ ] New files in correct directory
