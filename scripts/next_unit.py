#!/usr/bin/env python3
"""
next_unit.py — 获取当前阅读单元信息（不自动更新进度）

用法：
    python next_unit.py <state_dir> <sha> <book_index> [--advance]

参数：
    --advance  在返回结果后自动将进度推进到下一单元

输出 JSON：
{
    "unit_id": 469,
    "title": "...",
    "file": "Text/part0466.xhtml",
    "anchor": "c012",
    "word_count": 14107,
    "chapter_path": "state/sha_extracted/OEBPS/Text/part0466.xhtml",
    "current_unit": 469,
    "total_units": 1680
}
"""

import sys
import os
import json
from pathlib import Path


def main():
    if len(sys.argv) < 4:
        print("用法: python next_unit.py <state_dir> <sha> <book_index> [--advance]")
        sys.exit(1)

    state_dir = Path(sys.argv[1])
    sha = sys.argv[2]
    book_index = int(sys.argv[3])
    advance = '--advance' in sys.argv

    # 1. 读取当前进度
    progress_path = state_dir / f'{sha}-progress.json'
    if not progress_path.exists():
        print(json.dumps({"error": "progress.json not found"}))
        sys.exit(1)

    with open(progress_path, 'r', encoding='utf-8') as f:
        progress = json.load(f)

    current_unit = progress.get('current_unit', 0)

    # 2. 读取单元计划
    plan_path = state_dir / f'{sha}_book{book_index}-unit-plan.json'
    if not plan_path.exists():
        print(json.dumps({"error": f"book{book_index}-unit-plan.json not found"}))
        sys.exit(1)

    with open(plan_path, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    total_units = plan.get('total_units', 0)

    # 3. 查找当前单元
    target_unit = None
    for unit in plan.get('units', []):
        if unit['id'] == current_unit:
            target_unit = unit
            break

    if not target_unit:
        print(json.dumps({
            "error": f"Unit {current_unit} not found",
            "current_unit": current_unit,
            "total_units": total_units
        }))
        sys.exit(1)

    # 4. 构建章节文件路径
    extract_dir = state_dir / f'{sha}_extracted' / 'OEBPS'
    chapter_path = extract_dir / target_unit['file']

    # 5. 如果指定了 --advance，更新进度到下一单元
    if advance:
        next_unit_id = current_unit + 1
        progress['current_unit'] = next_unit_id
        if current_unit not in progress.get('completed_units', []):
            progress.setdefault('completed_units', []).append(current_unit)

        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    # 6. 输出结果
    result = {
        "unit_id": current_unit,
        "title": target_unit['title'],
        "file": target_unit['file'],
        "anchor": target_unit.get('anchor'),
        "word_count": target_unit.get('word_count', 0),
        "chapter_path": str(chapter_path),
        "current_unit": current_unit,
        "total_units": total_units,
        "book_index": book_index
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
