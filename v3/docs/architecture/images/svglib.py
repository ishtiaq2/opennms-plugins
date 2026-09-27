"""A very small SVG toolkit for the architecture diagrams (standard library only).

Coordinates are absolute pixels. Text in a line may contain `code` spans (rendered in a monospace
font). Every drawing gets a white background so it stays readable on dark themes. Boxes and group
labels are checked against a deliberately wide estimate of the text width (DejaVu Sans, the widest
common fallback font), and problems are collected in Svg.warnings.
"""
from __future__ import annotations

from html import escape

FONT = "Helvetica, Arial, 'DejaVu Sans', sans-serif"
MONO = "Menlo, Consolas, 'DejaVu Sans Mono', monospace"

# fill, stroke, text colour per layer
STYLES = {
    "host": ("#f3f4f6", "#6b7280", "#111827"),
    "container": ("#f8fafc", "#64748b", "#0f172a"),
    "jvm": ("#ffffff", "#0f172a", "#0f172a"),
    "daemon": ("#ecfdf5", "#059669", "#064e3b"),
    "jetty": ("#fff7ed", "#ea580c", "#7c2d12"),
    "webapp": ("#ffedd5", "#c2410c", "#7c2d12"),
    "karaf": ("#f5f3ff", "#7c3aed", "#4c1d95"),
    "bundle": ("#ede9fe", "#7c3aed", "#4c1d95"),
    "plugin": ("#dbeafe", "#2563eb", "#1e3a8a"),
    "data": ("#fefce8", "#ca8a04", "#713f12"),
    "assets": ("#fce7f3", "#db2777", "#831843"),
    "note": ("#ffffff", "#cbd5e1", "#334155"),
    "white": ("#ffffff", "#94a3b8", "#0f172a"),
    "grey": ("#f1f5f9", "#94a3b8", "#334155"),
    "dark": ("#1e293b", "#0f172a", "#ffffff"),
}

ARROW = {
    "default": "#334155",
    "http": "#ea580c",
    "osgi": "#7c3aed",
    "plugin": "#2563eb",
    "assets": "#db2777",
    "data": "#a16207",
    "daemon": "#059669",
    "grey": "#94a3b8",
}

SEQ_COLOR = "#2563eb"   # numbered circles that give an order of events


def text_width(s: str, size: float, mono: bool = False, bold: bool = False) -> float:
    """Generous width estimate; `code` spans are measured as monospace at 93 % size."""
    w = 0.0
    for i, part in enumerate(s.split("`")):
        if not part:
            continue
        if mono:
            w += len(part) * size * 0.61
        elif i % 2 == 1:
            w += len(part) * size * 0.93 * 0.61
        else:
            w += len(part) * size * (0.64 if bold else 0.60)
    return w


class Svg:
    def __init__(self, width: int, height: int, title: str, subtitle: str = ""):
        self.w, self.h = width, height
        self.body: list[str] = []
        self.markers: dict[str, str] = {}
        self.title = title
        self.subtitle = subtitle
        self.warnings: list[str] = []

    def top(self) -> float:
        """y below the title block."""
        n = len(self.subtitle.split("\n")) if self.subtitle else 0
        return 58 + 19 * n

    def _check(self, what: str, needed: float, available: float, tolerance: float = 1.04) -> None:
        # widths: the estimate is generous, DejaVu Sans still fits a few per cent over it
        if needed > available * tolerance + 0.5:
            self.warnings.append(f"{what}: needs {needed:.0f}px, has {available:.0f}px")

    # -- primitives -------------------------------------------------------------------------------
    def add(self, s: str) -> None:
        self.body.append(s)

    def rect(self, x, y, w, h, fill, stroke, rx=10, sw=1.6, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{o} '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def line(self, x1, y1, x2, y2, color="#94a3b8", sw=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=13, weight="normal", anchor="start", color="#0f172a", mono=False,
             italic=False):
        """One line; `code` spans switch to the monospace font."""
        fam = MONO if mono else FONT
        style = ' font-style="italic"' if italic else ""
        parts = s.split("`")
        if len(parts) == 1:
            inner = escape(s)
        else:
            spans = []
            for i, p in enumerate(parts):
                if not p:
                    continue
                if i % 2 == 1:  # inside backticks; keep runs of spaces
                    p = p.replace(" ", "\u00a0")
                    spans.append(f'<tspan font-family="{MONO}" font-size="{size * 0.93:.1f}">{escape(p)}</tspan>')
                else:
                    spans.append(f"<tspan>{escape(p)}</tspan>")
            inner = "".join(spans)
        self.add(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
                 f'text-anchor="{anchor}" fill="{color}"{style}>{inner}</text>')

    def lines(self, x, y, lines, size=13, color="#0f172a", mono=False, anchor="start", lh=None,
              weight="normal", italic=False):
        lh = lh or size * 1.38
        for i, s in enumerate(lines):
            self.text(x, y + i * lh, s, size=size, color=color, mono=mono, anchor=anchor, weight=weight,
                      italic=italic)
        return y + len(lines) * lh

    # -- composed shapes --------------------------------------------------------------------------
    def box(self, x, y, w, h, style, title=None, lines=(), title_size=14, size=13, center=False,
            mono=False, badge=None, rx=9, sw=1.6, dash=None, title_mono=False, seq=None, italic=False):
        fill, stroke, tcol = STYLES[style]
        self.rect(x, y, w, h, fill, stroke, rx=rx, sw=sw, dash=dash)
        cx = x + w / 2
        pad = 8 if center else 12
        avail = w - 2 * pad
        ty = y + 8 + title_size
        name = (title or (lines[0] if lines else "")).replace("`", "")[:40]
        if title:
            indent = 12 if seq is not None and not center else 0
            self._check(f"box '{name}' title", text_width(title, title_size, title_mono, bold=True) + indent, avail)
            if center:
                self.text(cx, ty, title, size=title_size, weight="bold", anchor="middle", color=tcol, mono=title_mono)
            else:
                self.text(x + pad + indent, ty, title, size=title_size, weight="bold", color=tcol, mono=title_mono)
            ty += size * 1.45
        else:
            ty = y + 8 + size
        for s in lines:
            self._check(f"box '{name}' line '{s[:30]}'", text_width(s, size, mono), avail)
        if lines:
            if center:
                self.lines(cx, ty, lines, size=size, color=tcol, anchor="middle", mono=mono, italic=italic)
            else:
                self.lines(x + pad, ty, lines, size=size, color=tcol, mono=mono, italic=italic)
            last = ty + (len(lines) - 1) * size * 1.38
        else:
            last = ty - size * 1.45
        self._check(f"box '{name}' height", last + size * 0.25 + 2 - y, h, tolerance=1.0)
        if badge is not None:
            self.badge(x + w - 4, y + 4, badge)
        if seq is not None:
            self.badge(x + 4, y + 4, seq, color=SEQ_COLOR)

    def group(self, x, y, w, h, style, label, sub=None, label_size=14, badge=None, dash=None, sw=1.8,
              rx=12, seq=None):
        fill, stroke, tcol = STYLES[style]
        self.rect(x, y, w, h, fill, stroke, rx=rx, sw=sw, dash=dash)
        lx = x + (26 if seq is not None else 14)
        self._check(f"group '{label[:30]}' label", text_width(label, label_size, bold=True),
                    w - (lx - x) - (22 if badge is not None else 10))
        self.text(lx, y + 8 + label_size, label, size=label_size, weight="bold", color=tcol)
        if sub:
            self._check(f"group '{label[:30]}' sub", text_width(sub, 12.5), w - (lx - x) - 10)
            self.text(lx, y + 12 + label_size + 14, sub, size=12.5, color=tcol)
        if badge is not None:
            self.badge(x + w - 4, y + 4, badge)
        if seq is not None:
            self.badge(x + 4, y + 4, seq, color=SEQ_COLOR)

    def badge(self, x, y, n, color="#111827", r=12):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="#ffffff" stroke-width="2"/>')
        self.text(x, y + 4.5, str(n), size=12.5, weight="bold", anchor="middle", color="#ffffff")

    def seq(self, x, y, n):
        """A blue numbered circle: the order of events in the text."""
        self.badge(x, y, n, color=SEQ_COLOR, r=11)

    def _marker(self, color: str) -> str:
        mid = "a" + color.lstrip("#")
        if mid not in self.markers:
            self.markers[mid] = (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                                 f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
                                 f'fill="{color}"/></marker>')
        return mid

    def arrow(self, pts, kind="default", label=None, lx=None, ly=None, dash=None, sw=1.8, start=False,
              end=True, label_size=12, label_anchor="middle", label_color=None, color=None):
        color = color or ARROW.get(kind, kind)
        mid = self._marker(color)
        d = "M" + " L".join(f"{px},{py}" for px, py in pts)
        ms = f' marker-start="url(#{mid})"' if start else ""
        me = f' marker-end="url(#{mid})"' if end else ""
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{dd}{ms}{me} '
                 f'stroke-linejoin="round"/>')
        if label:
            if lx is None:
                (x1, y1), (x2, y2) = pts[0], pts[-1]
                lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 6
            self.label(lx, ly, label, size=label_size, anchor=label_anchor, color=label_color or color)

    def label(self, x, y, s, size=12, anchor="middle", color="#334155", bg="#ffffff"):
        """A small text on a white pill, for arrow labels. '\n' separates lines."""
        lines = s.split("\n")
        widest = max(text_width(line, size) for line in lines)
        h = len(lines) * size * 1.3 + 6
        if anchor == "middle":
            x0 = x - widest / 2 - 5
        elif anchor == "start":
            x0 = x - 5
        else:
            x0 = x - widest - 5
        self.rect(round(x0, 1), round(y - size - 2, 1), round(widest + 10, 1), round(h, 1), bg, bg, rx=5, sw=0)
        for i, line in enumerate(lines):
            self.text(x, y + i * size * 1.3, line, size=size, anchor=anchor, color=color)

    def legend(self, x, y, items, size=12.5):
        """items: [(style, text)]"""
        cx = x
        for style, s in items:
            fill, stroke, _ = STYLES[style]
            self.rect(cx, y - 11, 16, 14, fill, stroke, rx=3, sw=1.4)
            self.text(cx + 22, y, s, size=size, color="#334155")
            cx += 22 + text_width(s, size) + 18
        self._check("legend", cx - 18, self.w - 16)

    # -- sequence diagrams ------------------------------------------------------------------------
    def lanes(self, x0, y, width, bottom, lanes, head_h=58, size=13):
        """Column headers plus dashed lifelines; lanes = [(key, title, lines, style)].
        Returns {key: centre x}."""
        n = len(lanes)
        col = width / n
        xs = {}
        for i, (key, title, sub, style) in enumerate(lanes):
            bx = x0 + i * col + 5
            self.box(round(bx, 1), y, round(col - 10, 1), head_h, style, title, sub, title_size=13.5, size=12,
                     center=True)
            cx = round(x0 + i * col + col / 2, 1)
            xs[key] = cx
            self.line(cx, y + head_h, cx, bottom, color="#cbd5e1", sw=1.6, dash="5 5")
        return xs

    def msg(self, xs, a, b, y, text, kind="default", n=None, dash=None, size=12.5, above=True, at="middle"):
        """A message between two lifelines, with its label above the arrow ("start": next to the sender)."""
        x1, x2 = xs[a], xs[b]
        off = 7 if x2 > x1 else -7
        self.arrow([(x1 + off / 3, y), (x2 - off, y)], kind, dash=dash)
        color = ARROW.get(kind, kind) if kind != "default" else "#0f172a"
        if above:
            if at == "start":  # next to the left-hand lifeline, reading to the right
                self.label(min(x1, x2) + 12, y - 10, text, size=size, color=color, anchor="start")
            else:
                self.label((x1 + x2) / 2, y - 10, text, size=size, color=color)
        if n is not None:
            self.seq(x1 + (14 if x2 > x1 else -14), y - 13, n)

    # -- output -----------------------------------------------------------------------------------
    def render(self) -> str:
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t d">',
                f'<title id="t">{escape(self.title)}</title>',
                f'<desc id="d">{escape(self.subtitle.replace(chr(10), " ") or self.title)}</desc>',
                "<defs>" + "".join(self.markers.values()) + "</defs>",
                f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="14" fill="#ffffff" '
                f'stroke="#e2e8f0"/>']
        head.append(f'<text x="24" y="36" font-family="{FONT}" font-size="21" font-weight="bold" '
                    f'fill="#0f172a">{escape(self.title)}</text>')
        self._check("title", text_width(self.title, 21, bold=True), self.w - 48)
        for i, sub in enumerate(self.subtitle.split("\n") if self.subtitle else []):
            self._check(f"subtitle line {i + 1}", text_width(sub, 14), self.w - 48)
            head.append(f'<text x="24" y="{59 + 19 * i}" font-family="{FONT}" font-size="14" fill="#475569">'
                        f'{escape(sub)}</text>')
        return "\n".join(head + self.body + ["</svg>"]) + "\n"
