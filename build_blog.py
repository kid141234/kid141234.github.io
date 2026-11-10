"""把 blog/optimization/meta.json 中的文章渲染成页面，并同步主页的「优化」专题。

用法（在项目根目录 personal-homepage/ 下）：
    python build_blog.py

输入：
    blog/optimization/meta.json   专题元信息 + 文章顺序、标题、简介、渲染开关
    blog/<slug>.md                每篇文章的 Markdown 源文件

输出：
    dist/blog/<slug>.html         文章阅读页（公式由 MathJax 运行时渲染）
    dist/blog/optimization/index.html   「优化」专题首页
    dist/content.js               末尾的「优化」专题数据段（由标记包裹）

新增一篇文章：把 Markdown 放进 blog/，在 meta.json 的 articles 中加一条，
重新运行本脚本即可。articles 的顺序决定专题首页列表与主页专题卡片里的篇数。

John Lee 专题由 build_notes.py 单独维护：它覆写 content.js 中 BEGIN 专题 /
END 专题 标记的 topics 区块。本脚本不碰那个区块，只在文件末尾把「优化」
专题插到 topics 数组最前面，两个脚本因此互不干扰，运行顺序不限。

公式用占位符保护后原样交给 MathJax 运行时渲染，不预编译。
文章里的内联 HTML（示意图、锚点等）由配置中的 html 开关控制。
"""

from html import escape
from pathlib import Path
import json
import re
from markdown_it import MarkdownIt

root = Path(__file__).resolve().parent
META = json.loads((root / 'blog' / 'optimization' / 'meta.json').read_text(encoding='utf-8'))
TOPIC = META['topic']
ARTICLES = META['articles']

MATH_RE = r'(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|(?<!\\)\$(?!\$)[^\n$]*?(?<!\\)\$'
ANCHOR_LINE = re.compile(r'(?m)^<a\s+id="([^"]+)"\s*>\s*</a>[ \t]*$\n?')
ANCHOR_PARA = re.compile(r'<p>\s*BLOGANCHOR(\d+)END\s*</p>\s*<h2\s+id="(section-\d+)"')

PAGE_HEAD = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="'''
PAGE_HEAD_2 = '''">
<title>'''
PAGE_HEAD_3 = ''' · 高源的学习笔记</title><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="blog.css">
<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]},svg:{fontCache:'global'}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script></head>
<body id="top"><a class="skip-link" href="#article">跳转到正文</a><header class="site-header"><div class="header-inner"><a class="brand" href="../index.html"><span class="brand-mark" aria-hidden="true">✳</span> 个人主页<span class="brand-slash"> / </span><span class="brand-en">PERSONAL SPACE</span></a><a class="back-link" href="../index.html#blog">← 返回博客</a></div></header>
<div class="article-layout"><aside class="article-toc" aria-label="文章目录"><p>目录 <span>CONTENTS</span></p><ol>'''
PAGE_MID = '''</ol></aside><main id="article" class="article"><p class="article-kicker">'''
PAGE_TAIL = '''</p>'''  # 由调用处拼接正文与页尾
PAGE_END = '''<div class="article-end"><a href="../index.html#blog">← 返回博客列表</a><a href="#top">回到顶部 ↑</a></div></main></div><footer class="site-footer"><div class="footer-inner"><p>© 高源 · Personal Homepage</p><p>保持好奇，慢慢积累。</p></div></footer></body></html>'''

TOPIC_PAGE = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{description}">
<title>{title} · 专题目录 · 高源的学习笔记</title><link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../../styles.css"><link rel="stylesheet" href="../blog.css"><link rel="stylesheet" href="../notes.css"></head>
<body id="top"><a class="skip-link" href="#article">跳转到正文</a><header class="site-header"><div class="header-inner"><a class="brand" href="../../index.html"><span class="brand-mark" aria-hidden="true">✳</span> 个人主页<span class="brand-slash"> / </span><span class="brand-en">PERSONAL SPACE</span></a><a class="back-link" href="../../index.html#blog">← 返回学习笔记</a></div></header>
<div class="article-layout"><aside class="article-toc" aria-label="文章目录"><p>目录 <span>CONTENTS</span></p><ol>{toc}</ol></aside><main id="article" class="article"><p class="article-kicker">学习笔记 / {kicker} · 专题目录</p><h1>{title} · 专题目录</h1><p class="article-lead">{description}</p><p class="article-source">以下 {count} 篇文章按专题顺序排列，文章中的公式由 MathJax 渲染，点击标题即可进入对应文章。</p><ol class="note-series">{series}</ol><div class="article-end"><a href="../../index.html#blog">← 返回学习笔记</a><a href="#top">回到顶部 ↑</a></div></main></div><footer class="site-footer"><div class="footer-inner"><p>© 高源 · Personal Homepage</p><p>保持好奇，慢慢积累。</p></div></footer></body></html>'''

TOPIC_BEGIN = '\n// --- BEGIN 优化专题：由 build_blog.py 生成，请勿手工改动 ---\n'
TOPIC_END = '// --- END 优化专题 ---\n'


def render_article(cfg):
    source = (root / 'blog' / (cfg['slug'] + '.md')).read_text(encoding='utf-8')
    source = re.sub(r'\n```\s*\n\s*```\s*$', '\n', source)

    # 标题前的 <a id="..."> 单独成行时，先换成纯文本占位符；
    # 渲染后与紧随其后的 h2 合并，避免页面里留下空段落。
    anchors = []
    if cfg['merge_anchors']:
        def stash(match):
            anchors.append(match.group(1))
            return 'BLOGANCHOR%dEND\n' % (len(anchors) - 1)
        source = ANCHOR_LINE.sub(stash, source)

    math = []

    def protect(match):
        math.append(match.group())
        return 'MATHPLACEHOLDER%dEND' % (len(math) - 1)

    source = re.sub(MATH_RE, protect, source)
    md = MarkdownIt('commonmark', {'html': cfg['html']}).enable('table')
    tokens = md.parse(source)

    headings = []
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag == 'h2':
            anchor = 'section-%d' % (len(headings) + 1)
            token.attrSet('id', anchor)
            title = tokens[i + 1].content
            headings.append(None if title in cfg['skip_toc'] else (anchor, title))

    content = md.renderer.render(tokens, md.options, {})
    for i, formula in enumerate(math):
        content = content.replace('MATHPLACEHOLDER%dEND' % i, escape(formula))
    content = re.sub(r'<table>', '<div class="table-wrap"><table>', content).replace(
        '</table>', '</table></div>')

    anchor_map = {}
    if cfg['merge_anchors']:
        def merge(match):
            real = anchors[int(match.group(1))]
            anchor_map[match.group(2)] = real
            return '<h2 id="%s"' % real
        content = ANCHOR_PARA.sub(merge, content)

    toc_items = []
    for item in headings:
        if item is None:
            continue
        anchor, title = item
        toc_items.append('<li><a href="#%s">%s</a></li>' % (
            anchor_map.get(anchor, anchor), escape(title)))
    toc = ''.join(toc_items)

    html = (PAGE_HEAD + escape(cfg['description'], quote=True) + PAGE_HEAD_2
            + escape(cfg['title']) + PAGE_HEAD_3 + toc + PAGE_MID
            + escape(cfg['kicker']) + PAGE_TAIL + content + PAGE_END)
    out = root / 'dist' / 'blog' / (cfg['slug'] + '.html')
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print('Generated %s: %d sections, %d formulas' % (out.name, len(headings), len(math)))


def render_topic_index():
    toc = ''.join('<li><a href="../%s.html">%s</a></li>' % (
        a['slug'], escape(a['title'], quote=True)) for a in ARTICLES)
    series = ''.join(
        '<li><a href="../{slug}.html"><span class="series-no">{no:02d}</span>'
        '<span class="series-main"><strong>{title}</strong><small>{desc}</small></span>'
        '<span class="series-arrow">阅读 →</span></a></li>'.format(
            slug=a['slug'], no=i, title=escape(a['title']),
            desc=escape(a['description']))
        for i, a in enumerate(ARTICLES, start=1))
    html = TOPIC_PAGE.format(
        title=escape(TOPIC['title']),
        kicker=escape(TOPIC['kicker']),
        description=escape(TOPIC['description'], quote=True),
        count=len(ARTICLES), toc=toc, series=series)
    out = root / 'dist' / 'blog' / 'optimization' / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print('Generated optimization/index.html: %d 篇文章' % len(ARTICLES))


def sync_content_js():
    """把「优化」专题插到 content.js 的 topics 最前面，不覆盖 John Lee 区块。"""
    path = root / 'dist' / 'content.js'
    source = path.read_text(encoding='utf-8')
    topic = {
        'title': TOPIC['title'],
        'english': TOPIC['english'],
        'description': TOPIC['description'],
        'url': TOPIC['url'],
        'notes': [{'title': a['title'], 'description': a['description'],
                   'url': 'blog/%s.html' % a['slug']} for a in ARTICLES],
    }
    payload = json.dumps(topic, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    block = (TOPIC_BEGIN + '// 插到数组最前面：主页上的专题顺序为「优化」→ John Lee\n'
             'window.HOMEPAGE.topics = [\n  ' + payload + ',\n'
             '  ...(window.HOMEPAGE.topics || []).filter('
             't => t.title !== ' + json.dumps(TOPIC['title'], ensure_ascii=False) + ')\n'
             '];\n' + TOPIC_END)
    if TOPIC_BEGIN in source and TOPIC_END in source:
        start = source.index(TOPIC_BEGIN)
        stop = source.index(TOPIC_END) + len(TOPIC_END)
        source = source[:start] + block + source[stop:]
    else:
        source = source.rstrip('\n') + '\n' + block
    path.write_text(source, encoding='utf-8')
    print('Synced content.js: 优化专题（%d 篇文章）' % len(ARTICLES))


def main():
    for article in ARTICLES:
        render_article(article)
    render_topic_index()
    sync_content_js()


if __name__ == '__main__':
    main()
