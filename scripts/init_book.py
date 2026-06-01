#!/usr/bin/env python3
"""
Narrativist Skill - 跨平台书籍初始化脚本

两阶段设计：
  阶段一：python init_book.py <epub_path>
    → 快速初始化（<1秒）：SHA256、解压、解析 TOC、生成 books 列表
    → 输出 {sha}-progress.json（含 books 元数据，无文本内容）

  阶段二：python init_book.py <epub_path> --extract <book_index>
    → 按需提取：只提取指定书的文本，保留章节边界
    → 输出 {sha}_book{N}-progress.json（该书的独立状态文件）
    → library 模式下不覆盖主 progress.json

  完成标记：python init_book.py <epub_path> --complete <book_index>
    → 标记该书为已完成，更新主 progress.json
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
    """解析 OPF 元数据，提取书名、作者、类型、主题"""
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

    # dc:type 可能包含 "fiction", "poetry", "drama", "nonfiction" 等
    dc_type = get_text('dc:type')
    # dc:subject 可能包含 "短篇小说集", "诗集", "散文" 等
    dc_subjects = get_all('dc:subject')
    # dc:description 可能包含体裁描述
    dc_description = get_text('dc:description')

    # spine 条目数（比 TOC 更真实的正文文件数）
    spine_count = 0
    spine_el = root.find('.//opf:spine', ns)
    if spine_el is not None:
        spine_count = len(spine_el.findall('opf:itemref', ns))

    return {
        'title': get_text('dc:title') or 'Unknown',
        'author': get_text('dc:creator') or 'Unknown',
        'authors': get_all('dc:creator'),
        'dc_type': dc_type,
        'dc_subjects': dc_subjects,
        'dc_description': dc_description,
        'spine_count': spine_count,
        'opf_path': opf_path
    }


def parse_spine(opf_path):
    """解析 spine 结构"""
    tree = ET.parse(opf_path)
    root = tree.getroot()

    ns = {'opf': 'http://www.idpf.org/2007/opf'}

    manifest = root.find('.//opf:manifest', ns)
    manifest_items = {}
    for item in manifest.findall('opf:item', ns):
        item_id = item.get('id')
        href = item.get('href')
        media_type = item.get('media-type')
        manifest_items[item_id] = {'href': href, 'media-type': media_type}

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
    """解析 toc.ncx 目录结构，返回带层级的条目列表"""
    ncx_path = os.path.join(extract_dir, 'toc.ncx')

    if not os.path.exists(ncx_path):
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
                toc_entries.append({
                    'level': level,
                    'title': label.text,
                    'src': content.get('src')
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


# ── 阶段一：快速初始化 ──────────────────────────────────────────

def quick_init(epub_path):
    """阶段一：快速初始化（<10秒）

    返回 dict：
      sha, title, author, extract_dir, books(list of {name, files, level})
    """
    sha = calculate_sha256(epub_path)

    # 解压
    skill_dir = Path(__file__).parent.parent
    state_dir = skill_dir / 'state'
    extract_dir = state_dir / f'{sha}_extracted'

    if not extract_dir.exists():
        extract_epub(epub_path, extract_dir)

    # 元数据
    metadata = parse_metadata(extract_dir)

    # TOC
    toc_entries = parse_toc_ncx(extract_dir)
    spine_items = parse_spine(metadata['opf_path'])

    # 构建书籍列表
    books = build_books_list(toc_entries, spine_items, extract_dir)

    return {
        'sha': sha,
        'title': metadata['title'],
        'author': metadata['author'],
        'authors': metadata['authors'],
        'metadata': metadata,  # 完整元数据（含 dc_type, dc_subjects 等）
        'extract_dir': str(extract_dir),
        'spine_items': spine_items,
        'books': books,
        'toc_entries': toc_entries
    }


def build_books_list(toc_entries, spine_items, extract_dir):
    """从 TOC 构建书籍列表（只解析结构，不提取文本）

    返回 list of dict：
      {name, type, files(list of spine hrefs), estimated_chars}
    """
    if not toc_entries:
        # 无 TOC，整本书作为一个条目
        return [{
            'name': 'Unknown',
            'type': 'single',
            'files': [s['href'] for s in spine_items if s['media_type'] == 'application/xhtml+xml'],
            'estimated_chars': 0
        }]

    has_children = any(e.get('level', 0) > 0 for e in toc_entries)

    # 跳过非内容页
    skip_keywords = ['扉页', '版权页', '目录', '封底', 'imaginist',
                     '附录', '译名表', '致谢', '注解与参考文献',
                     'title page', 'copyright', 'colophon']

    def is_skip(title):
        return any(kw in title for kw in skip_keywords)

    if has_children:
        # 多层 TOC：L0 = 书名，L1 = 章节
        books = []
        current_book = None

        for entry in toc_entries:
            level = entry.get('level', 0)
            title = entry['title']
            src = entry['src'].split('#')[0]

            if is_skip(title):
                continue

            if level == 0:
                if current_book:
                    books.append(current_book)
                current_book = {
                    'name': title,
                    'type': 'multi_chapter',
                    'files': [src],
                    'chapters': []  # L1 children
                }
            elif level >= 1 and current_book:
                current_book['chapters'].append({
                    'name': title,
                    'file': src
                })
                if src not in current_book['files']:
                    current_book['files'].append(src)

        if current_book:
            books.append(current_book)

        # 展开 spine 匹配
        for book in books:
            expanded = expand_files(book['files'], spine_items)
            book['files'] = expanded
            book['estimated_chars'] = estimate_chars(expanded, extract_dir)

        return books

    else:
        # 单层 TOC：检测是否为"部/章"结构
        # 更精确的匹配：标题含"第"且后跟数字/中文数字，或含"部""章""Part""Volume"
        part_pattern = re.compile(r'第[一二三四五六七八九十百千\d]+[部章卷节回]')
        parts = []
        current_part = None
        orphan_entries = []  # 不匹配 is_part 的条目

        for entry in toc_entries:
            title = entry['title']
            src = entry['src']

            if is_skip(title):
                continue

            is_part = bool(part_pattern.search(title)) or \
                      any(kw in title for kw in ['Part ', 'part ', 'Volume '])

            if is_part:
                if current_part:
                    parts.append(current_part)
                current_part = {
                    'name': title,
                    'type': 'single',
                    'files': [src.split('#')[0]]
                }
            elif current_part:
                # 属于当前 part 的子条目
                f = src.split('#')[0]
                if f not in current_part['files']:
                    current_part['files'].append(f)
            else:
                # 不属于任何 part，记录下来
                orphan_entries.append(entry)

        if current_part:
            parts.append(current_part)

        # 将孤立条目附加到最近的 part，或作为独立条目
        for orphan in orphan_entries:
            src = orphan['src'].split('#')[0]
            if parts:
                # 附加到上一个 part
                if src not in parts[-1]['files']:
                    parts[-1]['files'].append(src)
            else:
                # 作为独立 part
                parts.append({
                    'name': orphan['title'],
                    'type': 'single',
                    'files': [src]
                })

        if parts:
            for part in parts:
                expanded = expand_files(part['files'], spine_items)
                part['files'] = expanded
                part['estimated_chars'] = estimate_chars(expanded, extract_dir)
            return parts

        # 回退：每个 TOC 条目是一个章节
        chapters = []
        for entry in toc_entries:
            if not is_skip(entry['title']):
                chapters.append({
                    'name': entry['title'],
                    'type': 'single',
                    'files': [entry['src'].split('#')[0]],
                    'estimated_chars': 0
                })
        return chapters


def expand_files(base_files, spine_items):
    """将基础文件名展开为完整的 spine 文件列表

    精确匹配：base_file 的文件名部分必须在 spine 中存在
    """
    all_files = []
    spine_hrefs = {os.path.basename(item['href']): item['href'] for item in spine_items}

    for base_file in base_files:
        basename = os.path.basename(base_file)
        if basename in spine_hrefs:
            href = spine_hrefs[basename]
            if href not in all_files:
                all_files.append(href)
        else:
            # 回退：前缀匹配（处理 split 文件的情况）
            prefix = basename.split('_')[0] if '_' in basename else \
                     basename.replace('.html', '').replace('.xhtml', '')
            for item in spine_items:
                if os.path.basename(item['href']).startswith(prefix):
                    if item['href'] not in all_files:
                        all_files.append(item['href'])

    return all_files if all_files else base_files


def estimate_chars(files, extract_dir):
    """快速估算文本字数（采样多个文件取平均）"""
    if not files:
        return 0

    # 采样：取前 3 个文件和最后 1 个文件
    sample_indices = list(set([0, 1, 2, len(files) - 1]))
    sample_indices = [i for i in sample_indices if i < len(files)]

    total_sampled_chars = 0
    sampled_count = 0

    for idx in sample_indices:
        sample_file = files[idx]
        for root, dirs, fs in os.walk(extract_dir):
            for f in fs:
                if f == os.path.basename(sample_file) or sample_file.endswith(f):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                            text = fh.read(5000)
                        parser = HTMLTextExtractor()
                        parser.feed(text)
                        clean = parser.get_text().strip()
                        total_sampled_chars += len(clean)
                        sampled_count += 1
                    except:
                        pass
                    break

    if sampled_count == 0:
        return 0

    avg_chars_per_file = total_sampled_chars / sampled_count
    # read 5000 bytes but actual file may be larger, scale by ratio
    # Assume sampled portion is representative
    return int(avg_chars_per_file * len(files))


# ── 阶段二：按需提取 ──────────────────────────────────────────

def extract_book(extract_dir, book_info, chapters_dir, book_index):
    """阶段二：提取指定书的文本

    book_info: build_books_list 返回的单个 book dict
    返回 list of chapter dicts: [{index, name, file, length}]
    """
    os.makedirs(chapters_dir, exist_ok=True)
    chapters = []

    if book_info.get('chapters'):
        # 多章：每章一个文件
        for i, ch_info in enumerate(book_info['chapters']):
            text = extract_single_file(extract_dir, ch_info['file'])
            if text and len(text) > 50:
                ch_file = f'book{book_index}_ch{i+1:02d}.txt'
                with open(os.path.join(chapters_dir, ch_file), 'w', encoding='utf-8') as f:
                    f.write(text)
                chapters.append({
                    'index': i + 1,
                    'name': ch_info['name'],
                    'file': ch_file,
                    'length': len(text)
                })
    else:
        # 单文件或合并文件
        all_text = []
        for file_name in book_info['files']:
            text = extract_single_file(extract_dir, file_name)
            if text and len(text) > 50:
                all_text.append(text)

        if all_text:
            combined = '\n\n'.join(all_text)
            ch_file = f'book{book_index}_ch01.txt'
            with open(os.path.join(chapters_dir, ch_file), 'w', encoding='utf-8') as f:
                f.write(combined)
            chapters.append({
                'index': 1,
                'name': book_info['name'],
                'file': ch_file,
                'length': len(combined)
            })

    return chapters


def extract_single_file(extract_dir, file_name):
    """从解压目录中提取单个文件的纯文本"""
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f == file_name or file_name.endswith(f):
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    parser = HTMLTextExtractor()
                    parser.feed(content)
                    text = parser.get_text()
                    text = re.sub(r'\n\s*\n', '\n\n', text)
                    return text.strip()
                except Exception as e:
                    print(f"Warning: Failed to process {file_name}: {e}", file=sys.stderr)
                    return None
    return None


def diagnose_layer0(metadata):
    """Layer 0: OPF 元数据诊断（<5ms）

    dc:type → 直接映射
    dc:subject / dc:description → 关键词匹配
    返回 (mode, confidence, reason) 或 None
    """
    dc_type = (metadata.get('dc_type') or '').lower()
    subjects = ' '.join(metadata.get('dc_subjects', [])).lower()
    description = (metadata.get('dc_description') or '').lower()
    combined = f"{subjects} {description}"

    type_map = {
        'poetry': ('poetry', 'OPF dc:type 标注为 poetry'),
        'drama': ('drama', 'OPF dc:type 标注为 drama'),
        'nonfiction': ('nonfiction', 'OPF dc:type 标注为 nonfiction'),
    }
    if dc_type in type_map:
        return type_map[dc_type]

    kw_map = [
        (['诗集', '诗歌', 'poetry', 'poems', 'verse'], 'poetry'),
        (['剧本', '戏剧', 'drama', 'play', 'theatre'], 'drama'),
        (['散文', '随笔', '杂文', 'essay', 'prose'], 'essay'),
        (['书信', '日记', '信札', 'letter', 'diary', 'epistolary'], 'epistolary'),
        (['短篇小说', '短篇集', '故事集', 'short stories'], 'anthology'),
        (['长篇小说', 'novel'], 'standard_chapter'),
        (['传记', '回忆录', 'biography', 'memoir'], 'nonfiction'),
    ]
    for keywords, mode in kw_map:
        for kw in keywords:
            if kw in combined:
                return mode, 'high', f'元数据含关键词「{kw}」'

    return None


def diagnose_layer1(toc_entries, books_count):
    """Layer 1: TOC 结构指纹（<10ms）

    条目数、层级深度、标题文本模式
    返回 (mode, confidence, reason) 或 None
    """
    if not toc_entries:
        return None

    names = [e['title'] for e in toc_entries if e.get('level', 0) == 0]
    names_lower = [n.lower() for n in names]

    if books_count > 1:
        narrative_kw = ['部', '章', '卷', 'part', 'chapter', 'volume']
        seq = sum(1 for n in names_lower if any(kw in n for kw in narrative_kw))
        if books_count <= 5 and seq >= books_count * 0.6:
            return 'standard_chapter', 'high', f'{books_count} 部连续叙事'
        return 'library', 'high', f'TOC 检测到 {books_count} 本独立书籍'

    kw_groups = [
        (['散文', '随笔', '杂文', '书信', '日记', 'essay', 'memoir', 'letter', 'diary'], 'essay'),
        (['幕', '场', 'act', 'scene'], 'drama'),
        (['篇', '故事', '短篇', '小说集', 'story', 'stories'], 'anthology'),
        (['卷', '册', '全集', '选集', '文集'], 'library'),
    ]
    for keywords, mode in kw_groups:
        for n in names_lower:
            for kw in keywords:
                if kw in n:
                    return mode, 'high', f'TOC 含关键词「{kw}」'

    num = len(names)
    if num == 0:
        return None
    if num == 1:
        return 'short', 'medium', '单章文本'
    if num > 20:
        return 'grouped_epic', 'high', f'{num} 章'

    strong = ['部', '卷', '册', 'Part', 'Volume']
    if num <= 10 and any(any(kw in n for kw in strong) for n in names):
        return 'standard_chapter', 'high', f'{num} 部/卷'

    return None


def diagnose_layer2(extract_dir, spine_items):
    """Layer 2: 内容采样（<200ms，按需）

    取前 1-2 个文件的前 5KB，统计文本特征
    返回 (mode, confidence, reason) 或 None
    """
    content_files = [s for s in spine_items if s['media_type'] == 'application/xhtml+xml'][:2]
    if not content_files:
        return None

    texts = []
    for item in content_files:
        basename = os.path.basename(item['href'])
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f == basename or item['href'].endswith(f):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                            raw = fh.read(8000)
                        parser = HTMLTextExtractor()
                        parser.feed(raw)
                        texts.append(parser.get_text().strip())
                    except:
                        pass
                    break

    combined = '\n'.join(texts)
    if len(combined) < 100:
        return None

    lines = [l.strip() for l in combined.split('\n') if l.strip()]

    # 诗歌：行均 < 40 字符 + 高换行密度
    if lines:
        avg = sum(len(l) for l in lines) / len(lines)
        density = len(lines) / max(len(combined), 1)
        if avg < 40 and density > 0.02:
            return 'poetry', 'medium', f'行均 {avg:.0f} 字符 → 诗歌特征'

    # 剧本：对话标记密度高
    quotes = combined.count('"') + combined.count('"') + combined.count('「')
    colons = len(re.findall(r'[一-鿿]{2,6}[:：]', combined))
    if len(combined) > 0 and (quotes + colons * 2) / len(combined) > 0.08:
        return 'drama', 'medium', '对话标记密度高 → 剧本特征'

    # 散文：第一人称高频 + 时间推进词少
    first_person = combined.count('我') + combined.count('我们')
    time_markers = len(re.findall(r'[后来然后接着随后最终]', combined))
    if first_person > 5 and time_markers < 3:
        return 'essay', 'medium', f'第一人称 {first_person} 次，时间词 {time_markers} 次 → 散文特征'

    return None


def diagnose(metadata, toc_entries, books_count, extract_dir=None, spine_items=None):
    """三层诊断流水线

    Layer 0: OPF 元数据 → Layer 1: TOC 指纹 → Layer 2: 内容采样
    返回 (mode, confidence, reason, layer)
    """
    cached = None  # 由调用方检查缓存

    r = diagnose_layer0(metadata)
    if r:
        return (*r, 0)

    r = diagnose_layer1(toc_entries, books_count)
    if r:
        return (*r, 1)

    if extract_dir and spine_items:
        r = diagnose_layer2(extract_dir, spine_items)
        if r:
            return (*r, 2)

    return 'standard_chapter', 'low', '无法自动判定', -1


def load_diagnosis_cache(sha, state_dir):
    """加载诊断缓存"""
    p = state_dir / f'{sha}-diagnosis.json'
    if p.exists():
        try:
            return json.load(open(p, encoding='utf-8'))
        except:
            pass
    return None


def save_diagnosis_cache(sha, state_dir, mode, confidence, reason, layer):
    """保存诊断缓存"""
    p = state_dir / f'{sha}-diagnosis.json'
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'mode': mode, 'confidence': confidence, 'reason': reason,
                   'layer': layer, 'cached_at': datetime.now().isoformat()}, f,
                  ensure_ascii=False, indent=2)


def should_ask_user(confidence):
    """仅 low 置信度需要用户确认"""
    return confidence == 'low'


# ── 进度文件管理 ──────────────────────────────────────────────

def create_progress(sha, title, author, mode, chapters, output_path, books=None):
    """生成 progress.json"""
    progress = {
        'book_sha': sha,
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
        'characters': [],
        'used_thematic_probes': 0,
        'consecutive_transitional': 0,
        'created_at': datetime.now().isoformat(),
        'reader_signals': []
    }

    if books:
        progress['books'] = books
        progress['current_book'] = 0

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    return progress


def create_bookmark(sha, title, author, progress_path, bookmark_path):
    """创建书签文件"""
    bookmark = {
        'book_sha': sha,
        'title': title,
        'author': author,
        'progress_path': str(progress_path),
        'created_at': datetime.now().isoformat()
    }
    with open(bookmark_path, 'w', encoding='utf-8') as f:
        json.dump(bookmark, f, ensure_ascii=False, indent=2)
    return bookmark


# ── CLI ──────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python init_book.py <epub_path>              # 阶段一：快速初始化")
        print("  python init_book.py <epub_path> --extract N   # 阶段二：提取第N本书")
        sys.exit(1)

    epub_path = sys.argv[1]

    if not os.path.exists(epub_path):
        print(f"错误: 文件不存在: {epub_path}")
        sys.exit(1)

    skill_dir = Path(__file__).parent.parent
    state_dir = skill_dir / 'state'
    chapters_dir = state_dir / 'chapters'

    # ── 阶段二：按需提取 ──
    if '--extract' in sys.argv:
        idx = sys.argv.index('--extract')
        if idx + 1 >= len(sys.argv):
            print("错误: --extract 需要书的索引号")
            sys.exit(1)

        book_index = int(sys.argv[idx + 1])

        # 快速初始化获取书籍信息
        print(f"准备提取第 {book_index} 本书...")
        init = quick_init(epub_path)

        if book_index < 1 or book_index > len(init['books']):
            print(f"错误: 索引超出范围 (1-{len(init['books'])})")
            sys.exit(1)

        book = init['books'][book_index - 1]
        print(f"书名: {book['name']}")
        print(f"提取文本...")

        chapters = extract_book(init['extract_dir'], book, chapters_dir, book_index)
        print(f"提取完成: {len(chapters)} 章")

        # 模式诊断（三层流水线）
        is_library = len(init['books']) > 1
        if is_library:
            mode = 'standard_chapter'
            confidence = 'high'
            reason = 'library 内的单本书'
            layer = 0
        else:
            # 构造 toc_entries 用于 Layer 1
            fake_toc = [{'level': 0, 'title': ch['name'], 'src': ''} for ch in chapters]
            mode, confidence, reason, layer = diagnose(
                init['metadata'], fake_toc, 1,
                extract_dir=init['extract_dir'],
                spine_items=init['spine_items']
            )
            # 保存诊断缓存
            save_diagnosis_cache(init['sha'], state_dir, mode, confidence, reason, layer)

        # 构建该书的独立状态
        book_progress = {
            'book_sha': init['sha'],
            'book_index': book_index,
            'book_title': book['name'],
            'author': init['author'],
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
            'characters': [],
            'used_thematic_probes': 0,
            'consecutive_transitional': 0,
            'reader_signals': []
        }

        if is_library:
            # library 模式：写入该书的独立状态文件，不覆盖主 progress.json
            book_progress_path = state_dir / f'{init["sha"]}_book{book_index}-progress.json'
            with open(book_progress_path, 'w', encoding='utf-8') as f:
                json.dump(book_progress, f, ensure_ascii=False, indent=2)

            # 创建该书的输出目录
            book_output_dir = skill_dir / 'output' / init['sha'] / f'book{book_index}'
            os.makedirs(book_output_dir, exist_ok=True)

            total_chars = sum(c['length'] for c in chapters)
            print(f"总字数: {total_chars:,}")
            print(f"模式: {mode}")
            print(f"书状态文件: {book_progress_path}")
            print(f"输出目录: {book_output_dir}")

            result = {
                'status': 'ok',
                'book_index': book_index,
                'book_name': book['name'],
                'chapters': len(chapters),
                'total_chars': total_chars,
                'mode': mode,
                'confidence': confidence,
                'reason': reason,
                'is_library': True,
                'progress_file': str(book_progress_path)
            }
        else:
            # 单书模式：写入主 progress.json
            progress_path = state_dir / f'{init["sha"]}-progress.json'
            book_progress['created_at'] = datetime.now().isoformat()
            with open(progress_path, 'w', encoding='utf-8') as f:
                json.dump(book_progress, f, ensure_ascii=False, indent=2)

            total_chars = sum(c['length'] for c in chapters)
            print(f"总字数: {total_chars:,}")
            print(f"模式: {mode}")
            print(f"进度文件: {progress_path}")

            result = {
                'status': 'ok',
                'book_name': book['name'],
                'chapters': len(chapters),
                'total_chars': total_chars,
                'mode': mode,
                'confidence': confidence,
                'reason': reason,
                'is_library': False,
                'progress_file': str(progress_path)
            }

        print(f"\n{json.dumps(result, ensure_ascii=False)}")
        return

    # ── 阶段三：标记完成 ──
    if '--complete' in sys.argv:
        idx = sys.argv.index('--complete')
        if idx + 1 >= len(sys.argv):
            print("错误: --complete 需要书的索引号")
            sys.exit(1)

        book_index = int(sys.argv[idx + 1])
        sha = calculate_sha256(epub_path)
        progress_path = state_dir / f'{sha}-progress.json'

        if not progress_path.exists():
            print("错误: 未找到主 progress.json，请先运行阶段一")
            sys.exit(1)

        progress = json.load(open(progress_path, encoding='utf-8'))

        if 'books' not in progress:
            print("错误: 非 library 模式，无需 --complete")
            sys.exit(1)

        if book_index < 1 or book_index > len(progress['books']):
            print(f"错误: 索引超出范围 (1-{len(progress['books'])})")
            sys.exit(1)

        # 标记完成
        progress['books'][book_index - 1]['status'] = 'completed'
        progress['current_book'] = book_index  # 指向下一本

        # 统计已完成数
        completed = sum(1 for b in progress['books'] if b.get('status') == 'completed')
        total = len(progress['books'])

        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

        result = {
            'status': 'ok',
            'book_index': book_index,
            'book_title': progress['books'][book_index - 1]['title'],
            'completed': completed,
            'total': total,
            'all_done': completed == total
        }
        print(f"\n{json.dumps(result, ensure_ascii=False)}")
        return

    # ── 阶段一：快速初始化 ──
    print(f"正在初始化: {epub_path}")

    # 检查已有书签
    sha = calculate_sha256(epub_path)
    bookmark_path = state_dir / f'{sha}-bookmark.json'

    print("计算 SHA256...")
    print(f"SHA256: {sha}")

    print("解压 EPUB...")
    init = quick_init(epub_path)
    print(f"解压完成: {init['extract_dir']}")

    print(f"书名: {init['title']}")
    print(f"作者: {init['author']}")

    print(f"解析目录结构...")
    print(f"书籍数: {len(init['books'])}")

    # 创建目录
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(chapters_dir, exist_ok=True)
    output_dir = skill_dir / 'output' / sha
    os.makedirs(output_dir, exist_ok=True)

    # 判断模式（三层流水线 + 缓存）
    books_count = len(init['books'])

    # 检查诊断缓存
    cached = load_diagnosis_cache(sha, state_dir)
    if cached:
        mode = cached['mode']
        confidence = cached['confidence']
        reason = cached['reason']
        layer = cached.get('layer', -1)
    else:
        # 三层诊断
        mode, confidence, reason, layer = diagnose(
            init['metadata'], init['toc_entries'], books_count,
            extract_dir=init['extract_dir'],
            spine_items=init['spine_items']
        )
        save_diagnosis_cache(sha, state_dir, mode, confidence, reason, layer)

    if books_count > 1:
        books_meta = []
        for i, book in enumerate(init['books']):
            books_meta.append({
                'index': i + 1,
                'title': book['name'],
                'type': book.get('type', 'unknown'),
                'chapters_count': len(book.get('chapters', [])),
                'estimated_chars': book.get('estimated_chars', 0)
            })
    else:
        books_meta = None

    # 生成空 progress.json（只有书籍元数据，无文本）
    progress_path = state_dir / f'{sha}-progress.json'
    progress = {
        'book_sha': sha,
        'title': init['title'],
        'author': init['author'],
        'mode': mode,
        'total_chapters': 0,
        'current_chapter': 0,
        'chapters': [],
        'characters': [],
        'used_thematic_probes': 0,
        'consecutive_transitional': 0,
        'created_at': datetime.now().isoformat(),
        'reader_signals': []
    }
    if books_meta:
        progress['books'] = books_meta
        progress['current_book'] = 0

    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    # 创建书签
    create_bookmark(sha, init['title'], init['author'], progress_path, bookmark_path)

    # 完成
    print(f"模式: {mode}")
    print(f"进度文件: {progress_path}")
    print(f"书签文件: {bookmark_path}")

    print("\n" + "=" * 50)
    print("[OK] 初始化完成!")
    print(f"书名: {init['title']}")
    print(f"作者: {init['author']}")
    print(f"书籍数: {len(init['books'])}")
    print(f"模式: {mode}")
    print(f"置信度: {confidence} — {reason}")
    print(f"SHA256: {sha}")
    print("=" * 50)

    # 输出 JSON 供 Claude 读取
    result = {
        'status': 'ok',
        'title': init['title'],
        'author': init['author'],
        'mode': mode,
        'confidence': confidence,
        'reason': reason,
        'diagnosis_layer': layer,
        'need_user_confirm': should_ask_user(confidence),
        'books_count': len(init['books']),
        'books': books_meta
    }
    print(f"\n{json.dumps(result, ensure_ascii=False)}")


if __name__ == '__main__':
    main()
