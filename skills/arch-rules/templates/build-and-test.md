---
description: 项目构建、编译、测试命令
globs:
  - "**/pom.xml"
  - "**/*Test*.java"
---

# Build & Test

## Compile

```bash
# 全量编译
mvn compile -DskipTests

# 编译单个模块（含依赖模块）
mvn compile -pl {module-name} -am -DskipTests
```

## Test

```bash
# 运行全部测试
mvn test

# 运行单个模块的测试
mvn test -pl {module-name}

# 运行单个测试类
mvn test -pl {module-name} -Dtest=XxxTest
```

## Verify

```bash
# 检查编译是否通过（不跑测试）
mvn compile -DskipTests

# 检查是否有依赖冲突
mvn dependency:tree -pl {module-name}
```

