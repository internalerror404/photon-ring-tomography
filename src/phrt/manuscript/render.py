"""Minimal Markdown -> HTML renderer for the manuscript.

Deliberately small: it handles exactly the constructs the manuscript builder
emits -- ATX headings, paragraphs, pipe tables, fenced code, bullet and ordered
lists, blockquotes, horizontal rules, and inline emphasis/code/links. A general
Markdown implementation is not available in the pinned environment and vendoring
one would add an unpinned dependency to a provenance-tracked tree for the sake
of a document render.

Anything it does not recognise is emitted as a paragraph rather than dropped, so
a construct the builder starts using shows up as visibly wrong text instead of
silently disappearing from the paper.
"""
from __future__ import annotations

import html
import re

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:-]*-[\s|:-]*\|?\s*$")
BULLET = re.compile(r"^\s*[-*]\s+")
ORDERED = re.compile(r"^\s*\d+\.\s+")


def _inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = _INLINE_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = _ITALIC.sub(lambda m: f"<em>{m.group(1)}</em>", out)
    out = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    return out


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _alignments(sep: str) -> list[str]:
    out = []
    for c in _split_row(sep):
        left, right = c.startswith(":"), c.endswith(":")
        out.append("center" if left and right else
                   "right" if right else "left")
    return out


def to_html(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]

        if line.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue

        if not line.strip():
            i += 1
            continue

        if re.match(r"^-{3,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # pipe table: header row followed by a separator row
        if "|" in line and i + 1 < n and _TABLE_SEP.match(lines[i + 1]):
            header = _split_row(line)
            align = _alignments(lines[i + 1])
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_split_row(lines[i]))
                i += 1
            th = "".join(f'<th style="text-align:{a}">{_inline(c)}</th>'
                         for c, a in zip(header, align + ["left"] * len(header)))
            body = []
            for r in rows:
                tds = "".join(f'<td style="text-align:{a}">{_inline(c)}</td>'
                              for c, a in zip(r, align + ["left"] * len(r)))
                body.append(f"<tr>{tds}</tr>")
            out.append('<div class="tablewrap"><table><thead><tr>' + th
                       + "</tr></thead><tbody>" + "".join(body)
                       + "</tbody></table></div>")
            continue

        # Lists, with continuation lines folded into the item they belong to.
        # Source markdown is hard-wrapped, so a wrapped item would otherwise
        # break out of the list and render as a stray paragraph.
        marker = ("ul", BULLET) if BULLET.match(line) else \
                 ("ol", ORDERED) if ORDERED.match(line) else None
        if marker:
            tag, pat = marker
            items: list[str] = []
            while i < n:
                if pat.match(lines[i]):
                    items.append(pat.sub("", lines[i]).strip())
                elif (items and lines[i].strip() and lines[i][:1] in " \t"
                      and not BULLET.match(lines[i])
                      and not ORDERED.match(lines[i])):
                    items[-1] += " " + lines[i].strip()
                else:
                    break
                i += 1
            out.append(f"<{tag}>"
                       + "".join(f"<li>{_inline(x)}</li>" for x in items)
                       + f"</{tag}>")
            continue

        if line.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>" + _inline(" ".join(buf)) + "</blockquote>")
            continue

        buf = []
        while i < n and lines[i].strip() and not lines[i].startswith(("#", "```", ">")) \
                and not BULLET.match(lines[i]) and not ORDERED.match(lines[i]) \
                and not ("|" in lines[i] and i + 1 < n and _TABLE_SEP.match(lines[i + 1])):
            buf.append(lines[i])
            i += 1
        if buf:
            out.append("<p>" + _inline(" ".join(x.strip() for x in buf)) + "</p>")
        else:
            i += 1
    return "\n".join(out)


CSS = """
:root{--ink:#14161a;--muted:#5b6270;--rule:#d8dce4;--bg:#ffffff;--accent:#1c3f94;
--code-bg:#f3f4f7;--th-bg:#f7f8fa;}
@media (prefers-color-scheme: dark){:root{--ink:#e6e8ec;--muted:#a3aab8;
--rule:#333844;--bg:#101216;--accent:#8fb0ff;--code-bg:#1a1d23;--th-bg:#171a20;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.62 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;}
main{max-width:52rem;margin:0 auto;padding:3.5rem 1.5rem 6rem;}
h1{font-size:1.9rem;line-height:1.25;margin:0 0 .4rem;letter-spacing:-.01em}
h2{font-size:1.32rem;margin:2.6rem 0 .7rem;padding-bottom:.3rem;
border-bottom:1px solid var(--rule);letter-spacing:-.005em}
h3{font-size:1.08rem;margin:1.8rem 0 .5rem}
h4{font-size:.98rem;margin:1.3rem 0 .4rem;color:var(--muted)}
p{margin:0 0 .85rem}
ul,ol{margin:0 0 .95rem;padding-left:1.4rem}
li{margin:.24rem 0}
code{font:0.86em/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
background:var(--code-bg);padding:.1em .32em;border-radius:3px}
pre{background:var(--code-bg);padding:.85rem 1rem;border-radius:6px;
overflow-x:auto;border:1px solid var(--rule)}
pre code{background:none;padding:0;font-size:.84rem}
.tablewrap{overflow-x:auto;margin:0 0 1.1rem}
table{border-collapse:collapse;width:100%;font-size:.84rem;
font-family:ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif}
th,td{border-bottom:1px solid var(--rule);padding:.36rem .55rem;vertical-align:top}
th{background:var(--th-bg);font-weight:600;white-space:nowrap}
tbody tr:last-child td{border-bottom:1px solid var(--rule)}
blockquote{margin:0 0 1rem;padding:.1rem 0 .1rem 1rem;border-left:3px solid var(--rule);
color:var(--muted)}
hr{border:0;border-top:1px solid var(--rule);margin:2rem 0}
a{color:var(--accent)}
@media print{body{font-size:10.5pt}main{max-width:none;padding:0}
h2{page-break-after:avoid}table{page-break-inside:avoid}
.tablewrap{overflow:visible}}
"""


def page(title: str, md: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body><main>{to_html(md)}</main></body></html>")
