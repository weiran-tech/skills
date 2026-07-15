# /fe-workflow pr — CR 汇总 + commit 引导 + PR 创建

流水线完成后的提交出口。分两个阶段：**汇总检查**（默认执行）与 **git 操作**（仅在用户明确说"创建PR"/"提交PR"时执行）。

**Input**: `/fe-workflow pr`

## 阶段一：汇总检查（默认执行）

1. **读取 CR 结论**：verify-report.md 各功能章节的 QA+CR 结果（评分、C 类阻塞项处理情况）。存在未验证的功能（verify 非 done/skipped）→ 提示先跑 verify，CR 审查在其中完成，本命令不重复审查
2. **补充增量检查**：verify 之后工作区若还有新改动（对照 files_changed 与 `git status`），对增量部分做快速 CR（复用 stage-4 的 QA+CR 子代理规则）
3. **输出汇总**：

```markdown
### 提交前汇总
| # | 功能 | verify | e2e | C 类阻塞项 | 建议 commit |
|---|------|--------|-----|-----------|-------------|
| 1 | coupon-list | ✅ 8.6 | ✅ | 0 | feat(coupon): 新增优惠券列表 |

**按功能 commit 顺序建议**：{decisions 中的冲突顺序约定，或按 id 升序}
**风险评估**：{低/中/高}
```

- 无未处理阻塞项 → "可以提交。"
- 有 → "有 {N} 个阻塞问题需处理后再提交。"

**汇总完成后停止，不自动进入阶段二。**

## 阶段二：git 操作（仅用户明确要求时）

1. 检查当前分支，确认不在 master/main 上
2. **按功能分组逐个 commit**（依据各功能 files_changed 与建议 commit message，Angular 规范 `feat/fix/chore(scope): description`）
3. Push 到远程（**需用户确认**）
4. `gh pr create` 创建 PR，描述包含 Summary / Changes（按功能列出）/ Test Plan（引用 verify/e2e 结论）
5. 创建成功后提示（不自动执行）：
   > "PR 已创建。合并后请运行 `/fe-workflow release` 同步项目文档。"

## Guardrails

- 阶段一只汇总与增量检查，不重复 verify 已做的完整审查；发现的问题只报告
- git 操作必须逐步确认：commit → push → create PR 每步需用户同意
- 不 force push，不 push 到 master/main
- commit 按功能分组，不把多个功能混进一个 commit
