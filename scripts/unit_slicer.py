#!/usr/bin/env python3
"""
unit_slicer.py — TOC 叶子节点 → 阅读单元计划

用法：
    python unit_slicer.py <state_dir> <sha>

输入：
    state/{sha}_extracted/   — 解压后的 EPUB
    state/{sha}-diagnosis.json — 结构诊断（single / library）

输出：
    state/{sha}-unit-plan.json — 阅读单元计划

流程：
    1. 取 TOC 所有叶子节点（最深层条目）
    2. 过滤无效单元（扉页/版权/目录/致谢等）
    3. 合并碎片单元（连续 <300 字的合并，上限 5 个）
    4. 不动过大单元（>20000 字保持原样）
    5. 输出 unit_plan.json
"""

import sys
import os
import json
import re
from pathlib import Path
from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.skip = False
        if tag in ['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.result.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.result.append(data)

    def get_text(self):
        return ''.join(self.result)


# ── 无效单元关键词 ──

SKIP_KEYWORDS = [
    '扉页', '版权页', '版权', '目录', '目 录', '封面', '封底',
    '致谢', '谢辞', '注释', '注解', '参考文献', '附录',
    '赠言', '梗概', '前言', '序言', '序', '后记', '跋',
    '译名表', '理想国·imaginist', 'imaginist',
    'title page', 'copyright', 'table of contents',
    'acknowledgments', 'references', 'appendix',
    'preface', 'foreword', 'afterword', 'epilogue',
]


def is_skip_title(title):
    """标题是否匹配无效关键词"""
    t = title.strip().lower()
    return any(kw in t for kw in SKIP_KEYWORDS)


def get_toc_leaves(toc_entries):
    """取 TOC 所有叶子节点（没有子节点的条目）"""
    if not toc_entries:
        return []

    # 标记哪些条目是其他条目的父节点
    child_srcs = set()
    for entry in toc_entries:
        if entry.get('level', 0) > 0:
            # 这个条目的 src 的父级就是上一个 level 更小的条目
            pass

    # 叶子节点：没有其他条目以它为父（即 level 不比它小的下一个条目）
    leaves = []
    for i, entry in enumerate(toc_entries):
        # 检查下一个条目是否是它的子节点
        is_leaf = True
        if i + 1 < len(toc_entries):
            next_entry = toc_entries[i + 1]
            if next_entry.get('level', 0) > entry.get('level', 0):
                is_leaf = False

        if is_leaf:
            leaves.append(entry)

    return leaves


def find_files(extract_dir, href):
    """在解压目录中查找文件（处理 split 文件）

    如果 href 是 part0003_split_000.html，还会查找 part0003_split_001.html 等
    返回文件路径列表
    """
    basename = os.path.basename(href.split('#')[0])
    found = []

    # 检查是否是 split 文件
    split_match = re.match(r'(.+_split_)\d+(\.\w+)$', basename)
    if split_match:
        prefix = split_match.group(1)
        ext = split_match.group(2)
        for root, dirs, files in os.walk(extract_dir):
            for f in sorted(files):
                if f.startswith(prefix) and f.endswith(ext):
                    found.append(os.path.join(root, f))
    else:
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f == basename or basename.endswith(f):
                    found.append(os.path.join(root, f))
                    break

    return found


def extract_text(file_paths, anchor=None):
    """从 HTML 文件提取纯文本（支持多文件合并）"""
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    combined = ''
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            parser = HTMLTextExtractor()
            parser.feed(content)
            combined += parser.get_text() + '\n'
        except:
            pass

    # 如果有锚点，只取锚点之后的内容
    if anchor:
        marker = f'id="{anchor}"'
        idx = combined.find(marker)
        if idx == -1:
            marker = f"name=\"{anchor}\""
            idx = combined.find(marker)
        if idx != -1:
            combined = combined[idx:]

    text = re.sub(r'\n\s*\n', '\n\n', combined)
    return text.strip()


def count_chinese_chars(text):
    """统计字数（中文字符 + 英文单词）"""
    chinese = len(re.findall(r'[一-鿿]', text))
    english = len(re.findall(r'[a-zA-Z]+', text))
    return chinese + english


def slice_units(extract_dir, toc_entries, spine_items):
    """主流程：TOC → 阅读单元"""

    # 1. 取叶子节点
    leaves = get_toc_leaves(toc_entries)

    if not leaves:
        # TOC 为空或无法解析，回退：用 spine 文件作为单元
        units = []
        for i, item in enumerate(spine_items):
            if item['media_type'] != 'application/xhtml+xml':
                continue
            file_path = find_files(extract_dir, item['href'])
            if not file_path:
                continue
            text = extract_text(file_path)
            wc = count_chinese_chars(text)
            if wc < 50:
                continue
            units.append({
                'id': len(units) + 1,
                'title': f'段落 {len(units) + 1}',
                'word_count': wc,
                'file': os.path.basename(item['href'].split('#')[0]),
                'anchor': None,
            })
        return units

    # 2. 提取每个叶子节点的文本和字数
    raw_units = []
    for entry in leaves:
        title = entry['title']
        src = entry['src']
        href = src.split('#')[0]
        anchor = src.split('#')[1] if '#' in src else None

        # 过滤无效单元（标题匹配则跳过，不再检查字数）
        if is_skip_title(title):
            continue

        file_paths = find_files(extract_dir, href)
        if not file_paths:
            continue

        text = extract_text(file_paths, anchor)
        wc = count_chinese_chars(text)

        # 过滤太短的单元（但不包括已通过标题过滤的内容）
        if wc < 50:
            continue

        raw_units.append({
            'title': title,
            'word_count': wc,
            'file': href,
            'anchor': anchor,
            'text': text,  # 临时保留，后面删除
        })

    # 3. 合并碎片单元（连续 <300 字的合并，上限 5 个）
    merged = []
    buffer = []

    for unit in raw_units:
        if unit['word_count'] < 300:
            buffer.append(unit)
            if len(buffer) >= 5:
                # 达到合并上限，强制合并
                merged.append(_merge_buffer(buffer))
                buffer = []
        else:
            # 先合并缓冲区
            if buffer:
                merged.append(_merge_buffer(buffer))
                buffer = []
            merged.append(unit)

    # 处理尾部缓冲
    if buffer:
        merged.append(_merge_buffer(buffer))

    # 4. 编号并清理
    units = []
    for i, unit in enumerate(merged):
        units.append({
            'id': i + 1,
            'title': unit['title'],
            'word_count': unit['word_count'],
            'file': unit['file'],
            'anchor': unit.get('anchor'),
        })

    return units


def _merge_buffer(buffer):
    """合并一组碎片单元"""
    total_wc = sum(u['word_count'] for u in buffer)
    first_title = buffer[0]['title']
    last_title = buffer[-1]['title']

    if first_title == last_title:
        title = first_title
    else:
        title = f'{first_title} → {last_title}'

    return {
        'title': title,
        'word_count': total_wc,
        'file': buffer[0]['file'],
        'anchor': buffer[0].get('anchor'),
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python unit_slicer.py <state_dir> <sha>")
        sys.exit(1)

    state_dir = Path(sys.argv[1])
    sha = sys.argv[2]

    # 加载诊断结果
    diag_path = state_dir / f'{sha}-diagnosis.json'
    if not diag_path.exists():
        print("错误: 未找到 diagnosis.json，请先运行 init_book.py")
        sys.exit(1)

    diagnosis = json.load(open(diag_path, encoding='utf-8'))
    structure = diagnosis.get('structure', 'single')

    # 加载 TOC 和 spine
    from init_book import parse_toc_ncx, parse_spine, parse_metadata

    extract_dir = state_dir / f'{sha}_extracted'
    metadata = parse_metadata(extract_dir)
    toc_entries = parse_toc_ncx(extract_dir)
    spine_items = parse_spine(metadata['opf_path'])

    if structure == 'library':
        # Library 模式：为每本书生成独立的 unit_plan
        books = diagnosis.get('books', [])
        all_plans = {}
        for book in books:
            book_idx = book['index']
            book_toc = _filter_toc_for_book(toc_entries, book)
            units = slice_units(str(extract_dir), book_toc, spine_items)
            all_plans[f'book{book_idx}'] = {
                'book_index': book_idx,
                'book_title': book['title'],
                'total_units': len(units),
                'units': units,
            }

            # 写入每本书的 unit_plan
            plan_path = state_dir / f'{sha}_book{book_idx}-unit-plan.json'
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(all_plans[f'book{book_idx}'], f, ensure_ascii=False, indent=2)
            print(f'书 {book_idx}「{book["title"]}」: {len(units)} 个单元')

        # 写入主 unit_plan（library 级别）
        main_plan = {
            'structure': 'library',
            'books': list(all_plans.keys()),
        }
        plan_path = state_dir / f'{sha}-unit-plan.json'
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(main_plan, f, ensure_ascii=False, indent=2)

    else:
        # 单书模式
        units = slice_units(str(extract_dir), toc_entries, spine_items)
        plan = {
            'structure': 'single',
            'total_units': len(units),
            'units': units,
        }
        plan_path = state_dir / f'{sha}-unit-plan.json'
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f'单书: {len(units)} 个单元')

    print(f'单元计划: {plan_path}')


def _filter_toc_for_book(toc_entries, book):
    """从全局 TOC 中提取属于指定书的条目"""
    # 这里简化处理：返回所有条目，由 slice_units 自行过滤
    # 更精确的实现需要根据 book['files'] 匹配
    return toc_entries


if __name__ == '__main__':
    main()
