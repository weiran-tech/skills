#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
统计云效项目中 线上故障 类型工作项
统计三个指标：
1. 当前所有未解决线上故障数量
2. 日期范围内创建的线上故障总数量
3. 日期范围内关闭的线上故障总数量

支持自然语言解析日期范围：
- `"昨天"` → 仅昨天
- `"今天"` → 今天到结束
- `"最近7天"` → 过去7天到今天
- `"2026-05-01 - 2026-05-11"` → 显式范围
- `""` 或 `"本月至今"` → 当月1日到今天

固定配置：
- 已关闭 statusId: 100085
"""

import json
import sys
import re
import datetime
from typing import Dict, List, Tuple
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


def load_workitems(json_file_path: str) -> List[Dict]:
    """加载工作项数据，支持多种格式"""
    with open(json_file_path, 'r') as f:
        content = f.read()

    data = json.loads(content)

    # 格式 1: 嵌套在 [{"text": "..."}] 中（旧 MCP 格式）
    if isinstance(data, list) and len(data) > 0 and 'text' in data[0]:
        actual_json_str = data[0]['text']
        result = json.loads(actual_json_str)
        return result.get('items', [])

    # 格式 2: 直接包含 items 字段
    if isinstance(data, dict) and 'items' in data:
        return data.get('items', [])

    # 格式 3: 直接是 items 列表
    if isinstance(data, list):
        return data

    return []


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


def analyze_stats(json_file_path: str, days_label: str) -> Dict:
    """分析统计数据"""
    items = load_workitems(json_file_path)

    # 固定配置
    online_fault_type_id = 'bba77181ef64f834248a0175'  # 线上故障
    closed_status_ids = {'100085'}  # 已关闭

    _, start_ts, end_ts = parse_days(days_label)

    total_online_fault = 0
    unresolved_items = []
    current_month_created = 0
    current_month_closed = 0

    for item in items:
        workitem_type_id = item.get('workitemType', {}).get('id')
        if workitem_type_id != online_fault_type_id:
            continue

        total_online_fault += 1

        # Check if created in current month
        gmt_create = item.get('gmtCreate', 0)
        if start_ts <= gmt_create <= end_ts:
            current_month_created += 1

        status_id = str(item.get('status', {}).get('id', ''))
        update_status_at = item.get('updateStatusAt', 0)

        # Check if closed in current month
        if status_id in closed_status_ids and start_ts <= update_status_at <= end_ts:
            current_month_closed += 1

        # Check if unresolved
        if status_id not in closed_status_ids:
            unresolved_items.append(item)

    return {
        'total_online_fault': total_online_fault,
        'unresolved': len(unresolved_items),
        'unresolved_items': unresolved_items,
        'created': current_month_created,
        'closed': current_month_closed,
        'days_label': days_label
    }


def print_result(stats: Dict, organization_id: str = ""):
    """打印结果 - 按负责人分组，带 Emoji"""
    label = stats['days_label']
    print(f"""
# 线上故障统计结果

| 统计项 | 数量 |
|--------|------|
| **当前所有未解决线上故障** | **{stats['unresolved']}** |
| **`{label}`创建的线上故障** | **{stats['created']}** |
| **`{label}`关闭的线上故障** | **{stats['closed']}** |

**统计说明:**
- 项目中总共有 **{stats['total_online_fault']}** 个"线上故障"类型工作项
- **{stats['total_online_fault'] - stats['unresolved']}** 个已经关闭，**{stats['unresolved']}** 个仍处于未解决状态
""")

    unresolved_items = stats.get('unresolved_items', [])
    if not unresolved_items:
        print("✅ 当前没有未解决的线上故障！")
        return

    def gmt_create_str(ts) -> str:
        """将毫秒时间戳转为可读日期"""
        try:
            dt = datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return "-"

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

    print("## 未解决故障清单（按负责人分组）\n")

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
                link = f"https://devops.aliyun.com/organization/{organization_id}/work/workitems/{identifier}"
            else:
                link = identifier

            print(f"| {priority_emoji} {priority} | {severity_emoji} {severity} | {status_emoji} {status_name} | {identifier} | {subject} | {create_time} | [查看]({link}) |")
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
                link = f"https://devops.aliyun.com/organization/{organization_id}/work/workitems/{identifier}"
            else:
                link = identifier

            print(f"| {priority_emoji} {priority} | {severity_emoji} {severity} | {status_emoji} {status_name} | {identifier} | {subject} | {create_time} | [查看]({link}) |")
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


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <json-file-path> \"<days>\" [organization_id]")
        print("  days examples: \"昨天\", \"最近7天\", \"2026-05-01 - 2026-05-11\", \"\"")
        sys.exit(1)

    json_file = sys.argv[1]
    days_label = sys.argv[2]
    organization_id = sys.argv[3] if len(sys.argv) > 3 else ''

    stats = analyze_stats(json_file, days_label)
    print_result(stats, organization_id)


if __name__ == '__main__':
    main()
