---
description: Unit test conventions, build and compile commands
globs:
  - "**/*Test*.java"
  - "**/src/test/**/*.java"
  - "**/pom.xml"
---

# Unit Test & Build Conventions

## Build & Compile

```bash
# Full compile
mvn compile -DskipTests

# Compile single module (with dependencies)
mvn compile -pl {module-name} -am -DskipTests

# Check dependency conflicts
mvn dependency:tree -pl {module-name}
```

## Test Framework

- JUnit 5 + Mockito (via `spring-boot-starter-test`)
- JaCoCo for coverage
- Root pom may set `skipTests=true`; override with `-DskipTests=false`

## Test Class Structure

- `@ExtendWith(MockitoExtension.class)` — do NOT use `@SpringBootTest` for unit tests
- `@DisplayName` on class and every `@Test` method
- `@Mock` for dependencies, `@InjectMocks` for class under test
- Follow Given/When/Then pattern

## ErrorCodeChecker

When error codes are involved, extend `TestSupport`:

```java
public abstract class TestSupport {
    @BeforeEach
    void initServiceId() {
        ErrorCodeChecker.serviceId = "{serviceId}";
    }
}
```

## Test Placement

- Each module: `{module}/src/test/java/`, package mirrors source
- Naming: `{ClassName}Test`

## What to Test per Layer

| Layer | Test | Mock |
|-------|------|------|
| Domain Service | Business logic, fault isolation | Repository, other domain services |
| Repository Impl | DO↔PO conversion, mapper delegation | MyBatis Mapper |
| Application Service | Orchestration, null handling | Repository, Domain Service |
| Strategy / Evaluator | Core evaluate logic | Injected domain services |

## What NOT to Unit Test

PO/DO/DTO, Enums, MapStruct interfaces, Mapper XML, MQ Listeners, Controllers.

## Running Tests

```bash
# Single test class
mvn test -pl {module-name} -Dtest=XxxTest -DskipTests=false -DfailIfNoTests=false

# Multiple test classes
mvn test -pl {module-name} -Dtest="TestA,TestB" -DskipTests=false
```
