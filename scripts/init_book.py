#!/usr/bin/env python3
"""
Narrativist Skill - 跨平台书籍初始化脚本

用法：
    python init_book.py <epub_path>

功能：
1. 计算 EPUB SHA256
2. 解压 EPUB
3. 解析元数据
4. 提取章节文本
5. 模式诊断
6. 生成 progress.json
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
    """HTML 文本提取器，保留段落结构"""

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


def calculate_sha256(file_path):
    """计算文件 SHA256 前 16 位"""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def extract_epub(epub_path, extract_dir):
    """解压 EPUB 文件"""
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return extract_dir


def parse_metadata(extract_dir):
    """解析 OPF 元数据"""
    opf_path = None

    # 查找 OPF 文件
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.endswith('.opf'):
                opf_path = os.path.join(root, f)
                break

    if not opf_path:
        raise FileNotFoundError("OPF file not found in EPUB")

    # 解析 OPF
    tree = ET.parse(opf_path)
    root = tree.getroot()

    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # 获取元数据
    title = root.find('.//dc:title', ns)
    author = root.find('.//dc:creator', ns)

    return {
        'title': title.text if title is not None else 'Unknown',
        'author': author.text if author is not None else 'Unknown',
        'opf_path': opf_path
    }


def parse_spine(opf_path):
    """解析 spine 结构"""
    tree = ET.parse(opf_path)
    root = tree.getroot()

    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
    }

    # 获取 manifest
    manifest = root.find('.//opf:manifest', ns)
    manifest_items = {}
    for item in manifest.findall('opf:item', ns):
        item_id = item.get('id')
        href = item.get('href')
        media_type = item.get('media-type')
        manifest_items[item_id] = {'href': href, 'media-type': media_type}

    # 获取 spine
    spine = root.find('.//opf:spine', ns)
    spine_items = []
    for itemref in spine.findall('opf:itemref', ns):
        idref = itemref.get('idref')
        if idref in manifest_items:
            spine_items.append({
                'id': idref,
                'href': manifest_items[idref]['href'],
                'media_type': manifest_items[idref]['media-type']
            })

    return spine_items


def parse_toc_ncx(extract_dir):
    """解析 toc.ncx 目录结构"""
    ncx_path = os.path.join(extract_dir, 'toc.ncx')

    if not os.path.exists(ncx_path):
        # 尝试查找其他可能的目录文件
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.endswith('.ncx') or f == 'nav.xhtml':
                    ncx_path = os.path.join(root, f)
                    break

    if not os.path.exists(ncx_path):
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
                title = label.text
                src = content.get('src')
                toc_entries.append({
                    'level': level,
                    'title': title,
                    'src': src
                })

            # 递归处理子项
            for child in navpoint.findall('ncx:navPoint', ns):
                parse_navpoint(child, level + 1)

        # 解析 navMap
        nav_map = root.find('ncx:navMap', ns)
        if nav_map is not None:
            for navpoint in nav_map.findall('ncx:navPoint', ns):
                parse_navpoint(navpoint)

        return toc_entries

    except Exception as e:
        print(f"Warning: Failed to parse TOC: {e}", file=sys.stderr)
        return None


def detect_book_structure(toc_entries, spine_items):
    """根据目录结构检测书籍类型和章节组织"""
    if not toc_entries:
        # 没有目录信息，使用 spine 顺序
        return {
            'type': 'sequential',
            'chapters': [{'name': f'Chapter {i+1}', 'files': [item['href']]} for i, item in enumerate(spine_items)]
        }

    # 分析目录结构
    parts = []
    current_part = None

    for entry in toc_entries:
        title = entry['title']
        src = entry['src']

        # 检测是否为"部"或"Part"
        is_part = any(keyword in title for keyword in ['第', '部', 'Part', 'part', '卷', 'Volume'])

        if is_part:
            if current_part:
                parts.append(current_part)
            current_part = {
                'name': title,
                'files': [src.split('#')[0]]  # 移除锚点
            }
        elif current_part:
            # 当前条目属于上一个"部"
            file_name = src.split('#')[0]
            if file_name not in current_part['files']:
                current_part['files'].append(file_name)

    # 添加最后一个部
    if current_part:
        parts.append(current_part)

    if parts:
        # 为每个部收集所有相关的 split 文件
        for part in parts:
            base_files = part['files'].copy()
            all_files = []

            for base_file in base_files:
                # 获取文件名前缀（如 part0003）
                file_prefix = base_file.split('_')[0] if '_' in base_file else base_file.replace('.html', '')

                # 在 spine 中查找所有匹配的文件
                for spine_item in spine_items:
                    spine_href = spine_item['href']
                    if spine_href.startswith(file_prefix):
                        if spine_href not in all_files:
                            all_files.append(spine_href)

            part['files'] = all_files if all_files else base_files

        return {
            'type': 'structured',
            'chapters': parts
        }
    else:
        # 没有检测到"部"结构，使用目录条目作为章节
        return {
            'type': 'toc_based',
            'chapters': [{'name': entry['title'], 'files': [entry['src'].split('#')[0]]} for entry in toc_entries]
        }


def extract_chapters(extract_dir, spine_items, chapters_dir, book_structure=None):
    """提取章节纯文本"""
    os.makedirs(chapters_dir, exist_ok=True)

    # 如果有书籍结构信息，按结构提取
    if book_structure and book_structure['type'] == 'structured':
        chapters = []
        for i, part in enumerate(book_structure['chapters']):
            all_text = []
            for file_name in part['files']:
                file_path = os.path.join(extract_dir, file_name)
                if not os.path.exists(file_path):
                    # 尝试查找文件
                    for root_dir, dirs, files in os.walk(extract_dir):
                        for f in files:
                            if f == file_name or file_name.endswith(f):
                                file_path = os.path.join(root_dir, f)
                                break

                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        parser = HTMLTextExtractor()
                        parser.feed(content)
                        text = parser.get_text()

                        # 清理文本
                        text = re.sub(r'\n\s*\n', '\n\n', text)
                        text = text.strip()

                        if len(text) > 100:
                            all_text.append(text)
                    except Exception as e:
                        print(f"Warning: Failed to process {file_name}: {e}", file=sys.stderr)

            # 合并该部分的所有文本
            if all_text:
                combined_text = '\n\n'.join(all_text)
                chapter_file = os.path.join(chapters_dir, f'part{i+1}.txt')
                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(combined_text)

                chapters.append({
                    'index': i + 1,
                    'name': part['name'],
                    'file': f'part{i+1}.txt',
                    'length': len(combined_text)
                })

        return chapters

    else:
        # 没有结构信息，按顺序提取
        chapters = []
        chapter_count = 0

        for item in spine_items:
            if item['media_type'] == 'application/xhtml+xml':
                href = item['href']
                file_path = os.path.join(extract_dir, href)

                # 如果文件不存在，尝试查找
                if not os.path.exists(file_path):
                    for root_dir, dirs, files in os.walk(extract_dir):
                        for f in files:
                            if f == href or href.endswith(f):
                                file_path = os.path.join(root_dir, f)
                                break

                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        parser = HTMLTextExtractor()
                        parser.feed(content)
                        text = parser.get_text()

                        # 清理文本
                        text = re.sub(r'\n\s*\n', '\n\n', text)
                        text = text.strip()

                        # 只保存有实质内容的章节
                        if len(text) > 100:
                            chapter_count += 1
                            chapter_file = os.path.join(chapters_dir, f'ch{chapter_count:02d}.txt')
                            with open(chapter_file, 'w', encoding='utf-8') as f:
                                f.write(text)

                            chapters.append({
                                'index': chapter_count,
                                'name': f'Chapter {chapter_count}',
                                'file': f'ch{chapter_count:02d}.txt',
                                'length': len(text)
                            })
                    except Exception as e:
                        print(f"Warning: Failed to process {href}: {e}", file=sys.stderr)

        return chapters


def diagnose_mode(chapters):
    """三阶段智能诊断"""
    # 阶段 A：TOC 层级信号
    if len(chapters) > 20:
        mode = 'grouped_epic'
    elif len(chapters) <= 5:
        mode = 'standard_chapter'
    else:
        mode = 'standard_chapter'

    # 阶段 B & C：内容分析（简化版）
    # 实际实现需要更复杂的人物重叠度分析
    # 这里暂时使用章节数作为主要判断依据

    return mode


def generate_progress(book_sha, title, author, mode, chapters, output_path):
    """生成 progress.json"""
    progress = {
        'book_sha': book_sha,
        'title': title,
        'author': author,
        'mode': mode,
        'total_chapters': len(chapters),
        'current_chapter': 0,
        'chapters': [
            {
                'index': ch['index'],
                'name': ch['name'],
                'file': ch['file'],
                'length': ch['length'],
                'status': 'pending'
            }
            for ch in chapters
        ],
        'created_at': datetime.now().isoformat(),
        'reader_signals': {},
        'reading_schedule': {}
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    return progress


def main():
    if len(sys.argv) < 2:
        print("用法: python init_book.py <epub_path>")
        sys.exit(1)

    epub_path = sys.argv[1]

    # 验证文件存在
    if not os.path.exists(epub_path):
        print(f"错误: 文件不存在: {epub_path}")
        sys.exit(1)

    # 设置路径
    skill_dir = Path(__file__).parent.parent
    state_dir = skill_dir / 'state'
    chapters_dir = state_dir / 'chapters'

    print(f"正在初始化: {epub_path}")

    # Step 0: 计算 SHA256
    print("计算 SHA256...")
    book_sha = calculate_sha256(epub_path)
    print(f"SHA256: {book_sha}")

    # 检查是否已存在
    progress_path = state_dir / f'{book_sha}-progress.json'
    bookmark_path = state_dir / f'{book_sha}-bookmark.json'

    if bookmark_path.exists():
        print(f"发现已有书签: {bookmark_path}")
        print("是否继续初始化？这将覆盖现有进度。(y/N)")
        response = input().strip().lower()
        if response != 'y':
            print("已取消初始化")
            sys.exit(0)

    # Step 1: 创建目录
    print("创建目录...")
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(chapters_dir, exist_ok=True)

    # Step 2: 解压 EPUB
    print("解压 EPUB...")
    extract_dir = state_dir / f'{book_sha}_extracted'
    extract_epub(epub_path, extract_dir)
    print(f"解压完成: {extract_dir}")

    # Step 3: 解析元数据
    print("解析元数据...")
    metadata = parse_metadata(extract_dir)
    print(f"书名: {metadata['title']}")
    print(f"作者: {metadata['author']}")

    # Step 4: 解析目录结构
    print("解析目录结构...")
    toc_entries = parse_toc_ncx(extract_dir)
    spine_items = parse_spine(metadata['opf_path'])

    if toc_entries:
        print(f"目录条目: {len(toc_entries)}")
        book_structure = detect_book_structure(toc_entries, spine_items)
        print(f"结构类型: {book_structure['type']}")
    else:
        print("未找到目录文件，按顺序提取")
        book_structure = None

    # Step 5: 提取章节
    print("提取章节...")
    chapters = extract_chapters(extract_dir, spine_items, chapters_dir, book_structure)
    print(f"提取完成: {len(chapters)} 章/部")

    # Step 6: 模式诊断
    print("模式诊断...")
    mode = diagnose_mode(chapters)
    print(f"模式: {mode}")

    # Step 7: 生成 progress.json
    print("生成进度文件...")
    progress = generate_progress(
        book_sha,
        metadata['title'],
        metadata['author'],
        mode,
        chapters,
        progress_path
    )
    print(f"进度文件: {progress_path}")

    # Step 7: 创建 output 目录
    output_dir = skill_dir / 'output' / book_sha
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")

    # 完成
    print("\n" + "=" * 50)
    print("[OK] 初始化完成!")
    print(f"书名: {metadata['title']}")
    print(f"作者: {metadata['author']}")
    print(f"章节数: {len(chapters)}")
    print(f"模式: {mode}")
    print(f"SHA256: {book_sha}")
    print("=" * 50)
    print(f"\n已加载《{metadata['title']}》，共 {len(chapters)} 章/部。准备好了就开始第一章？")


if __name__ == '__main__':
    main()
