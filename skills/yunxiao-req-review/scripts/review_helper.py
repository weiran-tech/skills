#!/usr/bin/env python3
"""
需求评审辅助脚本
可被其他技能调用，提供标准化的需求评审功能
"""

import json
from typing import Dict, List, Optional

# 评分标准配置
SCORING_CRITERIA = [
    {
        "dimension": "业务背景与价值",
        "item": "背景描述是否清晰，说明了当前业务痛点或机会",
        "weight": 0.10,
        "score0": "未填写或仅有标题",
        "score1": "有描述但缺乏具体场景",
        "score2": "清晰描述痛点、场景和触发原因"
    },
    {
        "dimension": "业务背景与价值",
        "item": "业务价值是否明确（用户价值 / 商业价值）",
        "weight": 0.10,
        "score0": "未提及价值",
        "score1": "泛泛而谈，无具体说明",
        "score2": "明确指出对用户或业务的价值"
    },
    {
        "dimension": "业务目标与收益",
        "item": "目标是否可量化（有数据指标）",
        "weight": 0.10,
        "score0": "无目标描述",
        "score1": "有目标但无数据支撑",
        "score2": "包含具体指标（如转化率/GMV/DAU）"
    },
    {
        "dimension": "业务目标与收益",
        "item": "收益影响范围是否可评估",
        "weight": 0.10,
        "score0": "未提及",
        "score1": "范围模糊",
        "score2": "明确说明影响的业务范围和预期收益"
    },
    {
        "dimension": "模块影响范围",
        "item": "主业务模块及受影响模块是否列出",
        "weight": 0.08,
        "score0": "未填写",
        "score1": "只列出主模块",
        "score2": "主模块 + 所有受影响模块均已列出"
    },
    {
        "dimension": "模块影响范围",
        "item": "下游依赖 / 数据流影响是否已识别",
        "weight": 0.07,
        "score0": "未提及",
        "score1": "部分识别",
        "score2": "完整识别数据流和服务依赖"
    },
    {
        "dimension": "需求描述完整性",
        "item": "描述是否无歧义，开发侧可直接理解意图",
        "weight": 0.09,
        "score0": "描述模糊，多处歧义",
        "score1": "大致能理解但有模糊点",
        "score2": "语义清晰，开发无需追问"
    },
    {
        "dimension": "需求描述完整性",
        "item": "是否覆盖主流程 + 异常流程 / 边界场景",
        "weight": 0.09,
        "score0": "仅有主流程或完全缺失",
        "score1": "有主流程，异常场景不完整",
        "score2": "主流程 + 关键异常 + 边界场景均覆盖"
    },
    {
        "dimension": "需求描述完整性",
        "item": "是否包含 URL / 原型 / 示意图等参考资料",
        "weight": 0.07,
        "score0": "无任何参考",
        "score1": "有部分参考链接",
        "score2": "有完整参考资料（原型图/流程图/URL）"
    },
    {
        "dimension": "验收标准质量",
        "item": "验收项是否具体可测试（非泛泛描述）",
        "weight": 0.07,
        "score0": "无验收标准或全部模糊",
        "score1": "部分验收项可测试",
        "score2": "全部验收项可直接转为测试用例"
    },
    {
        "dimension": "验收标准质量",
        "item": "验收项数量是否充分（≥3条）",
        "weight": 0.07,
        "score0": "0–1条",
        "score1": "2条",
        "score2": "3条及以上"
    },
    {
        "dimension": "验收标准质量",
        "item": "是否包含非功能验收项（性能/安全/兼容）",
        "weight": 0.06,
        "score0": "无",
        "score1": "提及但不具体",
        "score2": "有明确的非功能验收指标"
    }
]

# 评级标准
RATING_CRITERIA = [
    {"min": 90, "max": 100, "rating": "优秀", "icon": "✓"},
    {"min": 75, "max": 89, "rating": "良好", "icon": "↑"},
    {"min": 55, "max": 74, "rating": "待改进", "icon": "⚠"},
    {"min": 0, "max": 54, "rating": "不通过", "icon": "✗"}
]


def calculate_total_score(scores: List[int]) -> Dict:
    """
    计算总分和评级

    Args:
        scores: 12项评分结果的列表（0-2分）

    Returns:
        包含总分、评级和详细得分的字典
    """
    if len(scores) != 12:
        raise ValueError("需要提供12项评分结果")

    total_score = 0
    score_details = []

    for i, (score, criteria) in enumerate(zip(scores, SCORING_CRITERIA)):
        weighted_score = score * criteria["weight"]
        total_score += weighted_score

        score_details.append({
            "dimension": criteria["dimension"],
            "item": criteria["item"],
            "score": score,
            "weight": criteria["weight"],
            "weighted_score": weighted_score
        })

    # 转换为百分制
    total_percent = int(round(total_score * 100, 0))

    # 确定评级
    rating = "未知"
    for rc in RATING_CRITERIA:
        if rc["min"] <= total_percent <= rc["max"]:
            rating = rc["rating"]
            break

    return {
        "total_score": total_percent,
        "rating": rating,
        "score_details": score_details
    }


def get_response_template(rating: str, total_score: int, issues: Optional[List[str]] = None) -> str:
    """
    根据评级获取回复模板

    Args:
        rating: 评级（优秀/良好/待改进/不通过）
        total_score: 总分
        issues: 问题列表（用于良好/待改进/不通过评级）

    Returns:
        格式化的回复文本
    """
    if rating == "优秀":
        return f"本次需求评审通过，总分 {total_score}/100。业务目标清晰，需求描述完整，验收标准可测试，可进入排期评估阶段。"

    elif rating == "良好":
        issue_list = "\n".join([f"{i+1}. {issue}" for i, issue in enumerate(issues or [])]) if issues else "1. [请补充具体问题]"
        return f"""本次需求基本通过，总分 {total_score}/100，有以下几处需在评审会前补充完善：
{issue_list}
请在 {{日期}} 前更新需求文档后，重新知会评审人。"""

    elif rating == "待改进":
        issue_list = "\n".join([f"{i+1}. {issue}" for i, issue in enumerate(issues or [])]) if issues else "1. [请补充关键缺失项]"
        return f"""本次需求暂不通过，总分 {total_score}/100，存在以下关键缺失：
{issue_list}
建议驳回重新梳理后再次提交。如有疑问请与产品负责人沟通。"""

    else:  # 不通过
        core_issue = issues[0] if issues else "需求信息严重不足"
        return f"""本次需求评审不通过，总分 {total_score}/100。需求信息严重不足，无法支撑有效评审。
主要问题：{core_issue}
请重新梳理业务目标、需求描述和验收标准后再次提交。"""


def generate_quick_review_result(check_results: List[Dict]) -> Dict:
    """
    生成快速评审结果

    Args:
        check_results: 5项检查结果列表，每项包含{conclusion, description}

    Returns:
        快速评审结果字典
    """
    check_items = [
        "业务背景清晰",
        "可量化目标",
        "描述无歧义",
        "覆盖异常场景",
        "验收标准可测"
    ]

    passed_count = sum(1 for r in check_results if r["conclusion"] == "是")
    conclusion = "通过初筛" if passed_count >= 4 else "需补充后重新提交"

    # 找出最关键的缺失
    missing_items = [f"{i+1}. {check_items[i]}" for i, r in enumerate(check_results) if r["conclusion"] == "否"]
    key_missing = missing_items[0] if missing_items else "无"

    return {
        "check_results": check_results,
        "passed_count": passed_count,
        "total_count": len(check_items),
        "conclusion": conclusion,
        "key_missing": key_missing
    }


if __name__ == "__main__":
    # 示例：测试评分计算
    test_scores = [2, 2, 1, 2, 2, 1, 2, 2, 1, 2, 2, 1]
    result = calculate_total_score(test_scores)
    print(json.dumps(result, ensure_ascii=False, indent=2))
