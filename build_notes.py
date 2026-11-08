"""把 blog/john-lee/*.tex 转成 dist/blog/john-lee/*.html，并同步主页的「专题」数据。

用法（在项目根目录 personal-homepage/ 下）：
    python build_notes.py

输入：
    blog/john-lee/meta.json   专题与笔记的顺序、标题、简介
    blog/john-lee/*.tex       每篇笔记的 LaTeX 源文件（从 John Lee 压缩包解压）

输出：
    dist/blog/john-lee/*.html 每篇笔记的阅读页（公式由 MathJax 渲染）
    dist/blog/john-lee/index.html  专题首页
    dist/blog/notes.css       定理框、列表、公式块等样式
    dist/content.js           自动同步 topics 数据块（由标记包裹）

新增笔记：把 main.tex 解压成 blog/john-lee/<slug>.tex，
在 meta.json 的 notes 中加一条，重新运行本脚本即可。
"""

from __future__ import annotations

from html import escape as html_escape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "blog" / "john-lee"
OUT = ROOT / "dist" / "blog" / "john-lee"
DIST = ROOT / "dist"

META = json.loads((SRC / "meta.json").read_text(encoding="utf-8"))
TOPIC = META["topic"]
NOTES = META["notes"]

THM_LABELS = {
    "definition": "定义",
    "theorem": "定理",
    "lemma": "引理",
    "proposition": "命题",
    "corollary": "推论",
    "example": "例",
    "exercise": "练习",
    "remark": "注记",
}
LIST_ENVS = {"enumerate", "itemize", "description"}
MATH_ENVS = ("align", "align*", "gather", "gather*", "equation", "equation*",
             "multline", "multline*", "flalign", "flalign*", "split")

# 需要从正文中删除的排版命令（可能带有 [..] 或 {..} 参数）
DROP_CMDS = [
    "documentclass", "usepackage", "newtheorem", "declaretheoremstyle",
    "declaretheorem", "newcommand", "renewcommand", "providecommand",
    "DeclareMathOperator", "setlist", "setlength", "setcounter",
    "thispagestyle", "maketitle", "tableofcontents", "newpage", "clearpage",
    "label", "vspace", "hspace", "noindent", "smallskip", "medskip",
    "bigskip", "centering", "raggedright", "allowdisplaybreaks", "indent",
    "par", "protect", "footnotesize", "small", "large", "normalsize",
]

SPECIALS = [
    (r"\%", "\x00S0\x00", "%"),
    (r"\_", "\x00S1\x00", "_"),
    (r"\&", "\x00S2\x00", "&amp;"),
    (r"\#", "\x00S3\x00", "#"),
    (r"\$", "\x00S4\x00", "$"),
    (r"\{", "\x00S5\x00", "{"),
    (r"\}", "\x00S6\x00", "}"),
]


def find_braced(s: str, i: int) -> tuple[str, int]:
    """s[i] == '{'，返回 (花括号内的内容, 右括号之后的下标)。"""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def find_bracket(s: str, i: int) -> tuple[str, int]:
    """s[i] == '['，返回 (方括号内的内容, 右括号之后的下标)。"""
    j = i + 1
    depth = 1
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def math_plain(latex: str) -> str:
    """把目录标题里的数学公式转成可读的纯文本。"""
    s = latex.replace("$$", "").replace("\\[", "").replace("\\]", "")
    s = s.replace("\\(", "").replace("\\)", "").strip("$ ")
    s = re.sub(r"\\(?:mathbb|mathrm|mathbf|mathcal|mathfrak|operatorname|text|mathit|mathsf)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\([A-Za-z]+)", r"\1", s)
    return s.replace("{", "").replace("}", "").replace("\\", "").strip()


def parse_macros(preamble: str) -> dict:
    """把 \newcommand 等转换成 MathJax 的 tex.macros 配置。"""
    macros: dict = {}
    pattern = re.compile(r"\\(newcommand|renewcommand|providecommand|DeclareMathOperator)\*?\s*\{")
    for m in pattern.finditer(preamble):
        name_tex, j = find_braced(preamble, m.end() - 1)
        name = name_tex.strip().lstrip("\\")
        if not name:
            continue
        k = j
        while k < len(preamble) and preamble[k] in " \t\r\n":
            k += 1
        nargs = 0
        if k < len(preamble) and preamble[k] == "[":
            arg_text, k = find_bracket(preamble, k)
            digits = re.match(r"\s*(\d+)", arg_text)
            nargs = int(digits.group(1)) if digits else 0
            while k < len(preamble) and preamble[k] in " \t\r\n":
                k += 1
        body = ""
        if k < len(preamble) and preamble[k] == "{":
            body, _ = find_braced(preamble, k)
        if m.group(1) == "DeclareMathOperator":
            body = "\\operatorname{" + body + "}"
        if body:
            macros[name] = [body, nargs] if nargs else body
    # 兼容源文件中引用过的额外宏包命令
    macros.setdefault("mathbbm", ["\\mathbf{#1}", 1])
    macros.setdefault("bm", ["\\boldsymbol{#1}", 1])
    return macros


class Converter:
    def __init__(self, macros: dict):
        self.macros = macros
        self.maths: list[tuple[str, bool]] = []
        self.toc: list[tuple[str, int, str]] = []
        self.warnings: list[str] = []

    def store_math(self, latex: str, display: bool) -> str:
        idx = len(self.maths)
        self.maths.append((latex, display))
        return f"\x00M{idx}\x00"

    def protect_math(self, text: str) -> str:
        """把数学公式替换成占位符，避免后续文本处理破坏 LaTeX。"""
        out: list[str] = []
        i, n = 0, len(text)
        math_envs = [("\\begin{" + e + "}", "\\end{" + e + "}") for e in MATH_ENVS]
        while i < n:
            if text.startswith("$$", i):
                end = text.find("$$", i + 2)
                if end != -1:
                    out.append(self.store_math(text[i:end + 2], True))
                    i = end + 2
                    continue
            elif text.startswith("\\[", i):
                end = text.find("\\]", i + 2)
                if end != -1:
                    out.append(self.store_math(text[i:end + 2], True))
                    i = end + 2
                    continue
            elif text.startswith("\\(", i):
                end = text.find("\\)", i + 2)
                if end != -1:
                    out.append(self.store_math(text[i:end + 2], False))
                    i = end + 2
                    continue
            matched = False
            for begin, end_token in math_envs:
                if text.startswith(begin, i):
                    end = text.find(end_token, i + len(begin))
                    if end != -1:
                        stop = end + len(end_token)
                        out.append(self.store_math("$$" + text[i:stop] + "$$", True))
                        i = stop
                        matched = True
                    break
            if matched:
                continue
            if text[i] == "$" and (i == 0 or text[i - 1] != "\\"):
                j = i + 1
                while j < n:
                    if text[j] == "$" and text[j - 1] != "\\":
                        break
                    j += 1
                if j < n and j > i + 1:
                    out.append(self.store_math(text[i:j + 1], False))
                    i = j + 1
                    continue
            out.append(text[i])
            i += 1
        return "".join(out)

    def esc_segment(self, seg: str) -> str:
        """注释清理 -> 排版命令清理 -> HTML 转义 -> 行内命令转换。"""
        for raw, token, _ in SPECIALS:
            seg = seg.replace(raw, token)
        # 去掉 LaTeX 注释（\% 已被占位符保护）
        seg = re.sub(r"(?<!\\)%[^\n]*", "", seg)
        seg, _ = self.remove_commands(seg)
        seg = html_escape(seg, quote=False)
        seg = self.inline_format(seg)
        for raw, token, value in SPECIALS:
            seg = seg.replace(token, value)
        return seg

    @staticmethod
    def remove_commands(text: str) -> tuple[str, int]:
        pattern = re.compile(r"\\(?:" + "|".join(DROP_CMDS) + r")\*?(?![A-Za-z])")
        out: list[str] = []
        pos = 0
        count = 0
        for m in pattern.finditer(text):
            if m.start() < pos:
                continue
            out.append(text[pos:m.start()])
            j = m.end()
            while j < len(text) and text[j] in " \t":
                j += 1
            while j < len(text) and text[j] == "[":
                _, j = find_bracket(text, j)
                while j < len(text) and text[j] in " \t":
                    j += 1
            while j < len(text) and text[j] == "{":
                _, j = find_braced(text, j)
                while j < len(text) and text[j] in " \t":
                    j += 1
            pos = j
            count += 1
        out.append(text[pos:])
        return "".join(out), count

    @staticmethod
    def replace_braced_cmd(text: str, cmd: str, nargs: int, fn) -> str:
        pattern = re.compile(r"\\" + re.escape(cmd) + r"(?![A-Za-z])\s*\{")
        for _ in range(60):
            m = pattern.search(text)
            if not m:
                break
            j = m.end() - 1
            args = []
            ok = True
            for _ in range(nargs):
                if j >= len(text) or text[j] != "{":
                    ok = False
                    break
                inner, j = find_braced(text, j)
                args.append(inner)
                while j < len(text) and text[j] in " \t":
                    j += 1
            if not ok:
                break
            text = text[:m.start()] + fn(*args) + text[j:]
        return text

    def inline_format(self, s: str) -> str:
        s = self.replace_braced_cmd(s, "texorpdfstring", 2, lambda a, b: a)
        for cmd, open_tag, close_tag in [
            ("textbf", "<strong>", "</strong>"),
            ("emph", "<em>", "</em>"),
            ("textit", "<em>", "</em>"),
            ("underline", '<span class="note-ul">', "</span>"),
            ("text", "", ""),
            ("mathrm", "", ""),
            ("operatorname", "", ""),
        ]:
            s = self.replace_braced_cmd(s, cmd, 1, lambda a, o=open_tag, c=close_tag: o + a + c)
        # 换行、空格与断行命令
        s = re.sub(r"\\\\(?:\[[^\]]*\])?", "<br>", s)
        s = s.replace("\\newline", "<br>")
        s = re.sub(r"\\(?:quad|qquad|,|;|!|:| )(?![A-Za-z])", " ", s)
        s = s.replace("\\-", "").replace("~", " ")
        s = re.sub(r"\\item(?![A-Za-z])", "• ", s)
        leftovers = re.findall(r"\\(?:begin|end|section|subsection|subsubsection|paragraph|newcommand|usepackage|cite|ref|label)\b", s)
        if leftovers:
            self.warnings.extend(sorted(set(leftovers)))
        return s

    def restore_inline(self, s: str) -> str:
        return re.sub(
            r"\x00M(\d+)\x00",
            lambda m: html_escape(self.maths[int(m.group(1))][0], quote=False),
            s,
        )

    def plain(self, s: str) -> str:
        """把含行内公式的片段转成纯文本（用于目录）。"""
        s = self.replace_braced_cmd(s, "texorpdfstring", 2, lambda a, b: a)
        s = re.sub(r"\\(?:textbf|emph|textit|underline|text|mathrm|operatorname)\s*\{([^{}]*)\}", r"\1", s)
        s = re.sub(r"\x00M(\d+)\x00", lambda m: math_plain(self.maths[int(m.group(1))][0]), s)
        s = re.sub(r"\\(?:quad|qquad|,|;|!|:| )(?![A-Za-z])", " ", s)
        s = re.sub(r"\\\\[A-Za-z]*", " ", s)
        s = s.replace("~", " ")
        return re.sub(r"\s+", " ", s).strip()

    def render_text(self, seg: str) -> str:
        seg = self.esc_segment(seg)
        # 展示公式单独成块
        def mark(m):
            idx = int(m.group(1))
            return f"\n\n\x00D{idx}\x00\n\n" if self.maths[idx][1] else m.group(0)
        seg = re.sub(r"\x00M(\d+)\x00", mark, seg)
        chunks = re.split(r"\n\s*\n", seg)
        parts = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            dm = re.fullmatch(r"\x00D(\d+)\x00", chunk)
            if dm:
                latex = html_escape(self.maths[int(dm.group(1))][0], quote=False)
                parts.append(f'<div class="math-block">{latex}</div>')
            else:
                body = self.restore_inline(chunk).strip()
                if body:
                    parts.append(f"<p>{body}</p>")
        return "".join(parts)

    def render_heading(self, kind: str, content: str) -> str:
        self.toc_level = getattr(self, "toc_level", 0) + 1
        anchor = f"section-{self.toc_level}"
        title = self.plain(content)
        level = {"section": 2, "subsection": 3, "subsubsection": 3, "paragraph": 4}[kind]
        self.toc.append((anchor, level, title))
        body = self.restore_inline(self.esc_segment(content)).strip()
        if kind == "paragraph":
            return f'<h4 class="note-para" id="{anchor}">{body}</h4>'
        tag = "h2" if kind == "section" else "h3"
        return f'<{tag} id="{anchor}">{body}</{tag}>'

    def render_env(self, env: str, inner: str) -> str:
        stripped = inner.lstrip()
        lead_ws = inner[:len(inner) - len(stripped)]
        # 环境选项，如 \begin{enumerate}[label=(\roman*)] 或 \begin{definition}[10.1]
        option = ""
        if stripped.startswith("["):
            option, j = find_bracket(stripped, 0)
            inner = stripped[j:]
        else:
            inner = stripped
        if env in LIST_ENVS:
            positions = []
            depth = 0
            scanner = re.compile(r"\\(begin|end)\{[A-Za-z*]+\}|\\item(?![A-Za-z])")
            for m in scanner.finditer(inner):
                token = m.group(0)
                if token.startswith("\\begin"):
                    depth += 1
                elif token.startswith("\\end"):
                    depth = max(0, depth - 1)
                elif depth == 0:
                    positions.append(m.start())
            pieces = [inner[a:b] for a, b in zip(positions, positions[1:] + [len(inner)])]
            lis = []
            for piece in pieces:
                piece = re.sub(r"^\\item(?![A-Za-z])", "", piece, count=1).strip()
                label = ""
                if piece.startswith("["):
                    label, k = find_bracket(piece, 0)
                    piece = piece[k:].strip()
                body = self.render(piece, unwrap=True)
                label_html = ""
                if label:
                    label_html = '<strong class="item-label">' + self.restore_inline(self.esc_segment(label)) + "</strong> "
                lis.append(f"<li>{label_html}{body}</li>")
            tag = "ol" if env == "enumerate" else "ul"
            return f'<{tag} class="note-list">' + "".join(lis) + f"</{tag}>"
        if env in THM_LABELS:
            name_html = ""
            if option:
                name_html = '<span class="thm-name">' + self.restore_inline(self.esc_segment(option)) + "</span>"
            body = self.render(inner)
            return (f'<div class="thm thm-{env}"><div class="thm-head">'
                    f'<span class="thm-kind">{THM_LABELS[env]}</span>{name_html}</div>'
                    f'<div class="thm-body">{body}</div></div>')
        if env in {"center", "flushleft", "flushright", "quote", "proof"}:
            return self.render(inner)
        self.warnings.append("未知环境: " + env)
        return self.render(inner)

    def find_env_end(self, text: str, start: int, env: str) -> tuple[int, int]:
        pattern = re.compile(r"\\(begin|end)\{" + re.escape(env) + r"\}")
        depth = 1
        for m in pattern.finditer(text, start):
            if m.group(1) == "begin":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    return m.start(), m.end()
        return len(text), len(text)

    def render(self, text: str, unwrap: bool = False) -> str:
        token = re.compile(r"\\begin\{([A-Za-z*]+)\}|\\(section|subsection|subsubsection|paragraph)\*?\s*\{")
        parts: list[str] = []
        pos = 0
        while True:
            m = token.search(text, pos)
            if not m:
                break
            parts.append(self.render_text(text[pos:m.start()]))
            if m.group(1):
                env = m.group(1)
                end_start, end_stop = self.find_env_end(text, m.end(), env)
                parts.append(self.render_env(env, text[m.end():end_start]))
                pos = end_stop
            else:
                content, after = find_braced(text, m.end() - 1)
                parts.append(self.render_heading(m.group(2), content))
                pos = after
        parts.append(self.render_text(text[pos:]))
        html = "".join(parts)
        if unwrap:
            html = html.strip()
            if (html.startswith("<p>") and html.endswith("</p>")
                    and html.count("<p>") == 1 and html.count("</p>") == 1):
                return html[3:-4]
        return html

    def convert(self, tex: str) -> tuple[str, list[tuple[str, int, str]], list[str]]:
        self.maths = []
        self.toc = []
        self.warnings = []
        self.toc_level = 0
        body = tex
        start = body.find("\\begin{document}")
        if start != -1:
            body = body[start + len("\\begin{document}"):]
        end = body.find("\\end{document}")
        if end != -1:
            body = body[:end]
        body = self.protect_math(body)
        html = self.render(body)
        return html, self.toc, sorted(set(self.warnings))


def mathjax_config(macros: dict) -> str:
    config = {
        "tex": {
            "inlineMath": [["$", "$"], ["\\(", "\\)"]],
            "displayMath": [["$$", "$$"], ["\\[", "\\]"]],
            "macros": macros,
        },
        "svg": {"fontCache": "global"},
    }
    return json.dumps(config, ensure_ascii=False, separators=(",", ":"))


def shell(*, title: str, description: str, kicker: str, toc_html: str,
          content: str, macros: dict, back_label: str = "← 返回学习笔记",
          back_href: str = "../../index.html#blog") -> str:
    head = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<meta name="description" content="{html_escape(description, quote=True)}">\n'
        f'<title>{html_escape(title)} · John Lee 专题 · 高源的学习笔记</title>'
        '<link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml">'
        '<link rel="stylesheet" href="../../styles.css">'
        '<link rel="stylesheet" href="../blog.css">'
        '<link rel="stylesheet" href="../notes.css">\n'
        f'<script>window.MathJax={mathjax_config(macros)};</script>\n'
        '<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>'
        '</head>\n<body id="top">'
        '<a class="skip-link" href="#article">跳转到正文</a>'
        '<header class="site-header"><div class="header-inner">'
        '<a class="brand" href="../../index.html"><span class="brand-mark" aria-hidden="true">✳</span> 个人主页'
        '<span class="brand-slash"> / </span><span class="brand-en">PERSONAL SPACE</span></a>'
        f'<a class="back-link" href="{back_href}">{back_label}</a></div></header>\n'
        '<div class="article-layout">'
        '<aside class="article-toc" aria-label="文章目录"><p>目录 <span>CONTENTS</span></p>'
        f'<ol>{toc_html}</ol></aside>'
        f'<main id="article" class="article"><p class="article-kicker">{html_escape(kicker)}</p>'
        f'<h1>{html_escape(title)}</h1>'
        f'<p class="article-lead">{html_escape(description)}</p>'
        f'{content}'
        '<div class="article-end"><a href="../../index.html#blog">← 返回学习笔记</a>'
        '<a href="#top">回到顶部 ↑</a></div></main></div>\n'
        '<footer class="site-footer"><div class="footer-inner"><p>© 高源 · Personal Homepage</p>'
        '<p>保持好奇，慢慢积累。</p></div></footer></body></html>\n'
    )
    return head


def toc_html(entries: list[tuple[str, int, str]]) -> str:
    return "".join(
        f'<li class="toc-l{lv}"><a href="#{anchor}">{html_escape(title, quote=True)}</a></li>'
        for anchor, lv, title in entries
    )


NOTES_CSS = """
/* 由 build_notes.py 生成：John Lee 专题的定理框、列表与公式样式 */
.article-lead{font-size:13px;color:#7b887f;line-height:1.9;margin:-22px 0 34px;padding-bottom:24px;border-bottom:1px solid var(--line)}
.article-source{font-size:12px;color:#909a91;background:#f3f6f2;border-left:2px solid #cfdccf;padding:12px 16px;border-radius:0 4px 4px 0}
.article-toc ol{max-height:68vh;overflow-y:auto;scrollbar-width:thin}
.article-toc li.toc-l3{padding-left:30px;font-size:11px;color:#95a096}
.article-toc li.toc-l4{padding-left:44px;font-size:10px;color:#a4aea5}
.article-toc li.toc-l4 a{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.article h4.note-para{font-family:var(--sans);font-size:14px;font-weight:650;color:#37523f;margin:32px 0 12px;letter-spacing:.3px;scroll-margin-top:100px}
.article h4.note-para:before{content:"";display:inline-block;width:5px;height:5px;border-radius:50%;background:#8dab91;vertical-align:middle;margin-right:9px}
.math-block{overflow-x:auto;overflow-y:hidden;margin:22px 0;padding:2px 0}
.math-block mjx-container[display="true"]{margin:.4em 0!important}
.thm{margin:26px 0;padding:18px 22px 6px;border:1px solid #e2e9e2;border-left:3px solid #8dab91;border-radius:4px;background:#f7faf7}
.thm-head{display:flex;align-items:baseline;flex-wrap:wrap;gap:10px;margin-bottom:10px}
.thm-kind{font-size:11px;font-weight:650;letter-spacing:1px;color:#4c7257;background:#e7f1e8;border-radius:3px;padding:2px 8px}
.thm-name{font-size:12px;color:#6d7f70;line-height:1.7}
.thm-body>p:last-child{margin-bottom:14px}
.thm-body>.math-block:last-child{margin-bottom:14px}
.thm-theorem,.thm-proposition{border-left-color:#6f8fbd;background:#f7f9fd}
.thm-theorem .thm-kind,.thm-proposition .thm-kind{color:#4a679b;background:#e6edf8}
.thm-example,.thm-exercise{border-left-color:#c5a86d;background:#fbf9f3}
.thm-example .thm-kind,.thm-exercise .thm-kind{color:#8a7440;background:#f2ead7}
.thm-remark{border-left-color:#b9b0c9;background:#faf9fc}
.thm-remark .thm-kind{color:#776b91;background:#ede9f4}
.note-list{padding-left:22px!important;margin:12px 0 20px!important}
.note-list li{margin:7px 0;line-height:1.95}
.item-label{color:#3d5a45;font-weight:650}
.note-ul{text-decoration:underline;text-underline-offset:3px}
.note-series{list-style:none;margin:30px 0 0;padding:0;border-top:1px solid var(--line)}
.note-series li{border-bottom:1px solid var(--line)}
.note-series a{display:flex;align-items:baseline;gap:18px;padding:17px 4px;transition:background .2s}
.note-series a:hover{background:var(--blue-soft)}
.note-series .series-no{font-family:Georgia,serif;font-style:italic;font-size:12px;color:#a4b0a2;width:26px;flex:none}
.note-series .series-main{display:flex;flex-direction:column;gap:5px;min-width:0}
.note-series strong{font-family:var(--serif);font-size:17px;font-weight:600;color:#2f4436}
.note-series small{font-size:11px;line-height:1.8;color:#8b958d}
.note-series .series-arrow{margin-left:auto;color:var(--blue);white-space:nowrap;font-size:12px}
.series-nav{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px 20px;border-top:1px solid var(--line);margin-top:44px;padding-top:22px;font-size:12px;color:var(--blue)}
.series-nav span{color:#a2aca2}
@media(max-width:600px){.thm{padding:15px 16px 4px}.article h4.note-para{font-size:13px}.note-series strong{font-size:15px}}
"""


def sync_content_js() -> None:
    """用 meta.json 同步 content.js 中由标记包裹的 topics 数据块。"""
    path = DIST / "content.js"
    source = path.read_text(encoding="utf-8")
    topics = [{
        "title": TOPIC["title"],
        "english": TOPIC["english"],
        "description": TOPIC["description"],
        "url": "blog/john-lee/index.html",
        "notes": [{
            "title": note["title"],
            "description": note["description"],
            "url": f'blog/john-lee/{note["slug"]}.html',
        } for note in NOTES],
    }]
    payload = json.dumps(topics, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    begin = "  // --- BEGIN 专题：由 build_notes.py 生成，请勿手工改动 ---\n"
    end = "  // --- END 专题 ---\n"
    block = begin + "  topics: " + payload + ",\n" + end
    if begin in source and end in source:
        start = source.index(begin)
        stop = source.index(end) + len(end)
        source = source[:start] + block + source[stop:]
    else:
        marker = "  publications: []"
        if marker not in source:
            raise RuntimeError("content.js 中找不到插入位置 publications: []")
        source = source.replace(marker, block + marker, 1)
    path.write_text(source, encoding="utf-8")
    print(f"Synced {path.name}: topics 数据块（{len(NOTES)} 篇笔记）")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (DIST / "blog" / "notes.css").write_text(NOTES_CSS.lstrip(), encoding="utf-8")

    total_warnings: list[str] = []
    for index, note in enumerate(NOTES, start=1):
        tex_path = SRC / f'{note["slug"]}.tex'
        if not tex_path.exists():
            raise FileNotFoundError(f"缺少笔记源文件：{tex_path}")
        tex = tex_path.read_text(encoding="utf-8")
        preamble = tex.split("\\begin{document}", 1)[0]
        macros = parse_macros(preamble)
        conv = Converter(macros)
        content, entries, warns = conv.convert(tex)
        total_warnings.extend(f'{note["slug"]}: {w}' for w in warns)

        prev_note = NOTES[index - 2] if index > 1 else None
        next_note = NOTES[index] if index < len(NOTES) else None
        nav = ['<div class="series-nav">']
        if prev_note:
            nav.append(f'<a href="{prev_note["slug"]}.html">← 上一篇：{html_escape(prev_note["title"])}</a>')
        else:
            nav.append('<span>已是第一篇</span>')
        nav.append(f'<a href="index.html">专题目录 · {html_escape(TOPIC["title"])}</a>')
        if next_note:
            nav.append(f'<a href="{next_note["slug"]}.html">下一篇：{html_escape(next_note["title"])} →</a>')
        else:
            nav.append('<span>已是最后一篇</span>')
        nav.append('</div>')

        kicker = f'学习笔记 / {TOPIC["kicker"]} · {index:02d} / {len(NOTES):02d}'
        page = shell(
            title=note["title"],
            description=note["description"],
            kicker=kicker,
            toc_html=toc_html(entries),
            content=content + "".join(nav),
            macros=macros,
        )
        (OUT / f'{note["slug"]}.html').write_text(page, encoding="utf-8")
        formulas = sum(1 for _, _ in conv.maths)
        print(f'Generated {note["slug"]}.html: {len(entries)} headings, {formulas} formulas, {len(macros)} macros')

    # 专题首页
    series = "".join(
        f'<li><a href="{note["slug"]}.html"><span class="series-no">{i:02d}</span>'
        f'<span class="series-main"><strong>{html_escape(note["title"])}</strong>'
        f'<small>{html_escape(note["description"])}</small></span>'
        f'<span class="series-arrow">阅读 →</span></a></li>'
        for i, note in enumerate(NOTES, start=1)
    )
    intro = (
        f'<p class="article-source">参考教材：{html_escape(TOPIC["source"])}。'
        f'以下 {len(NOTES)} 篇笔记按章节顺序排列，公式由 MathJax 渲染，'
        f'点击标题即可进入对应笔记。</p>'
        f'<ol class="note-series">{series}</ol>'
    )
    index_page = shell(
        title=f'{TOPIC["title"]} · 光滑流形读书笔记',
        description=TOPIC["description"],
        kicker=f'学习笔记 / {TOPIC["kicker"]} · 专题目录',
        toc_html="".join(
            f'<li><a href="{note["slug"]}.html">{html_escape(note["title"], quote=True)}</a></li>'
            for note in NOTES
        ),
        content=intro,
        macros={"mathbbm": ["\\mathbf{#1}", 1]},
    )
    (OUT / "index.html").write_text(index_page, encoding="utf-8")
    print(f'Generated index.html: 专题首页（{len(NOTES)} 篇）')

    sync_content_js()
    if total_warnings:
        print("\n需要注意的残留 LaTeX 命令 / 环境：")
        for w in total_warnings[:30]:
            print("  -", w)
    else:
        print("\n检查通过：正文未发现残留的 LaTeX 结构命令。")


if __name__ == "__main__":
    main()
