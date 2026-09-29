import json
import random

random.seed(42)
_id_counter = 0


def new_id(prefix):
    global _id_counter
    _id_counter += 1
    return f"{prefix}-{_id_counter}"


def seed():
    return random.randint(1, 2_000_000_000)


def rect(x, y, w, h, bg="#ffffff", stroke="#1e1e1e", dashed=False, rid=None, roundness=8):
    rid = rid or new_id("rect")
    return {
        "id": rid, "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg, "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "dashed" if dashed else "solid", "roughness": 1,
        "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 3} if roundness else None,
        "seed": seed(), "version": 1, "versionNonce": seed(), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
    }


def text(x, y, w, h, label, size=16, color="#1e1e1e", align="center", tid=None, bold_container=None):
    tid = tid or new_id("text")
    el = {
        "id": tid, "type": "text", "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": color, "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": seed(), "version": 1, "versionNonce": seed(), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
        "text": label, "fontSize": size, "fontFamily": 1, "textAlign": align,
        "verticalAlign": "middle", "containerId": bold_container, "originalText": label,
        "lineHeight": 1.25, "baseline": int(size * 0.9),
    }
    return el


def node(x, y, w, h, label, bg="#ffffff", font=16):
    """A rectangle with centered bound text. Returns (rect_el, text_el)."""
    rid = new_id("rect")
    tid = new_id("text")
    r = rect(x, y, w, h, bg=bg, rid=rid)
    r["boundElements"] = [{"id": tid, "type": "text"}]
    t = text(x + 10, y + h / 2 - font * 0.7, w - 20, font * 1.4, label, size=font,
              tid=tid, bold_container=rid)
    return r, t


def arrow(start_id, end_id, start_xy, end_xy, points, label=None, color="#1e1e1e", dashed=False):
    aid = new_id("arrow")
    a = {
        "id": aid, "type": "arrow", "x": start_xy[0], "y": start_xy[1],
        "width": abs(end_xy[0] - start_xy[0]), "height": abs(end_xy[1] - start_xy[1]),
        "angle": 0, "strokeColor": color, "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "dashed" if dashed else "solid", "roughness": 1,
        "opacity": 100, "groupIds": [], "frameId": None, "roundness": {"type": 2},
        "seed": seed(), "version": 1, "versionNonce": seed(), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
        "points": points, "lastCommittedPoint": None,
        "startBinding": {"elementId": start_id, "focus": 0, "gap": 6} if start_id else None,
        "endBinding": {"elementId": end_id, "focus": 0, "gap": 6} if end_id else None,
        "startArrowhead": None, "endArrowhead": "arrow",
    }
    elems = [a]
    if label:
        lx = start_xy[0] + (end_xy[0] - start_xy[0]) / 2 - len(label) * 3
        ly = start_xy[1] + (end_xy[1] - start_xy[1]) / 2 - 22
        elems.append(text(lx, ly, len(label) * 7 + 10, 18, label, size=13, color="#555555"))
    return elems


def save(elements, path, bg="#0d0d0d"):
    doc = {
        "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": 20, "viewBackgroundColor": bg},
        "files": {},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    print(f"wrote {len(elements)} elements to {path}")
