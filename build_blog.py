from html import escape
from pathlib import Path
import re
from markdown_it import MarkdownIt

root = Path(__file__).resolve().parent
source = (root / 'blog' / 'sgd-noise-geometry.md').read_text(encoding='utf-8')
source = re.sub(r'\n```\s*\n\s*```\s*$', '\n', source)
math = []
def protect(match):
    math.append(match.group())
    return f'MATHPLACEHOLDER{len(math)-1}END'
source = re.sub(r'(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|(?<!\\)\$(?!\$)[^\n$]*?(?<!\\)\$', protect, source)
md = MarkdownIt('commonmark', {'html': False}).enable('table')
tokens = md.parse(source)
headings = []
for i, token in enumerate(tokens):
    if token.type == 'heading_open' and token.tag == 'h2':
        anchor = f'section-{len(headings)+1}'
        token.attrSet('id', anchor)
        headings.append((anchor, tokens[i+1].content))
content = md.renderer.render(tokens, md.options, {})
for i, formula in enumerate(math):
    content = content.replace(f'MATHPLACEHOLDER{i}END', escape(formula))
content = re.sub(r'<table>', '<div class="table-wrap"><table>', content).replace('</table>', '</table></div>')
toc = ''.join(f'<li><a href="#{anchor}">{escape(title)}</a></li>' for anchor,title in headings)
html = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="从随机梯度的稳定性与噪声几何出发，理解优化器如何影响模型的解与参数表示。">
<title>优化器究竟在选择什么？ · 高源的学习笔记</title><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="blog.css">
<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]},svg:{fontCache:'global'}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script></head>
<body id="top"><a class="skip-link" href="#article">跳转到正文</a><header class="site-header"><div class="header-inner"><a class="brand" href="../index.html"><span class="brand-mark" aria-hidden="true">✳</span> 个人主页<span class="brand-slash"> / </span><span class="brand-en">PERSONAL SPACE</span></a><a class="back-link" href="../index.html#blog">← 返回博客</a></div></header>
<div class="article-layout"><aside class="article-toc" aria-label="文章目录"><p>目录 <span>CONTENTS</span></p><ol>''' + toc + '''</ol></aside><main id="article" class="article"><p class="article-kicker">学习笔记 / OPTIMIZATION</p>''' + content + '''<div class="article-end"><a href="../index.html#blog">← 返回博客列表</a><a href="#top">回到顶部 ↑</a></div></main></div><footer class="site-footer"><div class="footer-inner"><p>© 高源 · Personal Homepage</p><p>保持好奇，慢慢积累。</p></div></footer></body></html>'''
out=root/'dist/blog/sgd-noise-geometry.html'
out.parent.mkdir(exist_ok=True)
out.write_text(html,encoding='utf-8')
print(f'Generated {out.name}: {len(headings)} sections, {len(math)} formulas')
