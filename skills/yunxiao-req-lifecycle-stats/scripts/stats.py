#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
统计云效项目中需求生命周期。

接收两种输入模式：
A) 传统模式：全量 items，本地遍历统计
   json_file 格式: [{"workitemType": {"name": "..."}, ...}, ...]
B) 分页优先模式：来自 Step 0-4 的统计数据 + 明细清单
   json_file 格式: {"_counts": {...}, "_items": [...], "_pagination": {...}}

当存在 _counts 时优先使用，否则回退到 A 模式遍历所有 items。
"""

import json
import sys
import re
import datetime
from typing import Dict, List, Any


def parse_days(days_str: str) -> tuple[str, int, int]:
    """解析自然语言日期字符串为 (展示标签, 开始时间戳, 结束时间戳)"""
    today = datetime.datetime.now(tz=datetime.timezone.utc).date()
    s = days_str.strip().lower()

    if s in ("昨天", "yesterday"):
        d = today - datetime.timedelta(days=1)
        start = datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc)
        end = start + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
        return f"{d.isoformat()}", int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    if s in ("今天", "today"):
        start = datetime.datetime(today.year, today.month, today.day, tzinfo=datetime.timezone.utc)
        end = start + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
        return f"{today.isoformat()}", int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    m = re.match(r'(最近|近)\s*(\d+)\s*天|(\d+)\s*days?', s)
    if m:
        n = int(m.group(2) or m.group(3))
        end = datetime.datetime(today.year, today.month, today.day, tzinfo=datetime.timezone.utc)
        end = end + datetime.timedelta(hours=23, minutes=59, seconds=59) - datetime.timedelta(milliseconds=1)
        start_dt = today - datetime.timedelta(days=n - 1)
        start = datetime.datetime(start_dt.year, start_dt.month, start_dt.day, tzinfo=datetime.timezone.utc)
        label = f"{start_dt.isoformat()} - {today.isoformat()}"
        return label, int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    m = re.match(r'(\d{4}-\d{2}-\d{2})\s*[-~→]\s*(\d{4}-\d{2}-\d{2})', s)
    if m:
        ds, de = m.group(1), m.group(2)
        start = datetime.datetime(int(ds[:4]), int(ds[5:7]), int(ds[8:10]), tzinfo=datetime.timezone.utc)
        end_date = datetime.date(int(de[:4]), int(de[5:7]), int(de[8:10]))
        end = datetime.datetime(end_date.year, end_date.month, end_date.day, tzinfo=datetime.timezone.utc)
        end = end + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
        return f"{ds} - {de}", int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    # 默认：本月至今
    start = datetime.datetime(today.year, today.month, 1, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(today.year, today.month, today.day, tzinfo=datetime.timezone.utc)
    end = end + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
    return f"{today.month}月", int(start.timestamp() * 1000), int(end.timestamp() * 1000)


CLOSED_STAGES = {"4", "5"}

PRIORITY_MAP = {
    "1": "紧急",
    "2": "高",
    "3": "中",
    "4": "低",
}


def get_review_conclusion(custom_field_values: list) -> str:
    """从自定义字段中提取评审结论"""
    for cf in custom_field_values or []:
        if cf.get("fieldName") == "评审结论" and cf.get("values"):
            val = cf["values"][0].get("displayValue", "").strip()
            if val:
                return val
    return ""


def classify(item: dict) -> str:
    """判断需求类型：product / technical / unknown"""
    wtype = item.get("workitemType") or {}
    name = wtype.get("name", "") or ""
    if "产品" in name:
        return "product"
    if "技术" in name:
        return "technical"
    return "unknown"


def analyze_stats(json_file_path: str, days_label: str, use_pagination: bool = False) -> dict:
    _, start_ts, end_ts = parse_days(days_label)

    with open(json_file_path, "r") as f:
        data = json.load(f)

    # 支持两种输入格式
    has_counts = isinstance(data, dict) and "_counts" in data
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []

    # 过滤出有效类型的项
    valid_items = [item for item in items if classify(item) in ("product", "technical")]

    if has_counts:
        # 分页优先模式：使用来自 MCP pagination.total 的统计数据
        counts = data["_counts"]
        reviewed_pending = []

        for item in data.get("_items", []):
            ctype = classify(item)
            if ctype not in ("product", "technical"):
                continue
            stage = str(item.get("statusStageIdentifier", "") or item.get("statusStageId", ""))
            review = get_review_conclusion(item.get("customFieldValues", []))
            is_closed = stage in CLOSED_STAGES
            if review and not is_closed:
                reviewed_pending.append({**item, "_type": ctype, "_review": review})

        return {
            "not_reviewed_product": counts.get("not_reviewed_product", 0),
            "not_reviewed_technical": counts.get("not_reviewed_technical", 0),
            "created_product": counts.get("created_product", 0),
            "created_technical": counts.get("created_technical", 0),
            "closed_product": counts.get("closed_product", 0),
            "closed_technical": counts.get("closed_technical", 0),
            "reviewed_pending": reviewed_pending,
            "days_label": days_label,
        }
    else:
        # 传统模式：遍历 all items 本地统计
        not_reviewed = []
        created_count_product = 0
        created_count_technical = 0
        closed_count_product = 0
        closed_count_technical = 0
        reviewed_pending = []

        for item in valid_items:
            ctype = classify(item)
            stage = str(item.get("statusStageIdentifier", "") or item.get("statusStageId", ""))
            gmt_create_ms = item.get("gmtCreate") or 0
            gmt_status_changed_ms = item.get("gmtStatusChanged") or 0
            review = get_review_conclusion(item.get("customFieldValues", []))
            is_closed = stage in CLOSED_STAGES

            # 1. 未评审：未关闭 且 无评审结论
            if not is_closed and not review:
                not_reviewed.append({**item, "_type": ctype})

            # 2. 创建于范围内
            if start_ts <= gmt_create_ms <= end_ts:
                if ctype == "product":
                    created_count_product += 1
                else:
                    created_count_technical += 1

            # 3. 关闭于范围内
            if is_closed and start_ts <= gmt_status_changed_ms <= end_ts:
                if ctype == "product":
                    closed_count_product += 1
                else:
                    closed_count_technical += 1

            # 4. 已评审待计划
            if review and not is_closed:
                reviewed_pending.append({**item, "_type": ctype, "_review": review})

        return {
            "not_reviewed": not_reviewed,
            "not_reviewed_product": sum(1 for x in not_reviewed if x["_type"] == "product"),
            "not_reviewed_technical": sum(1 for x in not_reviewed if x["_type"] == "technical"),
            "created_product": created_count_product,
            "created_technical": created_count_technical,
            "closed_product": closed_count_product,
            "closed_technical": closed_count_technical,
            "reviewed_pending": reviewed_pending,
            "days_label": days_label,
        }


def gmt_create_str(ts) -> str:
    try:
        dt = datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def print_result(stats: dict, organization_id: str = ""):
    label = stats["days_label"]

    nr_product = stats["not_reviewed_product"]
    nr_technical = stats["not_reviewed_technical"]
    nr_total = nr_product + nr_technical

    cr_product = stats["created_product"]
    cr_technical = stats["created_technical"]

    cl_product = stats["closed_product"]
    cl_technical = stats["closed_technical"]

    rp = stats["reviewed_pending"]
    rp_product = sum(1 for x in rp if x["_type"] == "product")
    rp_technical = sum(1 for x in rp if x["_type"] == "technical")

    # Section 1: Overview table
    print(f"""| 统计项                               | 数量  |
| ------------------------------------ | ----- |
| **未评审需求总数**                   | **{nr_total}** |
| └ 产品类需求                         | {nr_product}     |
| └ 技术类需求                         | {nr_technical}     |
| **`{label}`创建需求总数**            | **{cr_product + cr_technical}** |
| └ 产品类需求                         | {cr_product}     |
| └ 技术类需求                         | {cr_technical}     |
| **`{label}`关闭需求总数**            | **{cl_product + cl_technical}** |
| └ 产品类需求                         | {cl_product}     |
| └ 技术类需求                         | {cl_technical}     |""")

    # Section 2: Reviewed but pending summary
    print(f"""
## 已评审待计划需求

| 统计项               | 数量  |
| -------------------- | ----- |
| **已评审待计划总数** | **{len(rp)}** |
| └ 产品类需求         | {rp_product}     |
| └ 技术类需求         | {rp_technical}     |""")

    # Section 3: Detailed list
    if rp:
        print("\n## 已评审待计划清单\n")
        print("| ID | 标题 | 负责人 | 优先级 | 创建时间 | 评审结论 | 链接 |")
        print("|-----|------|--------|--------|----------|----------|------|")
        for item in rp:
            identifier = item.get("identifier", "")
            subject = item.get("subject", "")
            assigned = item.get("assignedTo")
            assignee_name = ""
            if isinstance(assigned, list) and assigned:
                assignee_name = assigned[0].get("name", "")
            elif isinstance(assigned, dict):
                assignee_name = assigned.get("name", "")
            priority = PRIORITY_MAP.get(str(item.get("priorityIdentifier", "")), "")
            create_time = gmt_create_str(item.get("gmtCreate", 0))
            review = item.get("_review", "")
            link = ""
            if organization_id and identifier:
                link = f"[详细](https://devops.aliyun.com/organization/{organization_id}/work/workitems/{identifier})"
            elif identifier:
                link = identifier
            print(f"| {identifier} | {subject} | {assignee_name} | {priority} | {create_time} | {review} | {link} |")
    else:
        print("\n*暂无已评审待计划的需求。*")


def parse_days_cli(days_str: str):
    """CLI mode: output date range as JSON for MCP parameter construction"""
    _label, start_ms, end_ms = parse_days(days_str)
    start_iso = datetime.datetime.fromtimestamp(start_ms / 1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
    end_iso = datetime.datetime.fromtimestamp(end_ms / 1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
    result = {"label": _label, "start_iso": start_iso, "end_iso": end_iso}
    print(json.dumps(result, ensure_ascii=False))


def main():
    # Support --parse-days flag for CLI usage
    if len(sys.argv) >= 3 and sys.argv[1] == "--parse-days":
        parse_days_cli(sys.argv[2])
        return

    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <json-file> \"<range>\" [organization_id]")
        print(f"       {sys.argv[0]} --parse-days \"<range>\"")
        print("  range examples: \"昨天\", \"最近7天\", \"2026-05-01 - 2026-05-11\", \"\" (本月)")
        sys.exit(1)

    json_file = sys.argv[1]
    days_label = sys.argv[2]
    organization_id = sys.argv[3] if len(sys.argv) > 3 else ""

    stats = analyze_stats(json_file, days_label)
    print_result(stats, organization_id)


if __name__ == "__main__":
    main()
