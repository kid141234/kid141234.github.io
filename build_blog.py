"""把 blog/*.md 渲染成 dist/blog/*.html。

新增一篇文章：把 Markdown 放进 blog/，在 ARTICLES 中加一条配置，
再到 dist/content.js 的 blog 数组里加卡片（顺序决定主页上的展示顺序）。

公式用占位符保护后原样交给 MathJax 运行时渲染，不预编译。
文章里的内联 HTML（示意图、锚点等）由配置中的 html 开关控制。
"""

from html import escape
from pathlib import Path
import re
from markdown_it import MarkdownIt

root = Path(__file__).resolve().parent

# slug 同时决定源文件名 blog/<slug>.md 与输出文件名 dist/blog/<slug>.html
ARTICLES = [
    {
        'slug': 'sgd-noise-geometry',
        'title': '优化器究竟在选择什么？',
        'description': '从随机梯度的稳定性与噪声几何出发，理解优化器如何影响模型的解与参数表示。',
        'kicker': '学习笔记 / OPTIMIZATION',
        'html': False,              # 源文没有内联 HTML
        'merge_anchors': False,
        'skip_toc': (),
    },
    {
        'slug': 'pretraining-optimization-lecture',
        'title': '球面动力学、学习率与权重衰减',
        'description': '从尺度不变性与球面更新出发，串联有效学习率、Hyperball、权重衰减平衡、河谷动力学，以及预训练优化器的比较口径。',
        'kicker': '学习笔记 / PRETRAINING OPTIMIZATION',
        'html': True,               # 含 <figure>/<svg> 示意图与 <span id> 参考文献锚点
        'merge_anchors': True,      # 把标题前的 <a id> 合并成 h2 自身的 id
        'skip_toc': ('目录',),      # 正文已有目录，侧栏不重复列出
    },
]

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


if __name__ == '__main__':
    for article in ARTICLES:
        render_article(article)
