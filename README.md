## 安装

```
npx skills add weiran-tech/skills --skill devops-discuss
```

## 说明

```
bun-*         # bun 项目
java-ss-*     # Java 单独服务 Standalone Service
php-*         # PHP 相关
devops-*      # 开发相关
arch-*        # 架构部分
```

清单

```
# 前端
nuxt3-qa-analysis                : Nuxt3 项目分析
fe-backend-page                  : 后台页面
fe-kr36-ui-guide                 : UI 指南

# Weiran 框架
weiran-feature-module-workflow   : 功能模块全流程开发工作流（文档驱动七阶段）
weiran-openapi-writer            : OpenAPI 文档写作
weiran-project-qa-analysis       : 项目分析

# 架构
arch-analyzer                    : 架构分析
arch-publish                     : 架构发布

# 质量 / 工作流
devops-project-report                   : 项目报告
devops-sentry-exception                 : Sentry 异常输出
devops-aliyun-sls-stats                 : 阿里云 SLS 统计
devops-aliyun-sql-slow-log              : 阿里云 SQL 慢查询日志
devops-yunxiao-req-stats                : 云效需求统计
devops-yunxiao-bug-stats                : 云效 bug 统计
devops-yunxiao-req-ai-review            : 云效需求 AI 审核
devops-yunxiao-req-export-unplanned     : 云效需求导出未计划
devops-yunxiao-req-import               : 云效需求导入
devops-yunxiao-req-review-stats         : 云效需求审核统计

# 用例
devops-yunxiao-testcase-import          : 云效测试用例导入
devops-yunxiao-testcase-review          : 云效测试用例审核
```

## 开发

**软链接**

软链接到本地的 skills 目录

```
ln -s ~/project/of/weiran-tech/agent-skills/skills/nuxt3-qa-analysis ~/.agents/skills/nuxt3-qa-analysis
```

**Claude --add-dir**

启动的时候添加目录

```
claude --add-dir ~/project/of/weiran-tech/agent-skills/skills
```

