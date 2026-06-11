#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
统计云效项目中线上故障。

接收两种输入模式：
A) 传统模式：全量 items，本地遍历统计
   json_file 格式: [{"workitemType": {"name": "..."}, ...}, ...]
B) 分页优先模式：来自 Step 1-4 的统计数据 + 明细清单
   json_file 格式: {"_counts": {...}, "_items": [...]}

当存在 _counts 时优先使用，否则回退到 A 模式遍历所有 items。
"""

import json
import sys
import re
import datetime
from typing import Dict, List
from collections import defaultdict


def parse_days(days_str: str) -> tuple[str, int, int]:
    """解析自然语言日期字符串为 (展示标签, 开始时间戳, 结束时间戳)

    Returns:
        (display_label, start_ts_ms, end_ts_ms)
    """
    today = datetime.datetime.now(tz=datetime.timezone.utc).date()
    s = days_str.strip().lower()

    # "昨天"
    if s in ("昨天", "yesterday"):
        d = today - datetime.timedelta(days=1)
        start = datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc)
        end = start + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
        return f"{d.isoformat()}", int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    # "今天"
    if s in ("今天", "today"):
        start = datetime.datetime(today.year, today.month, today.day, tzinfo=datetime.timezone.utc)
        end = start + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
        return f"{today.isoformat()}", int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    # "最近 N 天" / "近 N 天" / "last N days"
    m = re.match(r'(最近|近)\s*(\d+)\s*天|(\d+)\s*days?', s)
    if m:
        n = int(m.group(2) or m.group(3))
        end = datetime.datetime(today.year, today.month, today.day, tzinfo=datetime.timezone.utc)
        end = end + datetime.timedelta(hours=23, minutes=59, seconds=59) - datetime.timedelta(milliseconds=1)
        start_dt = today - datetime.timedelta(days=n - 1)
        start = datetime.datetime(start_dt.year, start_dt.month, start_dt.day, tzinfo=datetime.timezone.utc)
        label = f"{start_dt.isoformat()} - {today.isoformat()}"
        return label, int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    # 显式日期范围 "YYYY-MM-DD - YYYY-MM-DD"
    m = re.match(r'(\d{4}-\d{2}-\d{2})\s*[-~→]\s*(\d{4}-\d{2}-\d{2})', s)
    if m:
        ds, de = m.group(1), m.group(2)
        start = datetime.datetime(int(ds[:4]), int(ds[5:7]), int(ds[8:10]), tzinfo=datetime.timezone.utc)
        end_date = datetime.date(int(de[:4]), int(de[5:7]), int(de[8:10]))
        end = datetime.datetime(end_date.year, end_date.month, end_date.day, tzinfo=datetime.timezone.utc)
        end = end + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
        return f"{ds} - {de}", int(start.timestamp() * 1000), int(end.timestamp() * 1000)

    # "本月至今" 或空 → 当月1日到今天
    start = datetime.datetime(today.year, today.month, 1, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(today.year, today.month, today.day, tzinfo=datetime.timezone.utc)
    end = end + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
    return f"{today.month}月", int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def get_priority_emoji(priority: str) -> str:
    """根据优先级获取 Emoji"""
    priority_map = {
        '紧急': '🔴',
        '高': '🟠',
        '中': '🟡',
        '低': '🟢',
        '最高': '🔴',
        '较高': '🟠',
        '普通': '🟡',
        '较低': '🟢',
    }
    for key, emoji in priority_map.items():
        if key in priority:
            return emoji
    return '⚪'


def get_severity_emoji(severity: str) -> str:
    """根据严重程度获取 Emoji"""
    severity_map = {
        '致命': '💥',
        '严重': '🔥',
        '一般': '⚠️',
        '轻微': '📝',
        '1-': '💥',
        '2-': '🔥',
        '3-': '⚠️',
        '4-': '📝',
    }
    for key, emoji in severity_map.items():
        if key in severity:
            return emoji
    return '⚪'


def get_status_emoji(status: str) -> str:
    """根据状态获取 Emoji"""
    status_map = {
        '待确认': '❓',
        '待处理': '📋',
        '处理中': '🔧',
        '进行中': '🔧',
        '已修复': '✅',
        '已解决': '✅',
        '挂起中': '⏸️',
        '暂停': '⏸️',
        '已关闭': '🔒',
        '开发中': '💻',
        '测试中': '🧪',
        '验证中': '🔍',
        '发布中': '🚀',
    }
    for key, emoji in status_map.items():
        if key in status:
            return emoji
    return '📍'


def get_custom_field_value(item: Dict, field_id: str) -> str:
    """获取自定义字段值"""
    custom_fields = item.get('customFieldValues', [])
    for field in custom_fields:
        if field.get('fieldId') == field_id:
            values = field.get('values', [])
            if values:
                return values[0].get('displayValue', '')
    return ''


def gmt_create_str(ts) -> str:
    """将毫秒时间戳转为可读日期"""
    try:
        dt = datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def is_online_fault(item: dict) -> bool:
    """判断是否为线上故障"""
    wtype = item.get("workitemType") or {}
    name = wtype.get("name", "") or ""
    type_id = wtype.get("id", "") or ""
    return "线上故障" in name or type_id == "bba77181ef64f834248a0175"


CLOSED_STATUS_IDS = {"100085"}


def analyze_stats(json_file_path: str, days_label: str) -> dict:
    """分析统计数据 - 支持两种模式"""
    _, start_ts, end_ts = parse_days(days_label)

    with open(json_file_path, "r") as f:
        data = json.load(f)

    # 检测是否为分页优先模式
    has_counts = isinstance(data, dict) and "_counts" in data
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []

    # 过滤出线上故障
    valid_items = [item for item in items if is_online_fault(item)]

    if has_counts:
        # 分页优先模式：使用 _counts 作为统计结果，_items 用于清单展示
        counts = data["_counts"]
        unresolved_items = data.get("_items", [])

        return {
            'total_online_fault': counts.get('total', 0),
            'unresolved': counts.get('unresolved', len(unresolved_items)),
            'unresolved_items': unresolved_items,
            'created': counts.get('created', 0),
            'closed': counts.get('closed', 0),
            'days_label': days_label
        }
    else:
        # 传统模式：遍历 all items 本地统计
        total_online_fault = 0
        unresolved_items = []
        created_count = 0
        closed_count = 0

        for item in valid_items:
            total_online_fault += 1

            gmt_create = item.get('gmtCreate', 0)
            if start_ts <= gmt_create <= end_ts:
                created_count += 1

            status_id = str(item.get('status', {}).get('id', ''))
            update_status_at = item.get('updateStatusAt', 0)

            if status_id in CLOSED_STATUS_IDS and start_ts <= update_status_at <= end_ts:
                closed_count += 1

            if status_id not in CLOSED_STATUS_IDS:
                unresolved_items.append(item)

        return {
            'total_online_fault': total_online_fault,
            'unresolved': len(unresolved_items),
            'unresolved_items': unresolved_items,
            'created': created_count,
            'closed': closed_count,
            'days_label': days_label
        }


def print_result(stats: Dict, organization_id: str = ""):
    """打印结果 - 按负责人分组，带 Emoji"""
    label = stats['days_label']
    unresolved_count = stats['unresolved']
    print(f"""## 线上故障统计

| 统计项 | 数量 |
|--------|------|
| **当前所有未解决线上故障** | **{unresolved_count}** |
| **`{label}`创建的线上故障** | **{stats['created']}** |
| **`{label}`关闭的线上故障** | **{stats['closed']}** |""")

    unresolved_items = stats.get('unresolved_items', [])
    if unresolved_count > 0 and not unresolved_items:
        print(f"\n⚠️  统计显示有 {unresolved_count} 个未解决故障，但未获取到明细清单数据")
        return
    if unresolved_count == 0:
        print("\n✅ 当前没有未解决的线上故障！")
        return

    # 按负责人分组
    items_by_assignee = defaultdict(list)
    unassigned_items = []

    for item in unresolved_items:
        assigned_to = item.get('assignedTo') or {}
        assignee = assigned_to.get('name', '未分配')
        if assignee:
            items_by_assignee[assignee].append(item)
        else:
            unassigned_items.append(item)

    print("\n## 未解决故障清单（按负责人分组）\n")

    # 按故障数量排序负责人
    sorted_assignees = sorted(items_by_assignee.keys(), key=lambda x: len(items_by_assignee[x]), reverse=True)

    for assignee in sorted_assignees:
        items = items_by_assignee[assignee]
        print(f"### 👤 {assignee}（{len(items)} 个故障）\n")
        print("| 优先级 | 严重程度 | 状态 | 编号 | 标题 | 创建时间 | 链接 |")
        print("|--------|----------|------|------|------|---------|------|")

        for item in items:
            identifier = item.get("serialNumber", "")
            subject = item.get("subject", "")
            status = item.get("status") or {}
            status_name = status.get("name", "")

            priority = get_custom_field_value(item, 'priority')
            severity = get_custom_field_value(item, 'seriousLevel')
            create_time = gmt_create_str(item.get('gmtCreate', 0))

            priority_emoji = get_priority_emoji(priority)
            severity_emoji = get_severity_emoji(severity)
            status_emoji = get_status_emoji(status_name)

            if organization_id and identifier:
                link = f"[查看](https://devops.aliyun.com/organization/{organization_id}/work/workitems/{identifier})"
            else:
                link = identifier

            print(f"| {priority_emoji} {priority} | {severity_emoji} {severity} | {status_emoji} {status_name} | {identifier} | {subject} | {create_time} | {link} |")
        print()

    # 未分配的故障
    if unassigned_items:
        print(f"### ❌ 未分配（{len(unassigned_items)} 个故障）\n")
        print("| 优先级 | 严重程度 | 状态 | 编号 | 标题 | 创建时间 | 链接 |")
        print("|--------|----------|------|------|------|---------|------|")
        for item in unassigned_items:
            identifier = item.get("serialNumber", "")
            subject = item.get("subject", "")
            status = item.get("status") or {}
            status_name = status.get("name", "")

            priority = get_custom_field_value(item, 'priority')
            severity = get_custom_field_value(item, 'seriousLevel')
            create_time = gmt_create_str(item.get('gmtCreate', 0))

            priority_emoji = get_priority_emoji(priority)
            severity_emoji = get_severity_emoji(severity)
            status_emoji = get_status_emoji(status_name)

            if organization_id and identifier:
                link = f"[查看](https://devops.aliyun.com/organization/{organization_id}/work/workitems/{identifier})"
            else:
                link = identifier

            print(f"| {priority_emoji} {priority} | {severity_emoji} {severity} | {status_emoji} {status_name} | {identifier} | {subject} | {create_time} | {link} |")
        print()

    # 摘要统计
    print("## 状态统计摘要\n")
    status_counts = defaultdict(int)
    for item in unresolved_items:
        status = item.get("status") or {}
        status_name = status.get("name", "未知")
        status_counts[status_name] += 1

    print("| 状态 | 数量 |")
    print("|------|------|")
    for status_name, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        status_emoji = get_status_emoji(status_name)
        print(f"| {status_emoji} {status_name} | {count} |")
    print()

    print("## 优先级统计摘要\n")
    priority_counts = defaultdict(int)
    for item in unresolved_items:
        priority = get_custom_field_value(item, 'priority') or "未知"
        priority_counts[priority] += 1

    print("| 优先级 | 数量 |")
    print("|--------|------|")
    for priority, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True):
        priority_emoji = get_priority_emoji(priority)
        print(f"| {priority_emoji} {priority} | {count} |")
    print()


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


if __name__ == '__main__':
    main()
