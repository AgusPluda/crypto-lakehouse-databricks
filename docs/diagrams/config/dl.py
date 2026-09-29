import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_excalidraw as g

BG = "#0d0d0d"
LIGHT = "#e6e6f0"
MUTED = "#9a9ab0"
ARROW = "#cfcfe0"

# kind -> (fill, stroke)
PAL = {
    "raw": ("#8ecae6", "#5aa9d0"),
    "bronze": ("#cd7f32", "#a2621f"),
    "silver": ("#c9ced6", "#9aa1ab"),
    "gold": ("#f2c744", "#c9a21f"),
    "ml": ("#ff922b", "#d9730d"),
    "dash": ("#51cf66", "#2f9e44"),
    "agent": ("#9775fa", "#7048e8"),
    "app": ("#ff6b6b", "#e03131"),
    "neutral": ("#2a2a3c", "#4a4a63"),
}
LEGEND = [
    ("raw", "Raw data"), ("bronze", "Bronze"), ("silver", "Silver"), ("gold", "Gold"),
    ("ml", "ML"), ("dash", "Dashboard"), ("agent", "Agente y relacionado"), ("app", "App"),
]


def _txt(x, y, w, label, size, color, align="left"):
    lines = label.count("\n") + 1
    h = lines * size * 1.25
    t = g.text(x, y, w, h, label, size=size, color=color, align=align)
    t["fontFamily"] = 1
    t["verticalAlign"] = "top"
    return t


class D:
    def __init__(self):
        self.els = []
        self.nodes = {}
        self.byid = {}

    def _add(self, *els):
        for e in els:
            self.els.append(e)
            self.byid[e["id"]] = e

    def label(self, x, y, w, label, size=16, color=LIGHT, align="left"):
        self._add(_txt(x, y, w, label, size, color, align))

    def container(self, x, y, w, h, title=None, stroke="#3a3a4e", fill="#13131d", title_color=MUTED, size=16):
        r = g.rect(x, y, w, h, bg=fill, stroke=stroke, dashed=True, roundness=12)
        self._add(r)
        if title:
            self.label(x + 16, y + 10, w - 32, title, size=size, color=title_color)
        return r

    def box(self, key, x, y, w, h, label, kind, font=14, bold_first=False):
        fill, stroke = PAL[kind]
        color = LIGHT if kind == "neutral" else "#111111"
        r = g.rect(x, y, w, h, bg=fill, stroke=stroke, roundness=8)
        lines = label.count("\n") + 1
        th = lines * font * 1.25
        t = _txt(x + 8, y + (h - th) / 2, w - 16, label, font, color, align="center")
        t["containerId"] = r["id"]
        t["verticalAlign"] = "middle"
        r["boundElements"] = [{"id": t["id"], "type": "text"}]
        self._add(r, t)
        self.nodes[key] = r
        return r

    def pt(self, key, side):
        r = self.nodes[key]
        x, y, w, h = r["x"], r["y"], r["width"], r["height"]
        return {"r": (x + w, y + h / 2), "l": (x, y + h / 2),
                "t": (x + w / 2, y), "b": (x + w / 2, y + h)}[side]

    def link(self, a, sa, b, sb, via=(), label=None, dashed=False, color=ARROW, both=False, label_at=None):
        pts_abs = [self.pt(a, sa), *via, self.pt(b, sb)]
        x0, y0 = pts_abs[0]
        rel = [[px - x0, py - y0] for px, py in pts_abs]
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        ra, rb = self.nodes[a], self.nodes[b]
        el = g.arrow(ra["id"], rb["id"], (x0, y0), pts_abs[-1], rel, color=color, dashed=dashed)[0]
        el["width"] = max(xs) - min(xs)
        el["height"] = max(ys) - min(ys)
        el["startBinding"]["gap"] = 0
        el["endBinding"]["gap"] = 0
        el["strokeWidth"] = 2
        if both:
            el["startArrowhead"] = "arrow"
        self._add(el)
        ra["boundElements"].append({"id": el["id"], "type": "arrow"})
        rb["boundElements"].append({"id": el["id"], "type": "arrow"})
        if label:
            if label_at:
                lx, ly = label_at
            else:
                mid = len(pts_abs) // 2
                mx = (pts_abs[mid - 1][0] + pts_abs[mid][0]) / 2
                my = (pts_abs[mid - 1][1] + pts_abs[mid][1]) / 2
                lx, ly = mx - len(label) * 3.4, my - 22
            self.label(lx, ly, len(label) * 7 + 10, label, size=13, color=MUTED)
        return el

    def poly(self, points, color=ARROW, dashed=False, both=False):
        x0, y0 = points[0]
        rel = [[px - x0, py - y0] for px, py in points]
        el = g.arrow(None, None, (x0, y0), points[-1], rel, color=color, dashed=dashed)[0]
        if both:
            el["startArrowhead"] = "arrow"
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        el["width"] = max(xs) - min(xs)
        el["height"] = max(ys) - min(ys)
        self._add(el)

    def legend(self, x, y, extra=None):
        cx = x
        for kind, name in LEGEND:
            fill, stroke = PAL[kind]
            self._add(g.rect(cx, y, 22, 22, bg=fill, stroke=stroke, roundness=4))
            self.label(cx + 30, y + 2, 200, name, size=15, color=LIGHT)
            cx += 30 + len(name) * 8.5 + 30
        if extra:
            self.label(cx, y + 2, 400, extra, size=15, color=MUTED)

    def save(self, path):
        g.save(self.els, path, bg=BG)
