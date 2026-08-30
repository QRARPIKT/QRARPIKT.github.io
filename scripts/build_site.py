#!/usr/bin/env python3
"""本格文库建站脚本：从书籍交付目录生成/更新 Qラピカ文库静态站。

书籍交付目录约定（扁平结构）:
    <book-dir>/
    ├── chapters/ch01.md ...   # 分章原稿（唯一可编辑源；首行为 "# 第N章 标题"）
    ├── documents/*.md          # truth/summaries/characters/foreshadowing/threads/world 等
    ├── final.md / final.txt    # 合订终稿（脚本同步产物）
    └── reviews/（可选）        # 外审报告等留存件

用法（在本仓库根目录执行）:
    python3 scripts/build_site.py --book-dir incoming/<book-id> --site-dir . \
        --book-id proof-read --title "校　样" \
        --meta "本格推理短篇 · 全十三章 · 约4.3万字 · 2026" \
        --blurb "一句话引子（分类页作品卡）" --section exercise

行为:
 1. 拆分 chapters/ → works/<book-id>/chNN.html（文库模板：工具栏/目录抽屉/上下章）
 2. 全量复制档案 → archive/<book-id>/（网页不直链，仅仓库留存）
 3. works/<book-id>/index.html 与 notes.html 不存在时生成骨架（含 TODO 标记），
    已存在则跳过——简介与手记属人工撰写，脚本永不覆盖
 4. 首页 index.html 中若无该书作品卡，则插入；已存在则跳过
 5. assets/style.css 与 reader.js 不存在时才生成——已存在则跳过（现行样式含人工增补，永不覆盖）
"""
import argparse, io, os, re, html, shutil, sys

# STYLE 常量与 assets/style.css 保持一致（2026-08 同步，含表格样式增补）；
# style.css 若有手工改动，请同步更新此常量。
STYLE = ''':root{--bg:#faf7f0;--paper:#fffdf8;--ink:#2b2b28;--ink-soft:#6b675f;--line:#e4ddd0;--accent:#8a4b38;--accent-soft:#b08a7c;--font-size:17px;--measure:38em}
html[data-theme="night"]{--bg:#1c1a17;--paper:#26231f;--ink:#d8d2c6;--ink-soft:#9a927f;--line:#3a352d;--accent:#c98a70;--accent-soft:#8a6552}
*{box-sizing:border-box;margin:0;padding:0}
html{font-size:var(--font-size)}
body{background:var(--bg);color:var(--ink);font-family:"Source Han Serif SC","Noto Serif SC","Songti SC","SimSun",serif;line-height:2;letter-spacing:.02em;transition:background .3s,color .3s}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header.site{max-width:var(--measure);margin:0 auto;padding:3rem 1.2rem 2rem;border-bottom:1px solid var(--line)}
header.site .pen{font-size:1.6rem;letter-spacing:.15em}
header.site .pen small{display:block;font-size:.75rem;color:var(--ink-soft);letter-spacing:.3em;margin-top:.4rem}
nav.breadcrumb{font-size:.8rem;color:var(--ink-soft);margin-bottom:.6rem}
nav.breadcrumb a{color:var(--ink-soft)}
main{max-width:var(--measure);margin:0 auto;padding:2.5rem 1.2rem 5rem}
footer{max-width:var(--measure);margin:0 auto;padding:2rem 1.2rem 3rem;border-top:1px solid var(--line);font-size:.78rem;color:var(--ink-soft)}
.work-card{display:block;background:var(--paper);border:1px solid var(--line);padding:2rem 1.8rem;margin-bottom:1.5rem}
.work-card:hover{text-decoration:none;border-color:var(--accent-soft)}
.work-card h2{font-size:1.25rem;letter-spacing:.1em}
.work-card .meta{font-size:.78rem;color:var(--ink-soft);margin:.5rem 0 .8rem}
.work-card p{font-size:.9rem;color:var(--ink-soft);line-height:1.9}
.home-entry{position:relative;display:block;background:var(--paper);border:1px solid var(--line);padding:1.6rem 1.8rem;margin-bottom:1.2rem;overflow:hidden;transition:border-color .4s,box-shadow .4s}
.home-entry::before{content:"";position:absolute;left:0;top:0;height:2px;width:0;background:linear-gradient(90deg,var(--accent),var(--accent-soft));transition:width .5s ease}
.home-entry:hover{text-decoration:none;border-color:var(--accent-soft);box-shadow:0 3px 14px rgba(0,0,0,.07)}
.home-entry:hover::before{width:100%}
.home-entry .num{position:absolute;right:1rem;top:50%;transform:translateY(-50%);font-size:4.5rem;line-height:1;color:var(--ink);opacity:.07;pointer-events:none;transition:opacity .4s}
.home-entry:hover .num{opacity:.14}
.home-entry h2{font-size:1.3rem;letter-spacing:.3em}
.home-entry p{font-size:.85rem;color:var(--ink-soft);line-height:1.9;margin-top:0;opacity:0;max-height:0;overflow:hidden;transition:opacity .4s ease,max-height .4s ease,margin-top .4s ease}
.home-entry:hover p,.home-entry:focus-visible p{opacity:1;max-height:5em;margin-top:.4rem}
@media (max-width:600px){.home-entry p{opacity:1;max-height:none;margin-top:.4rem}.home-entry .num{font-size:3.2rem;top:.6rem;transform:none}}
.work-head{text-align:center;margin-bottom:3rem}
.work-head h1{font-size:1.8rem;letter-spacing:.2em;margin-bottom:.6rem}
.work-head .meta{font-size:.8rem;color:var(--ink-soft)}
.section-label{font-size:.8rem;letter-spacing:.3em;color:var(--accent);margin:2.5rem 0 1rem;border-bottom:1px solid var(--line);padding-bottom:.5rem}
.chapter-list{list-style:none}
.chapter-list li{border-bottom:1px solid var(--line)}
.chapter-list a{display:flex;justify-content:space-between;align-items:baseline;padding:.85rem .2rem;color:var(--ink)}
.chapter-list a:hover{color:var(--accent);text-decoration:none}
.chapter-list .no{font-size:.75rem;color:var(--ink-soft)}
.warn{border:1px solid var(--accent-soft);background:var(--paper);padding:1.2rem 1.4rem;margin:1.5rem 0;font-size:.85rem;line-height:1.9}
.warn strong{color:var(--accent);letter-spacing:.2em}
.reader-tools{position:fixed;top:0;left:0;right:0;z-index:20;display:flex;justify-content:center;gap:1.2rem;align-items:center;background:var(--bg);border-bottom:1px solid var(--line);padding:.55rem 1rem;font-size:.8rem}
.reader-tools button{font:inherit;color:var(--ink-soft);background:none;border:1px solid var(--line);padding:.15rem .7rem;cursor:pointer}
.reader-tools button:hover{color:var(--accent);border-color:var(--accent-soft)}
article.chapter{padding-top:2.5rem}
article.chapter h1{font-size:1.35rem;text-align:center;letter-spacing:.15em;margin-bottom:2.5rem}
article.chapter p{margin-bottom:1.1em;text-indent:2em;text-align:justify}
article.chapter hr{border:none;text-align:center;margin:2em 0;color:var(--ink-soft)}
article.chapter hr::after{content:"＊ ＊ ＊";letter-spacing:.5em}
.pager{display:flex;justify-content:space-between;margin-top:3.5rem;border-top:1px solid var(--line);padding-top:1.2rem;font-size:.85rem}
#toc-drawer{position:fixed;top:0;right:-280px;width:280px;height:100%;z-index:30;background:var(--paper);border-left:1px solid var(--line);transition:right .25s;padding:3rem 1.5rem;overflow-y:auto;font-size:.9rem}
#toc-drawer.open{right:0}
#toc-drawer a{display:block;padding:.45rem 0;color:var(--ink);border-bottom:1px solid var(--line)}
#toc-drawer a:hover{color:var(--accent);text-decoration:none}
#toc-drawer .close{position:absolute;top:.8rem;right:1rem;background:none;border:none;font-size:1rem;cursor:pointer;color:var(--ink-soft)}
.notes h2{font-size:1.05rem;letter-spacing:.15em;margin:2.2rem 0 .8rem;color:var(--accent)}
.notes p{margin-bottom:1em;text-indent:2em;text-align:justify;font-size:.95rem}
.notes ul{margin:0 0 1em 2em;font-size:.9rem;color:var(--ink-soft)}
.notes li{margin-bottom:.4em}
.songlist{background:var(--paper);border:1px solid var(--line);padding:1.2rem 1.6rem;margin:0 0 1.1em;line-height:2.2;font-size:.95rem}
article.chapter h2.sec{text-align:center;font-size:1.05rem;letter-spacing:.3em;margin:2.5em 0;color:var(--ink-soft)}
.board{background:var(--paper);border:1px solid var(--line);padding:1.1rem 1.4rem;margin:1.5em 0;font-family:"SF Mono",Menlo,Consolas,monospace;font-size:.85rem;line-height:2;white-space:pre-wrap;word-break:break-word}
.epigraph{text-align:center;color:var(--ink-soft);margin:0 0 2.5em;font-size:.95rem;letter-spacing:.15em}
.worklog{background:var(--paper);border:1px solid var(--line);border-left:3px solid var(--accent-soft);padding:1.2rem 1.5rem;margin:1.8em 0;font-family:"SF Mono",Menlo,Consolas,"Courier New",monospace;font-size:.82rem;line-height:1.9;white-space:pre-wrap;word-break:break-word;color:var(--ink-soft)}
@media (max-width:600px){html{font-size:calc(var(--font-size) - 1px)}header.site{padding-top:2rem}}

/* === 表格 === */
.table-scroll{overflow-x:auto;margin:1.4em 0}
.table-scroll table{border-collapse:collapse;width:100%;font-size:.92em;line-height:1.7}
.table-scroll th,.table-scroll td{border:1px solid #cfc8b8;padding:.45em .8em;text-align:left;vertical-align:top}
.table-scroll thead th{background:#efe9db;font-weight:600;white-space:nowrap}
.table-scroll tbody tr:nth-child(even){background:#faf7f0}

/* === 电脑屏幕式表格（过拟合 ch10 名单） === */
table.comp{border-collapse:collapse;width:100%;font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;font-size:.88em;line-height:1.65;background:#fdfdfb;box-shadow:0 1px 4px rgba(0,0,0,.12);border:1px solid #b9b3a4}
table.comp th{background:#e8e4d8;border:1px solid #b9b3a4;padding:.4em .7em;text-align:left;font-weight:600;white-space:nowrap}
table.comp td{border:1px solid #b9b3a4;padding:.35em .7em;text-align:left}
table.comp tbody tr:nth-child(even){background:#f4f1e8}
'''

READER_JS = '''(function(){var root=document.documentElement;
var saved=localStorage.getItem('qlib-theme');if(saved)root.setAttribute('data-theme',saved);
window.toggleTheme=function(){var t=root.getAttribute('data-theme')==='night'?'':'night';if(t)root.setAttribute('data-theme',t);else root.removeAttribute('data-theme');localStorage.setItem('qlib-theme',t);};
var fs=parseInt(localStorage.getItem('qlib-fs')||'17',10);function applyFs(){root.style.setProperty('--font-size',fs+'px');}applyFs();
window.fontSize=function(d){fs=Math.min(22,Math.max(14,fs+d));localStorage.setItem('qlib-fs',fs);applyFs();};
window.toggleToc=function(){var el=document.getElementById('toc-drawer');if(el)el.classList.toggle('open');};})();
'''

FOOTER = 'Qラピカ（Q拉比卡）· 本格推理文库 · 初稿与修订均由人机协作完成'

def md_to_html(body):
    out = []
    for blk in body.split('\n\n'):
        blk = blk.strip()
        if not blk:
            continue
        if blk == '---':
            out.append('<hr>')
            continue
        if blk.startswith('```'):
            # 代码围栏块：白板/表格
            inner = blk.strip('`').strip('\n')
            rows = [r for r in inner.split('\n') if r.strip()]
            if rows and rows[0].startswith('姓名'):
                # 全角空格对齐的投影表格 → 真表格
                parsed = [re.split(r'　+', r.strip()) for r in rows]
                head, body_rows = parsed[0], parsed[1:]
                h = '<div class="table-scroll"><table class="comp"><thead><tr>' + ''.join('<th>'+html.escape(c)+'</th>' for c in head) + '</tr></thead><tbody>'
                for rr in body_rows:
                    h += '<tr>' + ''.join('<td>'+html.escape(c)+'</td>' for c in rr) + '</tr>'
                out.append(h + '</tbody></table></div>')
            else:
                out.append('<pre class="board">' + html.escape(inner) + '</pre>')
            continue
        if blk.startswith('## '):
            out.append('<h2 class="sec">' + html.escape(blk[3:].strip()) + '</h2>')
            continue
        lines = [l.strip() for l in blk.split('\n') if l.strip()]
        if all(l.startswith('>') for l in lines):
            body = '\n'.join(l.lstrip('> ').lstrip('>') for l in lines).strip('\n')
            if '〔' in body:
                # 顾问工作记录等档案引文 → 代码块样式
                out.append('<pre class="worklog">' + html.escape(body) + '</pre>')
            else:
                # 题句/引用短句 → 居中题句样式
                out.append('<div class="epigraph">' + '<br>'.join(html.escape(x) for x in body.split('\n')) + '</div>')
            continue
        if all(re.match(r'^[一二三四五六七八九十]+、《', l) for l in lines):
            # 曲目/列表块 → 无边距列表样式
            out.append('<div class="songlist">' + '<br>'.join(html.escape(l) for l in lines) + '</div>')
            continue
        out.append('<p>' + '<br>'.join(html.escape(l) for l in lines) + '</p>')
    return '\n'.join(out)

def read_chapters(book_dir):
    chs = []
    for fn in sorted(os.listdir(os.path.join(book_dir, 'chapters'))):
        if not fn.endswith('.md'):
            continue
        raw = io.open(os.path.join(book_dir, 'chapters', fn), encoding='utf-8').read().strip()
        title = raw.split('\n', 1)[0].lstrip('# ').strip()
        body = re.sub(r'\n*---\s*$', '', raw.split('\n', 1)[1]).strip()
        chs.append((title, body))
    assert chs, 'chapters/ 为空'
    return chs

def write_chapter_pages(site, book_id, title_book, chs):
    wdir = os.path.join(site, 'works', book_id)
    os.makedirs(wdir, exist_ok=True)
    toc = '\n'.join(f'<a href="ch{i+1:02d}.html">{html.escape(t)}</a>' for i, (t, _) in enumerate(chs))
    for i, (t, body) in enumerate(chs):
        prev = f'<a href="ch{i:02d}.html">上一章</a>' if i > 0 else ''
        nxt = f'<a href="ch{i+2:02d}.html">下一章</a>' if i < len(chs) - 1 else ''
        page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(t)} · {html.escape(title_book)} · Qラピカ文库</title>
<link rel="stylesheet" href="../../assets/style.css">
</head>
<body>
<div class="reader-tools">
  <button onclick="toggleToc()">目录</button>
  <button onclick="fontSize(-1)">A−</button>
  <button onclick="fontSize(1)">A＋</button>
  <button onclick="toggleTheme()">夜间</button>
</div>
<nav id="toc-drawer">
  <button class="close" onclick="toggleToc()">×</button>
  {toc}
</nav>
<nav class="breadcrumb" style="max-width:38em;margin:3rem auto 0;padding:0 1.2rem">
  <a href="../../index.html">Qラピカ文库</a> / <a href="index.html">{html.escape(title_book)}</a>
</nav>
<main>
<article class="chapter">
<h1>{html.escape(t)}</h1>
{md_to_html(body)}
</article>
<div class="pager">
  <span>@PREV@</span><span><a href="index.html">回目录</a></span><span>@NEXT@</span>
</div>
</main>
<footer>{FOOTER}</footer>
<script src="../../assets/reader.js"></script>
</body>
</html>'''.replace('@NEXT@', nxt).replace('@PREV@', prev)
        io.open(os.path.join(wdir, f'ch{i+1:02d}.html'), 'w', encoding='utf-8').write(page)
    # 清理多余章节页（如旧版章数更多）
    for fn in os.listdir(wdir):
        m = re.match(r'ch(\d+)\.html$', fn)
        if m and int(m.group(1)) > len(chs):
            os.remove(os.path.join(wdir, fn))

def ensure_work_index(site, book_id, title_book, meta, chs):
    p = os.path.join(site, 'works', book_id, 'index.html')
    if os.path.exists(p):
        return 'skip(存在,人工页不覆盖)'
    items = '\n'.join(f'    <li><a href="ch{i+1:02d}.html">{html.escape(t)}<span class="no">{i+1:02d}</span></a></li>' for i, (t, _) in enumerate(chs))
    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title_book)} · Qラピカ文库</title>
<link rel="stylesheet" href="../../assets/style.css">
</head>
<body>
<nav class="breadcrumb" style="max-width:38em;margin:3rem auto 0;padding:0 1.2rem">
  <a href="../../index.html">Qラピカ文库</a> / {html.escape(title_book)}
</nav>
<main>
  <div class="work-head">
    <h1>{html.escape(title_book)}</h1>
    <div class="meta">{html.escape(meta)}</div>
  </div>
  <div class="section-label">故事简介（阅读前 · 无剧透）</div>
  <!-- TODO: 人工撰写无剧透简介，替换本注释与下段 -->
  <p style="text-indent:2em;text-align:justify">（简介待撰写）</p>
  <div class="section-label">正文</div>
  <ul class="chapter-list">
{items}
  </ul>
  <div class="section-label">创作手记（阅读后）</div>
  <div class="warn">
    <strong>泄底警告</strong><br>
    创作手记完整涉及本案诡计、凶手与时间线真相。请务必将正文读至最后一章后再进入。<a href="notes.html">我已读完，进入手记 →</a>
  </div>
</main>
<footer>{FOOTER}</footer>
<script src="../../assets/reader.js"></script>
</body>
</html>'''
    io.open(p, 'w', encoding='utf-8').write(page)
    return 'created(骨架,待人工撰写简介)'

def ensure_notes(site, book_id, title_book):
    p = os.path.join(site, 'works', book_id, 'notes.html')
    if os.path.exists(p):
        return 'skip(存在)'
    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>创作手记 · {html.escape(title_book)} · Qラピカ文库</title>
<link rel="stylesheet" href="../../assets/style.css">
</head>
<body>
<nav class="breadcrumb" style="max-width:38em;margin:3rem auto 0;padding:0 1.2rem">
  <a href="../../index.html">Qラピカ文库</a> / <a href="index.html">{html.escape(title_book)}</a> / 创作手记
</nav>
<main class="notes">
  <div class="work-head">
    <h1>创作手记</h1>
    <div class="meta">{html.escape(title_book)}</div>
  </div>
  <div class="warn"><strong>泄底警告</strong><br>本页完整讨论诡计结构、凶手身份与时间线真相。</div>
  <!-- TODO: 人工撰写创作手记（建议章节：起点与设计、修订故事、协作分工、档案指引） -->
  <p>（手记待撰写）</p>
</main>
<footer>{FOOTER}</footer>
<script src="../../assets/reader.js"></script>
</body>
</html>'''
    io.open(p, 'w', encoding='utf-8').write(page)
    return 'created(骨架)'

def ensure_home_card(site, book_id, title_book, meta, blurb, section=''):
    # section 非空时插入分类页（long/short/exercise），否则插入首页
    if section:
        home = os.path.join(site, section, 'index.html')
        if not os.path.exists(home):
            return f'skip(分类页 {section}/index.html 不存在)'
    else:
        home = os.path.join(site, 'index.html')
        if not os.path.exists(home):
            io.open(home, 'w', encoding='utf-8').write(f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Qラピカ文库</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site">
  <div class="pen">Qラピカ<small>本格推理文库</small></div>
</header>
<main>
<!--CARDS-->
</main>
<footer>{FOOTER}</footer>
</body>
</html>''')
    s = io.open(home, encoding='utf-8').read()
    if f'works/{book_id}/index.html' in s:
        return 'skip(卡片已存在)'
    prefix = '../' if section else ''
    card = f'''  <a class="work-card" href="{prefix}works/{book_id}/index.html">
    <h2>{html.escape(title_book)}</h2>
    <div class="meta">{html.escape(meta)}</div>
    <p>{html.escape(blurb)}</p>
  </a>
<!--CARDS-->'''
    if '<!--CARDS-->' not in s:
        return f'skip({"分类页" if section else "首页"}无 <!--CARDS--> 标记)'
    io.open(home, 'w', encoding='utf-8').write(s.replace('<!--CARDS-->', card, 1))
    return f'created({"分类页" if section else "首页"}卡片)'

def copy_archive(book_dir, site, book_id):
    adir = os.path.join(site, 'archive', book_id)
    os.makedirs(adir, exist_ok=True)
    n = 0
    for sub in ('chapters', 'documents', 'reviews'):
        src = os.path.join(book_dir, sub)
        if not os.path.isdir(src):
            continue
        dst = adir if sub == 'documents' else os.path.join(adir, sub)
        os.makedirs(dst, exist_ok=True)
        for fn in os.listdir(src):
            if fn.startswith('.'):
                continue
            shutil.copy2(os.path.join(src, fn), os.path.join(dst, fn))
            n += 1
    for fn, name in (('final.md', 'final_manuscript.md'), ('final.txt', 'final_manuscript.txt')):
        src = os.path.join(book_dir, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(adir, name))
            n += 1
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book-dir', required=True)
    ap.add_argument('--site-dir', required=True)
    ap.add_argument('--book-id', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--meta', default='')
    ap.add_argument('--blurb', default='')
    ap.add_argument('--section', default='', choices=['', 'long', 'short', 'exercise'],
                    help='书卡插入的分类页（long/short/exercise/index.html）；缺省插首页')
    a = ap.parse_args()

    # assets 只在缺失时生成：现行 style.css / reader.js 含人工增补，永不覆盖
    assets_dir = os.path.join(a.site_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    css_path = os.path.join(assets_dir, 'style.css')
    js_path = os.path.join(assets_dir, 'reader.js')
    if not os.path.exists(css_path):
        io.open(css_path, 'w', encoding='utf-8').write(STYLE)
    if not os.path.exists(js_path):
        io.open(js_path, 'w', encoding='utf-8').write(READER_JS)

    chs = read_chapters(a.book_dir)
    write_chapter_pages(a.site_dir, a.book_id, a.title, chs)
    r1 = ensure_work_index(a.site_dir, a.book_id, a.title, a.meta, chs)
    r2 = ensure_notes(a.site_dir, a.book_id, a.title)
    r3 = ensure_home_card(a.site_dir, a.book_id, a.title, a.meta, a.blurb, a.section)
    n = copy_archive(a.book_dir, a.site_dir, a.book_id)
    print(f'章节页 {len(chs)} 已生成 | 作品页 {r1} | 手记页 {r2} | 书卡 {r3} | 档案 {n} 件已复制')

if __name__ == '__main__':
    main()
