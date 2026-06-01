#!/usr/bin/env python3
"""
init_book.py — EPUB 初始化：解压 + 诊断结构 + 生成单元计划

用法：
    python init_book.py <epub_path>

输出：
    state/{sha}-diagnosis.json  — 结构诊断（single / library）
    state/{sha}-progress.json   — 阅读进度
    state/{sha}-unit-plan.json  — 阅读单元计划（由 unit_slicer 生成）
    state/{sha}-bookmark.json   — 会话书签
    state/{sha}_extracted/      — 解压后的 EPUB
    state/chapters/             — 章节文本文件
"""

import sys
import os
import hashlib
import zipfile
import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path
from datetime import datetime
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


# ── 工具函数 ──

def calculate_sha256(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def extract_epub(epub_path, extract_dir):
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return extract_dir


# ── OPF 解析 ──

def parse_metadata(extract_dir):
    """解析 OPF 元数据"""
    opf_path = None
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.endswith('.opf'):
                opf_path = os.path.join(root, f)
                break

    if not opf_path:
        raise FileNotFoundError("OPF file not found in EPUB")

    tree = ET.parse(opf_path)
    root = tree.getroot()

    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    def get_text(tag):
        el = root.find(f'.//{tag}', ns)
        return el.text.strip() if el is not None and el.text else None

    def get_all(tag):
        return [el.text.strip() for el in root.findall(f'.//{tag}', ns) if el.text]

    spine_count = 0
    spine_el = root.find('.//opf:spine', ns)
    if spine_el is not None:
        spine_count = len(spine_el.findall('opf:itemref', ns))

    return {
        'title': get_text('dc:title') or 'Unknown',
        'author': get_text('dc:creator') or 'Unknown',
        'authors': get_all('dc:creator'),
        'dc_type': get_text('dc:type'),
        'dc_subjects': get_all('dc:subject'),
        'dc_description': get_text('dc:description'),
        'spine_count': spine_count,
        'opf_path': opf_path,
    }


def parse_spine(opf_path):
    tree = ET.parse(opf_path)
    root = tree.getroot()
    ns = {'opf': 'http://www.idpf.org/2007/opf'}

    manifest = root.find('.//opf:manifest', ns)
    manifest_items = {}
    for item in manifest.findall('opf:item', ns):
        manifest_items[item.get('id')] = {
            'href': item.get('href'),
            'media-type': item.get('media-type'),
        }

    spine = root.find('.//opf:spine', ns)
    spine_items = []
    for itemref in spine.findall('opf:itemref', ns):
        idref = itemref.get('idref')
        if idref in manifest_items:
            spine_items.append({
                'id': idref,
                'href': manifest_items[idref]['href'],
                'media_type': manifest_items[idref]['media-type'],
            })

    return spine_items


# ── TOC 解析 ──

def parse_toc_ncx(extract_dir):
    ncx_path = None
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.endswith('.ncx') or f == 'nav.xhtml':
                ncx_path = os.path.join(root, f)
                break

    if not ncx_path or not os.path.exists(ncx_path):
        return None

    try:
        tree = ET.parse(ncx_path)
        root = tree.getroot()
        ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}

        toc_entries = []

        def parse_navpoint(navpoint, level=0):
            label = navpoint.find('ncx:navLabel/ncx:text', ns)
            content = navpoint.find('ncx:content', ns)
            if label is not None and content is not None:
                toc_entries.append({
                    'level': level,
                    'title': label.text,
                    'src': content.get('src'),
                })
            for child in navpoint.findall('ncx:navPoint', ns):
                parse_navpoint(child, level + 1)

        nav_map = root.find('ncx:navMap', ns)
        if nav_map is not None:
            for navpoint in nav_map.findall('ncx:navPoint', ns):
                parse_navpoint(navpoint)

        return toc_entries

    except Exception as e:
        print(f"Warning: Failed to parse TOC: {e}", file=sys.stderr)
        return None


# ── 结构诊断（只分 single / library）──

def diagnose_structure(toc_entries, metadata):
    """判断是单书还是多书合集

    依据：TOC L0 条目是否看起来像独立著作
    """
    if not toc_entries:
        return 'single', []

    # 过滤掉非内容条目
    skip_kw = ['目录', '目 录', '赠言', '梗概', '附录', '前言', '序言', '序',
               '致谢', '版权', '封面', '封底', 'toc', 'table of contents',
               'preface', 'foreword', 'acknowledgments', 'appendix']

    l0_entries = [e for e in toc_entries if e.get('level', 0) == 0]
    content_entries = [
        e for e in l0_entries
        if not any(kw in e['title'].lower() for kw in skip_kw)
    ]

    if len(content_entries) <= 1:
        return 'single', []

    l0_names = [e['title'] for e in content_entries]

    # 检查是否为连续叙事（单书多部）
    narrative_kw = ['部', '章', '卷', '回', '节', 'part', 'chapter', 'volume']
    sequential = sum(
        1 for name in l0_names
        if any(kw in name.lower() for kw in narrative_kw)
    )

    # 如果大部分标题含叙事关键词，且总数 ≤ 5，视为单书
    if len(content_entries) <= 5 and sequential >= len(content_entries) * 0.6:
        return 'single', []

    # 否则视为多书合集
    books = []
    for i, entry in enumerate(content_entries):
        books.append({
            'index': i + 1,
            'title': entry['title'],
        })

    return 'library', books


# ── 主流程 ──

def main():
    if len(sys.argv) < 2:
        print("用法: python init_book.py <epub_path>")
        sys.exit(1)

    epub_path = sys.argv[1]
    if not os.path.exists(epub_path):
        print(f"错误: 文件不存在: {epub_path}")
        sys.exit(1)

    skill_dir = Path(__file__).parent.parent
    state_dir = skill_dir / 'state'
    chapters_dir = state_dir / 'chapters'

    print(f"正在初始化: {epub_path}")

    # 1. SHA256
    print("计算 SHA256...")
    sha = calculate_sha256(epub_path)
    print(f"SHA256: {sha}")

    # 检查缓存
    diagnosis_path = state_dir / f'{sha}-diagnosis.json'
    if diagnosis_path.exists():
        cached = json.load(open(diagnosis_path, encoding='utf-8'))
        print(f"发现缓存诊断: {cached['structure']}")
        print(f"跳过初始化，直接使用缓存")
        # 输出 JSON
        result = {'status': 'cached', 'sha': sha, **cached}
        print(f"\n{json.dumps(result, ensure_ascii=False)}")
        return

    # 2. 解压
    print("解压 EPUB...")
    extract_dir = state_dir / f'{sha}_extracted'
    extract_epub(epub_path, extract_dir)
    print(f"解压完成")

    # 3. 元数据
    print("解析元数据...")
    metadata = parse_metadata(extract_dir)
    print(f"书名: {metadata['title']}")
    print(f"作者: {metadata['author']}")

    # 4. TOC
    print("解析目录结构...")
    toc_entries = parse_toc_ncx(extract_dir)
    spine_items = parse_spine(metadata['opf_path'])

    l0_count = len([e for e in toc_entries if e.get('level', 0) == 0]) if toc_entries else 0
    print(f"TOC 条目: {l0_count} 个一级条目")

    # 5. 结构诊断
    structure, books = diagnose_structure(toc_entries, metadata)
    print(f"结构: {structure}")

    # 6. 创建目录
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(chapters_dir, exist_ok=True)
    output_dir = skill_dir / 'output' / sha
    os.makedirs(output_dir, exist_ok=True)

    # 7. 写入 diagnosis.json
    diagnosis = {
        'sha': sha,
        'title': metadata['title'],
        'author': metadata['author'],
        'structure': structure,
        'books': books,
        'diagnosed_at': datetime.now().isoformat(),
    }
    with open(diagnosis_path, 'w', encoding='utf-8') as f:
        json.dump(diagnosis, f, ensure_ascii=False, indent=2)
    print(f"诊断文件: {diagnosis_path}")

    # 8. 写入 progress.json
    progress_path = state_dir / f'{sha}-progress.json'
    progress = {
        'sha': sha,
        'title': metadata['title'],
        'author': metadata['author'],
        'structure': structure,
        'current_unit': 0,
        'completed_units': [],
        'library': books if structure == 'library' else None,
        'created_at': datetime.now().isoformat(),
    }
    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    # 9. 写入 bookmark
    bookmark_path = state_dir / f'{sha}-bookmark.json'
    bookmark = {
        'sha': sha,
        'title': metadata['title'],
        'author': metadata['author'],
        'progress_path': str(progress_path),
        'last_active': datetime.now().isoformat(),
    }
    with open(bookmark_path, 'w', encoding='utf-8') as f:
        json.dump(bookmark, f, ensure_ascii=False, indent=2)

    # 10. 调用 unit_slicer 生成单元计划
    print("生成阅读单元...")
    slicer_path = Path(__file__).parent / 'unit_slicer.py'
    os.system(f'python "{slicer_path}" "{state_dir}" "{sha}"')

    # 完成
    print("\n" + "=" * 50)
    print("[OK] 初始化完成!")
    print(f"书名: {metadata['title']}")
    print(f"作者: {metadata['author']}")
    print(f"结构: {structure}")
    print(f"SHA256: {sha}")
    print("=" * 50)

    # 输出 JSON
    result = {
        'status': 'ok',
        'sha': sha,
        'title': metadata['title'],
        'author': metadata['author'],
        'structure': structure,
        'books': books,
    }
    print(f"\n{json.dumps(result, ensure_ascii=False)}")


if __name__ == '__main__':
    main()
