"""
mermaid_diagram.py – Rendert Mermaid-Diagramme aus Markdown-Dateien als
moderne, professionelle PNGs im Darkmode (ein Bild pro Diagramm).

Nur Standardbibliothek + Pillow noetig.

Verwendung:
    python mermaid_diagram.py <datei.md> [weitere.md ...] [--out ORDNER]
    python mermaid_diagram.py <ordner> [--out ORDNER]

Unterstuetzte Diagrammtypen:
flowchart/graph, erDiagram, sequenceDiagram, classDiagram,
stateDiagram(-v2), mindmap, timeline, kanban, pie, gitGraph, gantt,
quadrantChart, xychart(-beta), journey.
Andere Mermaid-Diagrammtypen werden uebersprungen.
"""

import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INK = '#8b9bb0'          # Standard-Kontur (helles Schieferblau)
INK2 = '#4c5a6b'         # schwaechere Kontur
EDGE = '#8b9bb0'         # Kanten/Pfeile
BG = '#0d1117'           # Hintergrund (GitHub-Dark)
PAPER = '#151b23'        # dezentes Hintergrund-Raster
TEXT = '#e6edf3'         # Haupttext
LABEL_TXT = '#8b949e'    # Sekundaertext / Labels
TITLE_TXT = '#f0f6fc'    # Titel
SURFACE = '#161c26'      # Karten-/Panel-Flaeche
SHADOW = '#05080c'       # Schatten hinter Formen

# Dunkle Toene mit passender Akzent-Kontur (STROKE_OF)
FILLS = {
    'stadium': '#16283d',
    'rect': '#16283d',
    'subproc': '#16283d',
    'para': '#14321f',
    'diamond': '#33290f',
    'circle': '#271b45',
    'cyl': '#14321f',
    'state': '#271b45',
    'startdot': TEXT,
    'enddot': BG,
}
STROKE_OF = {
    '#16283d': '#58a6ff',   # Blau
    '#14321f': '#56d364',   # Gruen
    '#33290f': '#e3b341',   # Amber
    '#271b45': '#d2a8ff',   # Lila
    '#12303c': '#39c5cf',   # Cyan
    '#3a1c1c': '#f47067',   # Rot
}

PASTELS = ['#16283d', '#14321f', '#33290f', '#3a1c1c', '#271b45', '#12303c']
PASTELS_LIGHT = ['#131a26', '#101c16', '#1c1a10', '#201414', '#191427',
                 '#101c22']
GIT_COLORS = ['#58a6ff', '#56d364', '#e3b341', '#f47067', '#d2a8ff',
              '#39c5cf']

# Segoe UI (Windows) als moderne Sans-Serif; DejaVu als Fallback
SKILL_DIR = Path(__file__).resolve().parent
FONT_REG = Path(r'C:\Windows\Fonts') / 'segoeui.ttf'
FONT_BOLD = Path(r'C:\Windows\Fonts') / 'segoeuib.ttf'
if not FONT_REG.exists():
    FONT_REG = FONT_BOLD = Path('DejaVuSans.ttf')
if not FONT_BOLD.exists():
    FONT_BOLD = FONT_REG

S = 2  # Supersampling-Faktor
SX, SY = 340, 190      # Spalten-/Reihenabstand des Layouts
MARGIN = 90
NODE_FS, LABEL_FS = 24, 22


# ---------------------------------------------------------------- helpers

def font(n, bold=False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), n * S)


def wrap(text, width=22):
    lines = []
    for part in text.split('\n'):
        words, cur = part.split(), ''
        for w in words:
            t = (cur + ' ' + w).strip()
            if len(t) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur or not part:
            lines.append(cur)
    return lines or ['']


# ---------------------------------------------------------------- parsing

NODE_RE = re.compile(
    r'^\s*([\w\u00c0-\u00ff]+)\s*(?:'
    r'\(\((.*?)\)\)|'      # 2 circle
    r'\(\[(.*?)\]\)|'      # 3 stadium
    r'\[\[(.*?)\]\]|'      # 4 subproc
    r'\[\((.*?)\)\]|'      # 5 cylinder
    r'\[/(.+?)/\]|'        # 6 parallelogram /
    r'\[\\(.+?)\\\]|'      # 7 parallelogram backslash
    r'\{(.*?)\}|'          # 8 diamond
    r'\[(.*?)\]|'          # 9 rect
    r'\((.*?)\)'           # 10 rounded -> stadium
    r')?\s*$'
)

SHAPES = {2: 'circle', 3: 'stadium', 4: 'subproc', 5: 'cyl', 6: 'para',
          7: 'para', 8: 'diamond', 9: 'rect', 10: 'stadium'}


def unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in '"\'':
        s = s[1:-1]
    return s


class Diagram:
    def __init__(self, direction):
        self.direction = direction          # 'TD'/'TB' oder 'LR'/'RL'
        self.nodes = {}                     # id -> {'shape','label','order'}
        self.edges = []                     # (src, dst, label)

    def node(self, nid, shape='rect', label=None):
        if nid not in self.nodes:
            self.nodes[nid] = {'shape': shape,
                               'label': label if label is not None else nid,
                               'order': len(self.nodes)}
        elif label is not None:
            self.nodes[nid]['shape'] = shape
            self.nodes[nid]['label'] = label
        return nid


def parse_node_spec(seg, dia):
    m = NODE_RE.match(seg)
    if not m:
        return None
    nid = m.group(1)
    for gidx, shape in SHAPES.items():
        if m.group(gidx) is not None:
            return dia.node(nid, shape, unquote(m.group(gidx)))
    return dia.node(nid)


def parse_mermaid(code):
    """Gibt Diagram zurueck oder None, wenn kein Flowchart."""
    direction = None
    body = []
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue
        if direction is None:
            m = re.match(r'^(?:flowchart|graph)\s+(TD|TB|LR|RL|BT)', line, re.I)
            if m:
                direction = m.group(1).upper()
            continue
        if re.match(r'^(classDef|class|style|linkStyle|subgraph|end\b|click)', line):
            continue
        body.append(line)
    if direction is None:
        return None
    if direction == 'BT':
        direction = 'TB'  # einfache Naeherung
    dia = Diagram(direction)
    for line in body:
        if '-->' not in line:
            parse_node_spec(line, dia)
            continue
        parts = line.split('-->')
        ids, labels = [], []
        for part in parts:
            label = None
            if '--' in part:
                seg, lbl = part.split('--', 1)
                label = unquote(lbl)
            else:
                seg = part
            nid = parse_node_spec(seg, dia)
            if nid is None:
                break
            ids.append(nid)
            labels.append(label)
        else:
            for i in range(len(ids) - 1):
                dia.edges.append((ids[i], ids[i + 1], labels[i]))
    return dia if dia.nodes else None


# ---------------------------------------------------------------- layout

def layout(dia):
    """Weist jedem Knoten Spalte/Reihe zu; liefert pos, back_edges, cols, rows."""
    out = {n: [] for n in dia.nodes}
    preds = {n: [] for n in dia.nodes}
    for e in dia.edges:
        out[e[0]].append(e)
        preds[e[1]].append(e)

    # Rueckwaertskanten per DFS erkennen (zyklenfreies Ranking ermoeglichen)
    back, visited = set(), set()

    def dfs(n, stack):
        for e in out[n]:
            if e[1] in stack:
                back.add(e)
            elif e[1] not in visited:
                visited.add(e[1])
                dfs(e[1], stack | {e[1]})

    roots = [n for n in dia.nodes if not preds[n]] or list(dia.nodes)[:1]
    for r in roots:
        if r not in visited:
            visited.add(r)
            dfs(r, {r})
    for n in dia.nodes:  # nicht erreichbare Reste
        if n not in visited:
            visited.add(n)
            dfs(n, {n})

    # Laengster-Pfad-Ranking nur ueber Vorwaertskanten (Kahn)
    indeg = {n: 0 for n in dia.nodes}
    for e in dia.edges:
        if e not in back:
            indeg[e[1]] += 1
    rank = {n: 0 for n in dia.nodes}
    queue = sorted((n for n in dia.nodes if indeg[n] == 0),
                   key=lambda n: dia.nodes[n]['order'])
    while queue:
        n = queue.pop(0)
        for e in out[n]:
            if e in back:
                continue
            d = e[1]
            rank[d] = max(rank[d], rank[n] + 1)
            indeg[d] -= 1
            if indeg[d] == 0:
                queue.append(d)
                queue.sort(key=lambda x: dia.nodes[x]['order'])

    # Spalten: moeglichst nah an der Spalte der Vorgaenger
    col = {}
    for r in sorted(set(rank.values())):
        row = [n for n in dia.nodes if rank[n] == r]
        row.sort(key=lambda n: dia.nodes[n]['order'])

        def want(n):
            cs = [col[p] for (p, d, l) in preds[n]
                  if (p, d, l) not in back and p in col]
            return sum(cs) / len(cs) if cs else 0.0

        row.sort(key=lambda n: (want(n), dia.nodes[n]['order']))
        used = set()
        for n in row:
            w = want(n)
            c = int(round(w))
            step = 0
            while True:
                for cand in ((c + step,) if step == 0 else (c + step, c - step)):
                    if cand not in used and cand >= 0:
                        col[n] = cand
                        used.add(cand)
                        break
                else:
                    step += 1
                    continue
                break

    pos = {n: (MARGIN + col[n] * SX, MARGIN + rank[n] * SY) for n in dia.nodes}
    return pos, back, rank, col


# ---------------------------------------------------------------- drawing

def dims(shape, lines):
    f = ImageFont.truetype(str(FONT_REG), NODE_FS)
    tw = max((f.getlength(l) for l in lines), default=20)
    th = len(lines) * 32
    if shape == 'diamond':
        return tw * 2.0 + 90, th * 2.1 + 90
    if shape == 'para':
        return tw + 110, th + 50
    if shape == 'stadium':
        return tw + 90, th + 50
    if shape == 'circle':
        dd = max(tw + 50, th + 50, 70)
        return dd, dd
    if shape == 'cyl':
        return tw + 80, th + 90
    if shape == 'subproc':
        return tw + 72, th + 50
    if shape == 'state':
        return tw + 76, th + 54
    if shape in ('startdot', 'enddot'):
        return 40, 40
    return tw + 70, th + 50


class Sketch:
    def __init__(self, w, h):
        self.im = Image.new('RGB', (w * S, h * S), BG)
        self.d = ImageDraw.Draw(self.im)
        self.w, self.h = w, h

    def xy(self, p):
        return tuple(round(v * S) for v in p)

    def line(self, ps, c=EDGE, w=4):
        pts = [self.xy(p) for p in ps]
        self.d.line(pts, fill=c, width=w * S, joint='curve')
        r = w * S // 2
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=c)

    def head(self, tip, frm, size=18, angle=27, c=EDGE):
        # gefuellte Dreiecks-Pfeilspitze in Linienrichtung
        a = math.atan2(tip[1] - frm[1], tip[0] - frm[0])
        base = (tip[0] - size * math.cos(a), tip[1] - size * math.sin(a))
        px, py = -math.sin(a), math.cos(a)
        w2 = size * math.tan(math.radians(angle)) * 0.55
        p1 = (base[0] + px * w2, base[1] + py * w2)
        p2 = (base[0] - px * w2, base[1] - py * w2)
        self.d.polygon([self.xy(tip), self.xy(p1), self.xy(p2)], fill=c)

    def polyline_arrow(self, ps):
        clean = [ps[0]]
        for p in ps[1:]:
            if abs(p[0] - clean[-1][0]) > 1 or abs(p[1] - clean[-1][1]) > 1:
                clean.append(p)
        self.line(clean)
        if len(clean) >= 2:
            self.head(clean[-1], clean[-2])

    def text(self, x, y, v, n=NODE_FS, b=False, c=TEXT):
        self.d.text(self.xy((x, y)), v, font=font(n, b), fill=c, anchor='mm')

    def label_pill(self, x, y, v):
        f = ImageFont.truetype(str(FONT_BOLD), LABEL_FS)
        tw = f.getlength(v)
        hw, hh = tw / 2 + 14, 20
        self.d.rounded_rectangle(((x - hw) * S, (y - hh) * S, (x + hw) * S,
                                  (y + hh - 2) * S), radius=13 * S,
                                 fill=SURFACE, outline=INK2, width=2 * S)
        self.text(x, y, v, LABEL_FS, True, LABEL_TXT)

    def dashed(self, p1, p2, dash=12, gap=8, c=EDGE, w=3):
        x1, y1 = p1
        x2, y2 = p2
        L = math.hypot(x2 - x1, y2 - y1)
        if L == 0:
            return
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        t = 0.0
        while t < L:
            e = min(t + dash, L)
            self.d.line([self.xy((x1 + ux * t, y1 + uy * t)),
                         self.xy((x1 + ux * e, y1 + uy * e))],
                        fill=c, width=w * S)
            t = e + gap

    # ---- shapes (alle zentriert um cx, cy) ----
    def _oc(self, fill):
        # Akzent-Kontur passend zur Fuellfarbe
        return STROKE_OF.get(fill, INK)

    def poly(self, ps, fill):
        oc = self._oc(fill)
        sh = [self.xy((x + 3, y + 6)) for x, y in ps]
        self.d.polygon(sh, fill=SHADOW)
        p = [self.xy(a) for a in ps]
        self.d.polygon(p, fill=fill)
        self.d.line(p + [p[0]], fill=oc, width=3 * S, joint='curve')

    def rect(self, cx, cy, w, h, fill, double=False):
        x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        oc = self._oc(fill)
        self.d.rounded_rectangle(((x1 + 3) * S, (y1 + 6) * S, (x2 + 3) * S,
                                  (y2 + 6) * S), radius=10 * S, fill=SHADOW)
        b = (x1 * S, y1 * S, x2 * S, y2 * S)
        self.d.rounded_rectangle(b, radius=10 * S, fill=fill, outline=oc,
                                 width=3 * S)
        if double:
            self.line([(x1 + 14, y1 + 5), (x1 + 14, y2 - 5)], oc, 2)
            self.line([(x2 - 14, y1 + 5), (x2 - 14, y2 - 5)], oc, 2)

    def stadium(self, cx, cy, w, h, fill):
        x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        oc = self._oc(fill)
        self.d.rounded_rectangle(((x1 + 3) * S, (y1 + 6) * S, (x2 + 3) * S,
                                  (y2 + 6) * S), radius=(h / 2) * S,
                                 fill=SHADOW)
        b = (x1 * S, y1 * S, x2 * S, y2 * S)
        self.d.rounded_rectangle(b, radius=(h / 2) * S, fill=fill, outline=oc,
                                 width=3 * S)

    def para(self, cx, cy, w, h, fill):
        sk = min(26, w * 0.12)
        x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        self.poly([(x1 + sk, y1), (x2, y1), (x2 - sk, y2), (x1, y2)], fill)

    def diamond(self, cx, cy, w, h, fill):
        self.poly([(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2),
                   (cx - w / 2, cy)], fill)

    def circle(self, cx, cy, w, h, fill):
        r = w / 2
        oc = self._oc(fill)
        self.d.ellipse(((cx - r + 3) * S, (cy - r + 6) * S,
                        (cx + r + 3) * S, (cy + r + 6) * S), fill=SHADOW)
        self.d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S),
                       fill=fill, outline=oc, width=3 * S)

    def cyl(self, cx, cy, w, h, fill):
        x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        oc = self._oc(fill)
        ry = min(14, h / 5)
        ytc, ybc = y1 + ry, y2 - ry
        B = lambda x, y: (round(x * S), round(y * S))
        self.d.rectangle((*B(x1 + 3, ytc + 6), *B(x2 + 3, ybc + 6)),
                         fill=SHADOW)
        self.d.rectangle((*B(x1, ytc), *B(x2, ybc)), fill=fill)
        self.d.ellipse((*B(x1, ybc - ry), *B(x2, ybc + ry)), fill=fill)
        self.d.ellipse((*B(x1, ytc - ry), *B(x2, ytc + ry)), fill='#1d4530',
                       outline=oc, width=3 * S)
        self.d.line([self.xy((x1, ytc)), self.xy((x1, ybc))], fill=oc,
                    width=3 * S)
        self.d.line([self.xy((x2, ytc)), self.xy((x2, ybc))], fill=oc,
                    width=3 * S)
        self.d.arc((*B(x1, ybc - ry), *B(x2, ybc + ry)), 0, 180, fill=oc,
                   width=3 * S)

    def state(self, cx, cy, w, h, fill):
        x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        oc = self._oc(fill)
        self.d.rounded_rectangle(((x1 + 3) * S, (y1 + 6) * S, (x2 + 3) * S,
                                  (y2 + 6) * S), radius=16 * S, fill=SHADOW)
        b = (x1 * S, y1 * S, x2 * S, y2 * S)
        self.d.rounded_rectangle(b, radius=16 * S, fill=fill, outline=oc,
                                 width=3 * S)

    def startdot(self, cx, cy, w, h, fill):
        r = 13
        self.d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S),
                       fill=TEXT)

    def enddot(self, cx, cy, w, h, fill):
        r = 14
        self.d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S),
                       outline=TEXT, width=3 * S)
        self.d.ellipse(((cx - 6) * S, (cy - 6) * S, (cx + 6) * S, (cy + 6) * S),
                       fill=TEXT)

    def node(self, shape, cx, cy, w, h, fill=None):
        fill = fill or FILLS.get(shape, FILLS['rect'])
        if shape == 'subproc':
            self.rect(cx, cy, w, h, fill, double=True)
        else:
            getattr(self, 'rect' if shape == 'rect' else shape)(
                cx, cy, w, h, fill)


def render(dia):
    pos, back, rank, col = layout(dia)

    meta = {}
    for nid, nd in dia.nodes.items():
        lines = wrap(nd['label'])
        w, h = dims(nd['shape'], lines)
        meta[nid] = {'lines': lines, 'w': w, 'h': h}

    maxw = max(meta[n]['w'] for n in dia.nodes)
    maxh = max(meta[n]['h'] for n in dia.nodes)
    # Versatz, damit breite/hohe Knoten in Spalte/Reihe 0 nicht abgeschnitten
    # werden und links/oben Platz fuer Rueckkanten bleibt
    xoff = max(0, MARGIN + maxw / 2 + 70 - min(p[0] for p in pos.values()))
    yoff = max(0, MARGIN + maxh / 2 + 60 - min(p[1] for p in pos.values()))
    pos = {n: (p[0] + xoff, p[1] + yoff) for n, p in pos.items()}

    xs = [pos[n][0] for n in dia.nodes]
    ys = [pos[n][1] for n in dia.nodes]
    lr = dia.direction in ('LR', 'RL')

    gutter = min(xs) - maxw / 2 - 70     # Fuehrungsschiene fuer Rueckkanten
    cw = max(xs) + maxw / 2 + MARGIN
    ch = max(ys) + maxh / 2 + MARGIN
    W, H = ((int(ch), int(cw)) if lr else (int(cw), int(ch)))
    W, H = max(W, 500), max(H, 320)

    sk = Sketch(W, H)
    for y in range(45, H, 31):
        sk.line([(60, y), (W - 60, y)], PAPER, 1)

    def P(n):
        x, y = pos[n]
        return (y, x) if lr else (x, y)

    # ---- Kanten ----
    for (src, dst, lab) in dia.edges:
        sx, sy = P(src)
        tx, ty = P(dst)
        sw, sh = meta[src]['w'], meta[src]['h']
        tw, th = meta[dst]['w'], meta[dst]['h']
        if (src, dst, lab) in back or rank.get(dst, 0) <= rank.get(src, 0):
            # Rueckkante ueber die linke/obere Fuehrungsschiene
            if lr:
                gy = min(ys) - maxh / 2 - 60
                pts = [(sx, sy - sh / 2), (sx, gy), (tx, gy), (tx, ty - th / 2)]
                lab_pos = (sx - 10, (sy + gy) / 2)
            else:
                pts = [(sx - sw / 2, sy), (gutter, sy), (gutter, ty),
                       (tx - tw / 2, ty)]
                lab_pos = (gutter - 10, (sy + ty) / 2)
            sk.polyline_arrow(pts)
            if lab:
                sk.label_pill(*lab_pos, lab)
            continue
        if lr:
            a, b = (sx + sw / 2, sy), (tx - tw / 2, ty)
            if abs(a[1] - b[1]) < 12:
                pts = [a, b]
                lab_pos = ((a[0] + b[0]) / 2, a[1] - 24)
            else:
                midx = (a[0] + b[0]) / 2
                pts = [a, (midx, a[1]), (midx, b[1]), b]
                lab_pos = (midx, (a[1] + b[1]) / 2 - 24)
        else:
            a, b = (sx, sy + sh / 2), (tx, ty - th / 2)
            if abs(a[0] - b[0]) < 12:
                pts = [a, b]
                lab_pos = (a[0] + 40, (a[1] + b[1]) / 2)
            else:
                midy = (a[1] + b[1]) / 2
                pts = [a, (a[0], midy), (b[0], midy), b]
                lab_pos = ((a[0] + b[0]) / 2, midy - 24)
        sk.polyline_arrow(pts)
        if lab:
            sk.label_pill(*lab_pos, lab)

    # ---- Knoten ----
    for nid, nd in dia.nodes.items():
        cx, cy = P(nid)
        m = meta[nid]
        sk.node(nd['shape'], cx, cy, m['w'], m['h'])
        off = -16 * (len(m['lines']) - 1)
        for i, ln in enumerate(m['lines']):
            sk.text(cx, cy + off + i * 32, ln)

    out_im = sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)
    return out_im


# ---------------------------------------------------------------- ER diagrams

ER_REL_RE = re.compile(
    r'^\s*([\w\u00c0-\u00ff-]+)\s+([|o}{]{1,2})(--|\.\.)([|o}{]{1,2})\s+'
    r'([\w\u00c0-\u00ff-]+)\s*:\s*(.+?)\s*$')
ER_BLOCK_RE = re.compile(r'^\s*([\w\u00c0-\u00ff-]+)\s*\{\s*$')


def parse_er(code):
    """Liefert {'entities': {name: [(typ, name, keys)]}, 'rels': [...]} oder None."""
    entities = {}
    rels = []
    cur = None
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line == 'erDiagram':
            continue
        if cur is not None:
            if line.startswith('}'):
                cur = None
            else:
                parts = line.split()
                entities[cur].append((parts[0],
                                      parts[1] if len(parts) > 1 else '',
                                      ' '.join(parts[2:])))
            continue
        m = ER_BLOCK_RE.match(line)
        if m:
            cur = m.group(1)
            entities.setdefault(cur, [])
            continue
        m = ER_REL_RE.match(line)
        if m:
            a, ca, op, cb, b, lab = m.groups()
            entities.setdefault(a, [])
            entities.setdefault(b, [])
            rels.append((a, ca, op == '..', cb, b, unquote(lab)))
    if not entities:
        return None
    return {'entities': entities, 'rels': rels}


def er_meta(name, attrs):
    f_t = font(22, True)
    f_a = font(19)
    rows = []
    for typ, nm, keys in attrs:
        t = f'{typ} {nm}'.strip()
        if keys:
            t += f'  ({keys})'
        rows.append(t)
    tw = max([f_t.getlength(name)] + [f_a.getlength(r) for r in rows])
    w = tw + 60
    h = 46 + len(rows) * 32 + 14
    return rows, w, h


def border_point(cx, cy, w, h, dx, dy):
    """Schnittpunkt des Strahls vom Zentrum in Richtung (dx, dy) mit dem Rechteck."""
    if abs(dx) < 1e-9:
        return (cx, cy + math.copysign(h / 2, dy))
    if abs(dy) < 1e-9:
        return (cx + math.copysign(w / 2, dx), cy)
    t = min((w / 2) / abs(dx), (h / 2) / abs(dy))
    return (cx + dx * t, cy + dy * t)


def card_symbols(sk, tip, frm, card):
    """Kraehenfuss/Kreis/Striche der Kardinalitaet am Kastenrand (tip)."""
    dx, dy = tip[0] - frm[0], tip[1] - frm[1]
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    has_foot = '}' in card or '{' in card
    if has_foot:
        ax, ay = tip[0] - ux * 24, tip[1] - uy * 24
        sk.line([(ax, ay), tip])
        sk.line([(ax, ay), (tip[0] - ux * 2 + px * 13, tip[1] - uy * 2 + py * 13)])
        sk.line([(ax, ay), (tip[0] - ux * 2 - px * 13, tip[1] - uy * 2 - py * 13)])
    dist = 32 if has_foot else 8
    for ch in card:
        if ch in '}{':
            continue
        if ch == 'o':
            cxp, cyp = tip[0] - ux * (dist + 7), tip[1] - uy * (dist + 7)
            sk.d.ellipse(sk.xy((cxp - 7, cyp - 7)) + sk.xy((cxp + 7, cyp + 7)),
                         outline=EDGE, width=3 * S, fill=BG)
            dist += 22
        elif ch == '|':
            cxp, cyp = tip[0] - ux * (dist + 3), tip[1] - uy * (dist + 3)
            sk.line([(cxp - px * 10, cyp - py * 10),
                     (cxp + px * 10, cyp + py * 10)], w=4)
            dist += 14


def er_box(sk, cx, cy, name, rows, w, h):
    x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    sk.poly([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], '#1a2230')
    if not rows:
        sk.d.text(sk.xy((cx, cy)), name, font=font(22, True), fill=TEXT,
                  anchor='mm')
        return
    hh = 46
    sk.poly([(x1 + 1, y1 + 1), (x2 - 1, y1 + 1), (x2 - 1, y1 + hh),
             (x1 + 1, y1 + hh)], '#16283d')
    sk.d.text(sk.xy((cx, y1 + hh / 2)), name, font=font(22, True), fill=TEXT,
              anchor='mm')
    for i, r in enumerate(rows):
        yy = y1 + hh + 16 + i * 32
        if i:
            sk.line([(x1 + 6, y1 + hh + i * 32), (x2 - 6, y1 + hh + i * 32)],
                    '#30363d', 1)
        sk.d.text(sk.xy((x1 + 26, yy)), r, font=font(19), fill=TEXT, anchor='lm')


def render_er(er):
    ents = er['entities']
    metas = {n: er_meta(n, a) for n, a in ents.items()}
    dia = Diagram('TD')
    for n in ents:
        dia.node(n, 'rect', n)
    for (a, _ca, _d, _cb, b, _l) in er['rels']:
        dia.edges.append((a, b, None))
    _pos, _back, rank, col = layout(dia)

    colw = max(m[1] for m in metas.values()) + 190
    ranks = sorted(set(rank.values()))
    ypos = {}
    y = MARGIN
    for r in ranks:
        rh = max(metas[n][2] for n in dia.nodes if rank[n] == r) + 120
        ypos[r] = y + rh / 2
        y += rh
    P = {n: (MARGIN + col[n] * colw + colw / 2, ypos[rank[n]])
         for n in dia.nodes}
    W = int(MARGIN + (max(col.values()) + 1) * colw + 60)
    H = int(y + 60)

    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(60, yy), (W - 60, yy)], PAPER, 1)

    for (a, ca, ds, cb, b, lab) in er['rels']:
        ax, ay = P[a]
        bx, by = P[b]
        pa = border_point(ax, ay, metas[a][1], metas[a][2], bx - ax, by - ay)
        pb = border_point(bx, by, metas[b][1], metas[b][2], ax - bx, ay - by)
        if ds:
            sk.dashed(pa, pb)
        else:
            sk.line([pa, pb])
        card_symbols(sk, pa, pb, ca)
        card_symbols(sk, pb, pa, cb)
        if lab:
            sk.label_pill((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2 - 26, lab)

    for n in ents:
        rows, w, h = metas[n]
        er_box(sk, P[n][0], P[n][1], n, rows, w, h)

    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- sequence diagrams

SEQ_MSG_RE = re.compile(
    r'^\s*([\w\u00c0-\u00ff-]*[\w\u00c0-\u00ff])\s*'
    r'(-->>|-->|->>|->|--\)|-\)|--x|-x)\s*'
    r'([\w\u00c0-\u00ff-]*[\w\u00c0-\u00ff])\s*:\s*(.*?)\s*$')
SEQ_PART_RE = re.compile(
    r'^\s*(participant|actor)\s+([\w\u00c0-\u00ff-]+)(?:\s+as\s+(.+?))?\s*$')
SEQ_NOTE_RE = re.compile(
    r'^\s*Note\s+(over|right of|left of)\s+'
    r'([\w\u00c0-\u00ff-]+(?:\s*,\s*[\w\u00c0-\u00ff-]+)?)\s*:\s*(.*?)\s*$')
SEQ_BLOCK_RE = re.compile(
    r'^\s*(loop|alt|opt|par|critical|break)\b\s*(.*?)\s*$')


def parse_seq(code):
    """Liefert {'parts': [(id, label, kind)], 'events': [...]} oder None."""
    parts = []
    events = []
    seen = set()

    def add_part(pid, label=None, kind='participant'):
        if pid not in seen:
            seen.add(pid)
            parts.append((pid, label or pid, kind))
        elif label:
            i = next(i for i, p in enumerate(parts) if p[0] == pid)
            parts[i] = (pid, label, kind)

    for raw in code.splitlines():
        line = raw.strip()
        if (not line or line.startswith('%%') or line == 'sequenceDiagram'
                or line.startswith('autonumber')):
            continue
        m = SEQ_PART_RE.match(line)
        if m:
            add_part(m.group(2), unquote(m.group(3)) if m.group(3) else None,
                     m.group(1))
            continue
        m = SEQ_MSG_RE.match(line)
        if m:
            a, op, b, text = m.groups()
            add_part(a)
            add_part(b)
            events.append(('msg', a, b, unquote(text),
                           op.startswith('--')))
            continue
        m = SEQ_NOTE_RE.match(line)
        if m:
            where, ids, text = m.groups()
            ids = [i.strip() for i in ids.split(',')]
            for i in ids:
                add_part(i)
            events.append(('note', ids, where, unquote(text)))
            continue
        m = SEQ_BLOCK_RE.match(line)
        if m:
            events.append(('bs', m.group(1), unquote(m.group(2))))
            continue
        if re.match(r'^else\b', line):
            events.append(('bsep', unquote(line[4:].strip())))
            continue
        if re.match(r'^end\s*$', line):
            events.append(('be',))
            continue
        # activate/deactivate/rect u.ae. ignorieren
    return {'parts': parts, 'events': events} if parts else None


def note_box(sk, cx, cy, text):
    lines = wrap(text, 34)
    f = font(19)
    w = max(f.getlength(l) for l in lines) + 44
    h = len(lines) * 28 + 22
    x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    fold = 14
    sk.poly([(x1, y1), (x2 - fold, y1), (x2, y1 + fold), (x2, y2), (x1, y2)],
            '#3a2f10')
    sk.line([(x2 - fold, y1), (x2 - fold, y1 + fold), (x2, y1 + fold)],
            INK2, 2)
    off = -14 * (len(lines) - 1)
    for i, ln in enumerate(lines):
        sk.text(cx, cy + off + i * 28, ln, 19)
    return w, h


def render_seq(seq):
    parts = seq['parts']
    events = seq['events']
    f_lab = font(21, True)
    spacing = max(260, max(f_lab.getlength(p[1]) for p in parts) + 130)
    xs = {p[0]: 180 + i * spacing for i, p in enumerate(parts)}
    W = int(180 + (len(parts) - 1) * spacing + 300)

    box_h = 56
    top = 80
    y = top + box_h + 50

    msgs, notes, frames, seps = [], [], [], []
    stack = []
    for ev in events:
        kind = ev[0]
        if kind == 'msg':
            _k, a, b, text, ds = ev
            if a == b:
                msgs.append((a, b, text, ds, y + 24))
                y += 104
            else:
                msgs.append((a, b, text, ds, y + 26))
                y += 72
        elif kind == 'note':
            _k, ids, where, text = ev
            hh = len(wrap(text, 34)) * 28 + 22
            notes.append((ids, where, text, y + hh / 2 + 8))
            y += hh + 30
        elif kind == 'bs':
            stack.append((ev[1], ev[2], y))
            y += 58
        elif kind == 'bsep':
            seps.append((y + 20, ev[1]))
            y += 48
        elif kind == 'be':
            if stack:
                knd, lab, ytop = stack.pop()
                frames.append((knd, lab, ytop, y + 4))
            y += 34
    while stack:  # nicht geschlossene Bloecke dennoch zeichnen
        knd, lab, ytop = stack.pop()
        frames.append((knd, lab, ytop, y))
    H = int(y + 80)

    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(50, yy), (W - 50, yy)], PAPER, 1)

    # Lebenslinien
    for pid, x in xs.items():
        sk.dashed((x, top + box_h), (x, H - 60), dash=14, gap=9, c='#3d444d',
                  w=3)
    # Rahmen der Bloecke
    for knd, lab, ytop, ybot in frames:
        x1, x2 = 60, W - 60
        for (p1, p2) in [((x1, ytop), (x2, ytop)), ((x2, ytop), (x2, ybot)),
                         ((x2, ybot), (x1, ybot)), ((x1, ybot), (x1, ytop))]:
            sk.dashed(p1, p2, dash=10, gap=7, c=INK2, w=2)
        tab = f'{knd}  [{lab}]' if lab else knd
        f_t = font(18, True)
        tw = f_t.getlength(tab) + 26
        sk.d.rounded_rectangle(sk.xy((x1 + 10, ytop + 4)) +
                               sk.xy((x1 + 10 + tw, ytop + 34)),
                               radius=6 * S, fill='#271b45', outline=INK,
                               width=3 * S)
        sk.d.text(sk.xy((x1 + 23, ytop + 19)), tab, font=f_t, fill=TEXT,
                  anchor='lm')
    for sy, slab in seps:
        sk.dashed((60, sy), (W - 60, sy), dash=10, gap=7, c=INK2, w=2)
        if slab:
            sk.d.text(sk.xy((78, sy)), f'[{slab}]', font=font(17, True),
                      fill=LABEL_TXT, anchor='lm')
    # Nachrichten
    for a, b, text, ds, my in msgs:
        xa, xb = xs[a], xs[b]
        if a == b:
            pts = [(xa, my), (xa + 80, my), (xa + 80, my + 36), (xa, my + 36)]
            sk.line(pts)
            sk.head(pts[-1], pts[-2])
            sk.d.text(sk.xy((xa + 96, my + 4)), text, font=font(20),
                      fill=TEXT, anchor='lm')
            continue
        if ds:
            sk.dashed((xa, my), (xb, my))
        else:
            sk.line([(xa, my), (xb, my)])
        sk.head((xb, my), (xa, my))
        mid = (xa + xb) / 2
        sk.d.text(sk.xy((mid, my - 16)), text, font=font(20), fill=TEXT,
                  anchor='mm')
    # Notizen
    for ids, where, text, ny in notes:
        if where == 'over' and len(ids) == 2:
            cx = (xs[ids[0]] + xs[ids[1]]) / 2
        elif where == 'right of':
            cx = xs[ids[0]] + 150
        elif where == 'left of':
            cx = xs[ids[0]] - 150
        else:
            cx = xs[ids[0]]
        note_box(sk, cx, ny, text)
    # Teilnehmer-Kaesten oben
    for pid, label, kind in parts:
        x = xs[pid]
        tw = f_lab.getlength(label) + 56
        fill = '#3a1c1c' if kind == 'actor' else '#16283d'
        sk.stadium(x, top + box_h / 2, tw, box_h, fill)
        sk.text(x, top + box_h / 2, label, 21, True)

    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- class diagrams

CLS_REL_RE = re.compile(
    r'^\s*([\w\u00c0-\u00ff-]+)\s*(?:"([^"]*)")?\s*([<|>*o.\-]{2,})\s*'
    r'(?:"([^"]*)")?\s*([\w\u00c0-\u00ff-]+)(?:\s*:\s*(.+?))?\s*$')
CLS_BLOCK_RE = re.compile(r'^\s*class\s+([\w\u00c0-\u00ff-]+)\s*\{\s*$')
CLS_DECL_RE = re.compile(r'^\s*class\s+([\w\u00c0-\u00ff-]+)\s*$')
CLS_INLINE_RE = re.compile(r'^\s*([\w\u00c0-\u00ff-]+)\s*:\s*([+\-#~].+?)\s*$')
CLS_STEREO_RE = re.compile(r'^\s*<<(.+?)>>\s+([\w\u00c0-\u00ff-]+)\s*$')


def parse_class(code):
    classes = {}
    rels = []
    cur = None
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line == 'classDiagram':
            continue
        if cur is not None:
            if line.startswith('}'):
                cur = None
            else:
                classes[cur]['members'].append(line)
            continue
        m = CLS_BLOCK_RE.match(line)
        if m:
            cur = m.group(1)
            classes.setdefault(cur, {'members': [], 'stereo': None})
            continue
        m = CLS_STEREO_RE.match(line)
        if m:
            name = m.group(2)
            classes.setdefault(name, {'members': [], 'stereo': None})
            classes[name]['stereo'] = f'\u00ab{m.group(1)}\u00bb'
            continue
        m = CLS_REL_RE.match(line)
        if m:
            a, ca, rel, cb, b, lab = m.groups()
            classes.setdefault(a, {'members': [], 'stereo': None})
            classes.setdefault(b, {'members': [], 'stereo': None})
            rels.append((a, ca, rel, cb, b, unquote(lab) if lab else None))
            continue
        m = CLS_DECL_RE.match(line)
        if m:
            classes.setdefault(m.group(1), {'members': [], 'stereo': None})
            continue
        m = CLS_INLINE_RE.match(line)
        if m:
            name = m.group(1)
            classes.setdefault(name, {'members': [], 'stereo': None})
            classes[name]['members'].append(m.group(2))
            continue
        # note for ..., namespace usw. ignorieren
    if not classes:
        return None
    return {'classes': classes, 'rels': rels}


def box_meta(title, rows):
    f_t = font(22, True)
    f_a = font(19)
    tw = max([f_t.getlength(title)] + [f_a.getlength(r) for r in rows])
    return rows, tw + 60, 46 + len(rows) * 32 + 14


def _unit(tip, frm):
    dx, dy = tip[0] - frm[0], tip[1] - frm[1]
    L = math.hypot(dx, dy) or 1
    return dx / L, dy / L, -dy / L, dx / L


def uml_tri(sk, tip, frm, fill=BG):
    ux, uy, px, py = _unit(tip, frm)
    b1 = (tip[0] - ux * 22 + px * 13, tip[1] - uy * 22 + py * 13)
    b2 = (tip[0] - ux * 22 - px * 13, tip[1] - uy * 22 - py * 13)
    sk.d.polygon([sk.xy(p) for p in (tip, b1, b2)], fill=fill, outline=EDGE,
                 width=3 * S)


def uml_dia(sk, tip, frm, fill):
    ux, uy, px, py = _unit(tip, frm)
    mid = (tip[0] - ux * 12, tip[1] - uy * 12)
    far = (tip[0] - ux * 24, tip[1] - uy * 24)
    pts = [tip, (mid[0] + px * 8, mid[1] + py * 8), far,
           (mid[0] - px * 8, mid[1] - py * 8)]
    sk.d.polygon([sk.xy(p) for p in pts], fill=fill, outline=EDGE,
                 width=3 * S)


def uml_deco(sk, tip, frm, kind):
    if kind == 'tri':
        uml_tri(sk, tip, frm)
    elif kind == 'tri_f':
        uml_tri(sk, tip, frm, fill=EDGE)
    elif kind == 'dia_f':
        uml_dia(sk, tip, frm, fill=EDGE)
    elif kind == 'dia_o':
        uml_dia(sk, tip, frm, fill=BG)
    elif kind == 'arrow':
        sk.head(tip, frm)


def rel_ends(rel):
    """Liefert (Deko links, Deko rechts, gestrichelt)."""
    dashed = '..' in rel
    l = r = None
    if rel.startswith('<|'):
        l = 'tri'
    elif rel.startswith('*'):
        l = 'dia_f'
    elif rel.startswith('o'):
        l = 'dia_o'
    elif rel.startswith('<'):
        l = 'arrow'
    if rel.endswith('|>'):
        r = 'tri'
    elif rel.endswith('*'):
        r = 'dia_f'
    elif rel.endswith('o'):
        r = 'dia_o'
    elif rel.endswith('>'):
        r = 'arrow'
    return l, r, dashed


def render_class(cd):
    classes = cd['classes']
    metas = {}
    for n, info in classes.items():
        rows = ([info['stereo']] if info['stereo'] else []) + info['members']
        metas[n] = box_meta(n, rows)
    dia = Diagram('TD')
    for n in classes:
        dia.node(n, 'rect', n)
    for (a, _ca, _r, _cb, b, _l) in cd['rels']:
        dia.edges.append((a, b, None))
    _pos, _back, rank, col = layout(dia)

    colw = max(m[1] for m in metas.values()) + 190
    ypos = {}
    y = MARGIN
    for r in sorted(set(rank.values())):
        rh = max(metas[n][2] for n in dia.nodes if rank[n] == r) + 130
        ypos[r] = y + rh / 2
        y += rh
    P = {n: (MARGIN + col[n] * colw + colw / 2, ypos[rank[n]])
         for n in dia.nodes}
    W = int(MARGIN + (max(col.values()) + 1) * colw + 60)
    H = int(y + 60)

    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(60, yy), (W - 60, yy)], PAPER, 1)

    for (a, ca, rel, cb, b, lab) in cd['rels']:
        ax, ay = P[a]
        bx, by = P[b]
        pa = border_point(ax, ay, metas[a][1], metas[a][2], bx - ax, by - ay)
        pb = border_point(bx, by, metas[b][1], metas[b][2], ax - bx, ay - by)
        ld, rd, ds = rel_ends(rel)
        if ds:
            sk.dashed(pa, pb)
        else:
            sk.line([pa, pb])
        uml_deco(sk, pa, pb, ld)
        uml_deco(sk, pb, pa, rd)
        if ca:
            ux, uy, px, py = _unit(pa, pb)
            sk.text(pa[0] - ux * 24 + px * 18, pa[1] - uy * 24 + py * 18,
                    ca, 16, False, LABEL_TXT)
        if cb:
            ux, uy, px, py = _unit(pb, pa)
            sk.text(pb[0] - ux * 24 + px * 18, pb[1] - uy * 24 + py * 18,
                    cb, 16, False, LABEL_TXT)
        if lab:
            sk.label_pill((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2 - 26, lab)

    for n in classes:
        rows, w, h = metas[n]
        er_box(sk, P[n][0], P[n][1], n, rows, w, h)

    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- state diagrams

ST_TRANS_RE = re.compile(
    r'^\s*(\[\*\]|[\w\u00c0-\u00ff-]+)\s*-->\s*(\[\*\]|[\w\u00c0-\u00ff-]+)'
    r'\s*(?::\s*(.+?))?\s*$')
ST_ALIAS_RE = re.compile(
    r'^\s*state\s+"([^"]+)"\s+as\s+([\w\u00c0-\u00ff-]+)\s*(\{)?\s*$')
ST_STATE_RE = re.compile(r'^\s*state\s+([\w\u00c0-\u00ff-]+)\s*(\{)?\s*$')
ST_DESC_RE = re.compile(r'^\s*([\w\u00c0-\u00ff-]+)\s*:\s*(.+?)\s*$')


def parse_state(code):
    dia = Diagram('TD')
    aliases = {}
    cnt = [0, 0]

    def dot(kind):
        cnt[0 if kind == 'startdot' else 1] += 1
        nid = f'__{kind}{cnt[0 if kind == "startdot" else 1]}'
        dia.node(nid, kind, '')
        return nid

    def ensure(nid):
        if nid == '[*]':
            return None
        if nid not in dia.nodes:
            dia.node(nid, 'state', aliases.get(nid, nid))
        return nid

    for raw in code.splitlines():
        line = raw.strip()
        if (not line or line.startswith('%%')
                or line.startswith('stateDiagram') or line == '}'):
            continue
        m = re.match(r'^direction\s+(TB|TD|LR|RL)', line)
        if m:
            dia.direction = m.group(1)
            continue
        if line.startswith('note'):
            continue
        m = ST_ALIAS_RE.match(line)
        if m:
            aliases[m.group(2)] = m.group(1)
            dia.node(m.group(2), 'state', m.group(1))
            continue
        m = ST_TRANS_RE.match(line)
        if m:
            a, b, lab = m.groups()
            a = dot('startdot') if a == '[*]' else ensure(a)
            b = dot('enddot') if b == '[*]' else ensure(b)
            dia.edges.append((a, b, unquote(lab) if lab else None))
            continue
        m = ST_STATE_RE.match(line)
        if m:
            dia.node(m.group(1), 'state', aliases.get(m.group(1),
                                                     m.group(1)))
            continue
        m = ST_DESC_RE.match(line)
        if m and m.group(1) in dia.nodes:
            nd = dia.nodes[m.group(1)]
            nd['label'] = nd['label'] + '\n' + m.group(2)
            continue
    return dia if dia.edges else None


# ---------------------------------------------------------------- mindmap

MM_SHAPES = [
    (re.compile(r'^(?:[\w\u00c0-\u00ff-]+\s*)?\(\((.+)\)\)$'), 'circle'),
    (re.compile(r'^(?:[\w\u00c0-\u00ff-]+\s*)?\((.+)\)$'), 'stadium'),
    (re.compile(r'^(?:[\w\u00c0-\u00ff-]+\s*)?\[(.+)\]$'), 'rect'),
    (re.compile(r'^(?:[\w\u00c0-\u00ff-]+\s*)?\{\{(.+)\}\}$'), 'rect'),
    (re.compile(r'^(?:[\w\u00c0-\u00ff-]+\s*)?\)\)(.+)\(\($'), 'rect'),
]


def mm_shape(text):
    for pat, shp in MM_SHAPES:
        m = pat.match(text)
        if m:
            return m.group(1).strip(), shp
    return text, 'stadium'


def parse_mindmap(code):
    root = None
    stack = []
    for raw in code.splitlines():
        if (not raw.strip() or raw.strip().startswith('%%')
                or raw.strip() == 'mindmap'):
            continue
        indent = len(raw) - len(raw.lstrip())
        label, shape = mm_shape(raw.strip())
        node = {'label': label, 'shape': shape, 'children': [], 'depth': 0}
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stack:
            node['depth'] = stack[-1][1]['depth'] + 1
            stack[-1][1]['children'].append(node)
        elif root is None:
            root = node
        else:
            node['depth'] = 1
            root['children'].append(node)
        stack.append((indent, node))
    return root


def render_mindmap(root):
    metas = {}
    counter = [0]

    def measure(n):
        counter[0] += 1
        n['_id'] = counter[0]
        lines = wrap(n['label'], 26)
        w, h = dims(n['shape'], lines)
        metas[n['_id']] = (lines, w, h)
        for c in n['children']:
            measure(c)

    measure(root)
    depth_w = {}

    def dw(n):
        depth_w[n['depth']] = max(depth_w.get(n['depth'], 0),
                                  metas[n['_id']][1])
        for c in n['children']:
            dw(c)

    dw(root)
    xs = {}
    x = MARGIN
    for dep in sorted(depth_w):
        xs[dep] = x + depth_w[dep] / 2
        x += depth_w[dep] + 110
    slot = [MARGIN]

    def place(n):
        if not n['children']:
            h = metas[n['_id']][2]
            yy = slot[0] + h / 2
            slot[0] += h + 48
        else:
            ys = [place(c) for c in n['children']]
            yy = sum(ys) / len(ys)
        n['_y'] = yy
        return yy

    place(root)
    W = int(x + MARGIN)
    H = int(max(slot[0], root['_y'] * 2) + MARGIN)

    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(50, yy), (W - 50, yy)], PAPER, 1)

    def draw(n):
        cx, cy = xs[n['depth']], n['_y']
        lines, w, h = metas[n['_id']]
        for c in n['children']:
            ccx, ccy = xs[c['depth']], c['_y']
            cw = metas[c['_id']][1]
            a = (cx + w / 2, cy)
            b = (ccx - cw / 2, ccy)
            midx = (a[0] + b[0]) / 2
            sk.line([a, (midx, a[1]), (midx, b[1]), b])
            draw(c)
        sk.node(n['shape'], cx, cy, w, h,
                fill=PASTELS[n['depth'] % len(PASTELS)])
        off = -16 * (len(lines) - 1)
        for i, ln in enumerate(lines):
            sk.text(cx, cy + off + i * 32, ln)

    draw(root)
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- timeline

def parse_timeline(code):
    title = None
    periods = []
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line == 'timeline':
            continue
        m = re.match(r'^title\s+(.+)$', line)
        if m:
            title = m.group(1)
            continue
        if line.startswith('section'):
            continue
        if ':' in line:
            parts = [p.strip().strip('"') for p in line.split(':')]
            periods.append((parts[0], [p for p in parts[1:] if p]))
    return {'title': title, 'periods': periods} if periods else None


def render_timeline(tl):
    periods = tl['periods']
    n = len(periods)
    colw = 260
    W = 140 + n * colw + 140
    max_ev = max(len(ev) for _, ev in periods)
    axis_y = 200 + max_ev * 80
    H = axis_y + 130
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(50, yy), (W - 50, yy)], PAPER, 1)
    if tl['title']:
        sk.text(W / 2, 60, tl['title'], 30, True, TITLE_TXT)
    sk.line([(90, axis_y), (W - 90, axis_y)], INK, 5)
    sk.head((W - 88, axis_y), (W - 128, axis_y))
    for i, (per, evs) in enumerate(periods):
        x = 140 + i * colw + colw / 2
        r = 10
        sk.d.ellipse(((x - r) * S, (axis_y - r) * S, (x + r) * S,
                      (axis_y + r) * S), fill=INK)
        sk.text(x, axis_y + 36, per, 22, True)
        if evs:
            sk.line([(x, axis_y - r), (x, axis_y - 40 - (len(evs) - 1) * 80)],
                    INK2, 2)
        for j, ev in enumerate(evs):
            cy = axis_y - 78 - j * 80
            lines = wrap(ev, 20)
            w, h = dims('stadium', lines)
            sk.node('stadium', x, cy, w, h,
                    fill=PASTELS[(i + j) % len(PASTELS)])
            off = -16 * (len(lines) - 1)
            for k, ln in enumerate(lines):
                sk.text(x, cy + off + k * 32, ln, 18)
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- kanban

def parse_kanban(code):
    lines = [l for l in code.splitlines()
             if l.strip() and not l.strip().startswith('%%')
             and l.strip() != 'kanban']
    if not lines:
        return None
    base = min(len(l) - len(l.lstrip()) for l in lines)
    columns = []
    for raw in lines:
        indent = len(raw) - len(raw.lstrip())
        text = raw.strip()
        if text.startswith('@') or text in '{}':
            continue
        text = re.sub(r'^\[(.+)\]$', r'\1', text)
        if indent == base:
            columns.append((re.sub(r':\s*\[?\s*max\s*\].*$', '', text), []))
        elif columns:
            columns[-1][1].append(text)
    return {'columns': columns} if columns else None


def render_kanban(kb):
    cols = kb['columns']
    f_c = font(20)
    f_h = font(23, True)
    card_w = max(
        [f_c.getlength(c) for _n, cards in cols for c in cards] or [120])
    colw = int(max(card_w + 80, 260,
                   max((f_h.getlength(n) for n, _ in cols), default=0) + 60))
    gap = 34
    W = 90 + len(cols) * (colw + gap) + 60
    heights = []
    for _n, cards in cols:
        h = 90
        for c in cards:
            h += len(wrap(c, 26)) * 30 + 44
        heights.append(h)
    H = int(max(heights) + 90)
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(40, yy), (W - 40, yy)], PAPER, 1)
    for i, (name, cards) in enumerate(cols):
        x1 = 90 + i * (colw + gap)
        ph = heights[i]
        sk.poly([(x1, 70), (x1 + colw, 70), (x1 + colw, 70 + ph), (x1, 70 + ph)],
                PASTELS_LIGHT[i % len(PASTELS_LIGHT)])
        sk.poly([(x1 + 1, 71), (x1 + colw - 1, 71), (x1 + colw - 1, 70 + 54),
                 (x1 + 1, 70 + 54)], PASTELS[i % len(PASTELS)])
        sk.text(x1 + colw / 2, 70 + 28, name, 23, True)
        y = 70 + 54 + 22
        for c in cards:
            lines = wrap(c, 26)
            ch = len(lines) * 30 + 26
            sk.poly([(x1 + 18, y), (x1 + colw - 18, y), (x1 + colw - 18, y + ch),
                     (x1 + 18, y + ch)], '#1c2431')
            off = -15 * (len(lines) - 1)
            for k, ln in enumerate(lines):
                sk.text(x1 + colw / 2, y + ch / 2 + off + k * 30, ln, 20)
            y += ch + 18
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- pie

def parse_pie(code):
    title = None
    show = False
    data = []
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue
        m = re.match(r'^pie\b(.*)$', line)
        if m:
            rest = m.group(1)
            if 'showData' in rest:
                show = True
                rest = rest.replace('showData', '')
            m2 = re.search(r'title\s+(.+)$', rest)
            if m2:
                title = m2.group(1).strip()
            continue
        m = re.match(r'^"([^"]+)"\s*:\s*([\d.]+)$', line)
        if m:
            data.append((m.group(1), float(m.group(2))))
    return {'title': title, 'show': show, 'data': data} if data else None


def render_pie(pie):
    data = pie['data']
    total = sum(v for _l, v in data) or 1
    cx, cy, r = 330, 380, 250
    f_l = font(21)
    leg_w = max(f_l.getlength(l) + (f_l.getlength(f'  {v:g}') if pie['show']
                                    else 0) for l, v in data) + 90
    W = int(cx + r + 80 + leg_w + 60)
    H = int(cy + r + 80)
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(50, yy), (W - 50, yy)], PAPER, 1)
    if pie['title']:
        sk.text(W / 2, 56, pie['title'], 30, True, TITLE_TXT)
    box = ((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S)
    start = -90.0
    for i, (lab, v) in enumerate(data):
        ext = v / total * 360
        col = GIT_COLORS[i % len(GIT_COLORS)]
        sk.d.pieslice(box, start, start + ext, fill=col, outline=BG,
                      width=3 * S)
        mid = math.radians(start + ext / 2)
        if ext > 14:
            lx = cx + math.cos(mid) * r * 0.62
            ly = cy + math.sin(mid) * r * 0.62
            sk.text(lx, ly, f'{v / total * 100:.0f}%', 18, True, '#0d1117')
        start += ext
    sk.d.arc(box, 0, 360, fill=INK2, width=2 * S)
    lx = cx + r + 80
    ly = cy - len(data) * 24
    for i, (lab, v) in enumerate(data):
        col = GIT_COLORS[i % len(GIT_COLORS)]
        sk.d.rounded_rectangle((lx * S, (ly - 12) * S, (lx + 30) * S,
                                (ly + 12) * S), radius=5 * S, fill=col,
                               outline=INK, width=3 * S)
        t = f'{lab}  {v:g}' if pie['show'] else lab
        sk.d.text(sk.xy((lx + 44, ly)), t, font=f_l, fill=TEXT, anchor='lm')
        ly += 48
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- gitGraph

GIT_COMMIT_RE = re.compile(
    r'^\s*commit\b(.*?)$')
GIT_KV_RE = re.compile(r'(id|tag|type)\s*:\s*"([^"]*)"')


def parse_git(code):
    branches = {'main': 0}
    events = []
    cur = 'main'
    for raw in code.splitlines():
        line = raw.strip()
        if (not line or line.startswith('%%')
                or line.startswith('gitGraph')):
            continue
        m = re.match(r'^branch\s+([\w\u00c0-\u00ff/-]+)', line)
        if m:
            name = m.group(1)
            branches.setdefault(name, len(branches))
            events.append(('branch', name, cur))
            continue
        m = re.match(r'^checkout\s+([\w\u00c0-\u00ff/-]+)', line)
        if m:
            cur = m.group(1)
            branches.setdefault(cur, len(branches))
            continue
        m = re.match(r'^merge\s+([\w\u00c0-\u00ff/-]+)', line)
        if m:
            events.append(('merge', m.group(1), cur))
            continue
        m = GIT_COMMIT_RE.match(line)
        if m:
            kv = dict(GIT_KV_RE.findall(m.group(1)))
            events.append(('commit', cur, kv.get('id', ''),
                           kv.get('tag', '')))
            continue
        # cherry-pick u.ae. ignorieren
    return {'branches': branches, 'events': events} if events else None


def render_git(git):
    branches = git['branches']
    x0, dx = 190, 108
    row_y = {n: 150 + i * 96 for i, (n, _r) in enumerate(
        sorted(branches.items(), key=lambda kv: kv[1]))}
    W = 0
    commits = []
    merges = []
    starts = {}
    heads = {n: None for n in branches}
    cur = 'main'
    nx = [0]

    def next_x():
        nx[0] += 1
        return x0 + nx[0] * dx

    for ev in git['events']:
        if ev[0] == 'branch':
            _e, name, src = ev
            starts[name] = heads.get(src)
        elif ev[0] == 'commit':
            _e, br, cid, tag = ev
            x = next_x()
            commits.append((x, br, cid, tag))
            heads[br] = x
            cur = br
        elif ev[0] == 'merge':
            _e, src, dst = ev
            x = next_x()
            merges.append((heads.get(src), src, x, dst))
            commits.append((x, dst, '', ''))
            heads[dst] = x
            cur = dst
    last_x = x0 + (nx[0] + 1) * dx
    W = int(last_x + 60)
    H = int(max(row_y.values()) + 110)
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(40, yy), (W - 40, yy)], PAPER, 1)
    colors = {n: GIT_COLORS[i % len(GIT_COLORS)]
              for i, n in enumerate(sorted(branches, key=branches.get))}
    # Branch-Linien und Labels
    for name, y in row_y.items():
        x1 = starts.get(name) or 130
        x2 = heads.get(name) or x1
        sk.line([(x1, y), (x2 + 26, y)], colors[name], 6)
        sk.label_pill(70, y, name)
    # Merge-Konnektoren
    for sx, src, x, dst in merges:
        if sx is None:
            continue
        y1, y2 = row_y[src], row_y[dst]
        sk.line([(sx, y1), (x - 30, y1), (x - 30, y2), (x, y2)],
                colors[src], 4)
    # Commits
    for x, br, cid, tag in commits:
        y = row_y[br]
        r = 12
        sk.d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S),
                     fill=colors[br], outline=INK, width=3 * S)
        sk.d.ellipse(((x - r + 3) * S, (y - r + 3) * S, (x + r - 3) * S,
                      (y + r - 3) * S), outline=INK2, width=2 * S)
        if cid:
            sk.text(x, y - 28, cid, 15, False, LABEL_TXT)
        if tag:
            sk.text(x, y + 28, tag, 15, True, '#f47067')
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- gantt

GANTT_SKIP = ('dateformat', 'axisformat', 'excludes', 'todaymarker',
              'inclusiveenddates', 'tickinterval', 'weekday', 'outputformat')


def _parse_date(s):
    import datetime as _dt
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d'):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def parse_gantt(code):
    title = None
    sections = []          # [(name, [tasks])]
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line == 'gantt':
            continue
        if line.lower().split()[0] in GANTT_SKIP if line.split() else False:
            continue
        m = re.match(r'^title\s+(.+)$', line)
        if m:
            title = m.group(1)
            continue
        m = re.match(r'^section\s+(.+)$', line)
        if m:
            sections.append((m.group(1), []))
            continue
        m = re.match(r'^(.+?)\s*:\s*(.+)$', line)
        if m:
            name, spec = m.group(1).strip(), m.group(2)
            tokens = [t.strip() for t in spec.split(',') if t.strip()]
            tags = {t for t in tokens
                    if t in ('done', 'active', 'crit', 'milestone')}
            tid = after = start = dur = end = None
            for t in tokens:
                if t in tags:
                    continue
                if t.startswith('after'):
                    parts = t.split()
                    after = parts[1] if len(parts) > 1 else None
                elif re.match(r'^\d+[dwh]$', t):
                    dur = t
                elif _parse_date(t):
                    if start is None:
                        start = t
                    else:
                        end = t
                elif tid is None and start is None:
                    tid = t
            if not sections:
                sections.append(('', []))
            sections[-1][1].append({'name': name, 'tags': tags, 'id': tid,
                                    'after': after, 'start': start,
                                    'dur': dur, 'end': end})
    return {'title': title, 'sections': sections} if sections else None


def render_gantt(g):
    import datetime as _dt
    tasks = []
    ends = {}
    for sname, tl in g['sections']:
        for t in tl:
            if t['after'] and t['after'] in ends:
                s = ends[t['after']]
            elif t['start']:
                s = _parse_date(t['start'])
            else:
                s = None
            if s is None:
                s = min(ends.values()) if ends else _dt.date.today()
            if t['end']:
                e = _parse_date(t['end'])
            else:
                days = 1
                if t['dur']:
                    n = int(t['dur'][:-1])
                    days = n * 7 if t['dur'].endswith('w') else n
                e = s + _dt.timedelta(days=days)
            t['s'], t['e'] = s, e
            if t['id']:
                ends[t['id']] = e
            tasks.append((sname, t))
    if not tasks:
        return None
    d0 = min(t['s'] for _s, t in tasks)
    d1 = max(t['e'] for _s, t in tasks)
    days = max((d1 - d0).days + 1, 1)
    left = 300
    ppd = min(30, max(8, 1500 // days))
    plot_w = days * ppd
    W = left + plot_w + 100
    row_h = 46
    sec_h = 44
    top = 130
    nrows = len(tasks)
    nsec = sum(1 for _n, tl in g['sections'] if tl) + \
        sum(1 for n, _t in g['sections'] if n)
    H = top + nrows * row_h + len(g['sections']) * sec_h + 90
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(40, yy), (W - 40, yy)], PAPER, 1)
    if g['title']:
        sk.text(W / 2, 56, g['title'], 30, True, TITLE_TXT)

    def X(d):
        return left + (d - d0).days * ppd

    # Achse und Gitter
    axis_y = top - 30
    sk.line([(left, axis_y), (left + plot_w, axis_y)], INK2, 2)
    step = max(1, math.ceil(days / 10))
    d = d0
    while d <= d1:
        x = X(d)
        sk.dashed((x, axis_y), (x, H - 60), dash=6, gap=8, c='#21262d', w=1)
        sk.text(x, axis_y - 18, d.strftime('%d.%m.'), 15, False, LABEL_TXT)
        d += _dt.timedelta(days=step)
    # Zeilen
    y = top
    BAR = {'done': '#238636', 'active': '#1f6feb', 'crit': '#da3633'}
    for sname, tl in g['sections']:
        if sname:
            sk.poly([(70, y), (W - 70, y + sec_h - 10), (W - 70, y),
                     (70, y + sec_h - 10)], PASTELS_LIGHT[1])
            sk.d.text(sk.xy((86, y + (sec_h - 10) / 2)), sname,
                      font=font(20, True), fill=TEXT, anchor='lm')
            y += sec_h
        for t in tl:
            sk.d.text(sk.xy((86, y + row_h / 2)), t['name'], font=font(18),
                      fill=TEXT, anchor='lm')
            x1, x2 = X(t['s']), X(t['e'])
            if 'milestone' in t['tags']:
                cx, cy = x1, y + row_h / 2
                sk.poly([(cx, cy - 13), (cx + 13, cy), (cx, cy + 13),
                         (cx - 13, cy)], '#e3b341')
            else:
                fill = next((BAR[k] for k in ('crit', 'done', 'active')
                             if k in t['tags']), '#9e6a03')
                by1, by2 = y + 10, y + row_h - 10
                b = (x1 * S, by1 * S, max(x2, x1 + 16) * S, by2 * S)
                sk.d.rounded_rectangle(b, radius=10 * S, fill=fill,
                                       outline=INK, width=3 * S)
                sk.d.rounded_rectangle((b[0] + 2 * S, b[1] + S, b[2] - S,
                                        b[3] + 2 * S), radius=10 * S,
                                       outline=INK2, width=1 * S)
            y += row_h
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- quadrantChart

def parse_quadrant(code):
    q = {'title': None, 'x': ('', ''), 'y': ('', ''),
         'quads': {}, 'points': []}
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line == 'quadrantChart':
            continue
        m = re.match(r'^title\s+(.+)$', line)
        if m:
            q['title'] = m.group(1)
            continue
        m = re.match(r'^x-axis\s+(.+?)\s*-->\s*(.+)$', line)
        if m:
            q['x'] = (m.group(1).strip(), m.group(2).strip())
            continue
        m = re.match(r'^y-axis\s+(.+?)\s*-->\s*(.+)$', line)
        if m:
            q['y'] = (m.group(1).strip(), m.group(2).strip())
            continue
        m = re.match(r'^quadrant-([1-4])\s+(.+)$', line)
        if m:
            q['quads'][int(m.group(1))] = m.group(2).strip()
            continue
        m = re.match(r'^(.+?)\s*:\s*\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]\s*$',
                     line)
        if m:
            q['points'].append((m.group(1).strip(), float(m.group(2)),
                                float(m.group(3))))
    return q if q['points'] else None


def render_quadrant(q):
    plot = 900
    x0, y0 = 200, 150
    W = x0 + plot + 120
    H = y0 + plot + 150
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(40, yy), (W - 40, yy)], PAPER, 1)
    if q['title']:
        sk.text(W / 2, 56, q['title'], 30, True, TITLE_TXT)
    # Quadranten 1=ro, 2=lo, 3=lu, 4=ru
    fills = {2: '#131c27', 1: '#12211a', 3: '#221716', 4: '#211c10'}
    half = plot / 2
    for quad, (qx, qy) in {2: (x0, y0), 1: (x0 + half, y0),
                           3: (x0, y0 + half),
                           4: (x0 + half, y0 + half)}.items():
        sk.d.rectangle((qx * S, qy * S, (qx + half) * S, (qy + half) * S),
                       fill=fills[quad])
    # Rahmen und Mittellinien
    sk.poly([(x0, y0), (x0 + plot, y0), (x0 + plot, y0 + plot),
             (x0, y0 + plot)], BG)
    sk.d.rectangle((x0 * S, y0 * S, (x0 + plot) * S, (y0 + plot) * S),
                   outline=INK, width=4 * S)
    sk.line([(x0 + half, y0), (x0 + half, y0 + plot)], INK2, 2)
    sk.line([(x0, y0 + half), (x0 + plot, y0 + half)], INK2, 2)
    # Quadranten-Labels
    for quad, (qx, qy) in {2: (x0, y0), 1: (x0 + half, y0),
                           3: (x0, y0 + half),
                           4: (x0 + half, y0 + half)}.items():
        if quad in q['quads']:
            sk.text(qx + half / 2, qy + half / 2, q['quads'][quad], 22, True,
                    '#6e7681')
    # Achsenbeschriftungen
    sk.text(x0 - 20, y0 + plot + 24, q['x'][0], 19, False, LABEL_TXT)
    sk.text(x0 + plot + 20, y0 + plot + 24, q['x'][1], 19, False, LABEL_TXT)
    sk.text(x0 - 24, y0 + plot - 10, q['y'][0], 19, False, LABEL_TXT)
    sk.text(x0 - 24, y0 + 10, q['y'][1], 19, False, LABEL_TXT)
    # Punkte
    for i, (name, px_, py_) in enumerate(q['points']):
        cx = x0 + px_ * plot
        cy = y0 + (1 - py_) * plot
        r = 9
        col = GIT_COLORS[i % len(GIT_COLORS)]
        sk.d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S),
                     fill=col, outline=INK, width=3 * S)
        sk.text(cx, cy - 22, name, 18, True)
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- xychart

def _split_list(s):
    s = s.strip()
    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1]
    return [t.strip().strip('"').strip("'") for t in s.split(',') if t.strip()]


def parse_xy(code):
    cfg = {'title': None, 'xcats': None, 'ymin': 0.0, 'ymax': 100.0,
           'ylabel': '', 'series': []}
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line.startswith('xychart'):
            continue
        m = re.match(r'^title\s+(.+)$', line)
        if m:
            cfg['title'] = unquote(m.group(1))
            continue
        m = re.match(r'^x-axis\s+(.+)$', line)
        if m:
            body = m.group(1)
            m2 = re.match(r'^([\-\d.]+)\s*-->\s*([\-\d.]+)', body)
            if m2:
                a, b = float(m2.group(1)), float(m2.group(2))
                cfg['xcats'] = [f'{v:g}' for v in range(int(a), int(b) + 1)]
            else:
                cfg['xcats'] = _split_list(body)
            continue
        m = re.match(r'^y-axis\s+(?:"([^"]*)")?\s*([\-\d.]+)\s*-->\s*'
                     r'([\-\d.]+)', line)
        if m:
            cfg['ylabel'] = m.group(1) or ''
            cfg['ymin'] = float(m.group(2))
            cfg['ymax'] = float(m.group(3))
            continue
        m = re.match(r'^(bar|line)\s*(\[.*\])\s*$', line)
        if m:
            try:
                vals = [float(v) for v in _split_list(m.group(2))]
            except ValueError:
                continue
            cfg['series'].append((m.group(1), vals))
    return cfg if cfg['series'] and cfg['xcats'] else None


def render_xy(cfg):
    cats = cfg['xcats']
    n = len(cats)
    catw = max(110, int(1400 / max(n, 1)))
    x0, y0 = 190, 150
    plot_w, plot_h = n * catw, 560
    W = x0 + plot_w + 100
    H = y0 + plot_h + 130
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(40, yy), (W - 40, yy)], PAPER, 1)
    if cfg['title']:
        sk.text(W / 2, 56, cfg['title'], 30, True, TITLE_TXT)
    ymin, ymax = cfg['ymin'], cfg['ymax']
    span = (ymax - ymin) or 1

    def Y(v):
        return y0 + plot_h - (v - ymin) / span * plot_h

    # y-Gitter und Labels
    for i in range(6):
        v = ymin + span * i / 5
        y = Y(v)
        sk.dashed((x0, y), (x0 + plot_w, y), dash=6, gap=8, c='#21262d', w=1)
        sk.text(x0 - 18, y, f'{v:g}', 16, False, LABEL_TXT)
    if cfg['ylabel']:
        sk.text(x0 - 70, y0 + plot_h / 2, cfg['ylabel'], 18, True, LABEL_TXT)
    # Achsen
    sk.line([(x0, y0 + plot_h), (x0 + plot_w, y0 + plot_h)], INK, 4)
    sk.line([(x0, y0), (x0, y0 + plot_h)], INK, 4)
    for i, c in enumerate(cats):
        sk.text(x0 + i * catw + catw / 2, y0 + plot_h + 26, c, 17, False,
                LABEL_TXT)
    bars = [s for s in cfg['series'] if s[0] == 'bar']
    lines_ = [s for s in cfg['series'] if s[0] == 'line']
    nb = max(len(bars), 1)
    for bi, (_k, vals) in enumerate(bars):
        bw = catw * 0.55 / nb
        for i, v in enumerate(vals[:n]):
            cx = x0 + i * catw + catw / 2 + (bi - (nb - 1) / 2) * bw
            b = ((cx - bw / 2 + 3) * S, Y(v) * S, (cx + bw / 2 - 3) * S,
                 (y0 + plot_h) * S)
            sk.d.rectangle(b, fill=PASTELS[bi % len(PASTELS)], outline=INK,
                           width=3 * S)
            sk.d.line([(b[0] + 2 * S, b[1] + 2 * S), (b[2] - 2 * S,
                       b[1] + 2 * S)], fill=INK2, width=1 * S)
    for li, (_k, vals) in enumerate(lines_):
        pts = [(x0 + i * catw + catw / 2, Y(v))
               for i, v in enumerate(vals[:n])]
        sk.line(pts, GIT_COLORS[li % len(GIT_COLORS)], 5)
        for (px, py) in pts:
            r = 7
            sk.d.ellipse(((px - r) * S, (py - r) * S, (px + r) * S,
                          (py + r) * S), fill=BG,
                         outline=GIT_COLORS[li % len(GIT_COLORS)],
                         width=4 * S)
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- journey

def parse_journey(code):
    title = None
    sections = []
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line == 'journey':
            continue
        m = re.match(r'^title\s+(.+)$', line)
        if m:
            title = m.group(1)
            continue
        m = re.match(r'^section\s+(.+)$', line)
        if m:
            sections.append((m.group(1).strip(), []))
            continue
        m = re.match(r'^(.+?)\s*:\s*(\d+)\s*(?::\s*(.+))?$', line)
        if m:
            if not sections:
                sections.append(('', []))
            actors = ([a.strip() for a in m.group(3).split(',')]
                      if m.group(3) else [])
            sections[-1][1].append((m.group(1).strip(), int(m.group(2)),
                                    actors))
    return {'title': title, 'sections': sections} if sections else None


def render_journey(j):
    cardw, cardh, gap = 250, 150, 30
    max_tasks = max((len(t) for _s, t in j['sections']), default=1)
    W = 260 + max_tasks * (cardw + gap) + 90
    sec_h = 230
    H = 120 + len(j['sections']) * sec_h + 60
    sk = Sketch(W, H)
    for yy in range(45, H, 31):
        sk.line([(40, yy), (W - 40, yy)], PAPER, 1)
    if j['title']:
        sk.text(W / 2, 56, j['title'], 30, True, TITLE_TXT)
    y = 130
    for si, (sname, tasks) in enumerate(j['sections']):
        col = PASTELS[si % len(PASTELS)]
        sk.poly([(70, y), (230, y), (230, y + sec_h - 24), (70, y + sec_h - 24)],
                col)
        for k, ln in enumerate(wrap(sname, 12)):
            sk.text(150, y + sec_h / 2 - 24 + k * 30, ln, 21, True)
        x = 260
        for tname, score, actors in tasks:
            sk.poly([(x, y + 18), (x + cardw, y + 18), (x + cardw, y + 178),
                     (x, y + 178)], SURFACE)
            lines = wrap(tname, 20)[:2]
            off = -16 * (len(lines) - 1)
            for k, ln in enumerate(lines):
                sk.text(x + cardw / 2, y + 60 + off + k * 30, ln, 20)
            # Bewertungspunkte
            sc_col = ('#f47067' if score <= 2 else
                      '#e3b341' if score == 3 else '#56d364')
            for dot in range(5):
                dcx = x + cardw / 2 + (dot - 2) * 26
                dcy = y + 116
                if dot < score:
                    sk.d.ellipse(((dcx - 8) * S, (dcy - 8) * S, (dcx + 8) * S,
                                  (dcy + 8) * S), fill=sc_col, outline=INK,
                                 width=2 * S)
                else:
                    sk.d.ellipse(((dcx - 8) * S, (dcy - 8) * S, (dcx + 8) * S,
                                  (dcy + 8) * S), outline='#4c5a6b',
                                 width=2 * S)
            if actors:
                sk.text(x + cardw / 2, y + 152, ', '.join(actors), 15, False,
                        LABEL_TXT)
            x += cardw + gap
        y += sec_h
    return sk.im.resize((W * S, H * S), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- cli

MERMAID_RE = re.compile(r'```mermaid\s*\n(.*?)```', re.S)


DETECT = [
    ('er', r'erDiagram\b'),
    ('seq', r'sequenceDiagram\b'),
    ('class', r'classDiagram\b'),
    ('state', r'stateDiagram(-v2)?\b'),
    ('mindmap', r'mindmap\b'),
    ('timeline', r'timeline\b'),
    ('kanban', r'kanban\b'),
    ('pie', r'pie\b'),
    ('git', r'gitGraph\b'),
    ('gantt', r'gantt\b'),
    ('quadrant', r'quadrantChart\b'),
    ('xy', r'xychart(-beta)?\b'),
    ('journey', r'journey\b'),
    ('flow', r'(flowchart|graph)\b'),
]

def detect_type(code):
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue
        for kind, pat in DETECT:
            if re.match(pat, line):
                return kind
        return None
    return None


def _run(kind, code):
    if kind == 'flow':
        dia = parse_mermaid(code)
        return render(dia) if dia else None
    if kind == 'er':
        er = parse_er(code)
        return render_er(er) if er else None
    if kind == 'seq':
        seq = parse_seq(code)
        return render_seq(seq) if seq else None
    if kind == 'class':
        cd = parse_class(code)
        return render_class(cd) if cd else None
    if kind == 'state':
        dia = parse_state(code)
        return render(dia) if dia else None
    if kind == 'mindmap':
        mm = parse_mindmap(code)
        return render_mindmap(mm) if mm else None
    if kind == 'timeline':
        tl = parse_timeline(code)
        return render_timeline(tl) if tl else None
    if kind == 'kanban':
        kb = parse_kanban(code)
        return render_kanban(kb) if kb else None
    if kind == 'pie':
        p = parse_pie(code)
        return render_pie(p) if p else None
    if kind == 'git':
        g = parse_git(code)
        return render_git(g) if g else None
    if kind == 'gantt':
        g = parse_gantt(code)
        return render_gantt(g) if g else None
    if kind == 'quadrant':
        q = parse_quadrant(code)
        return render_quadrant(q) if q else None
    if kind == 'xy':
        c = parse_xy(code)
        return render_xy(c) if c else None
    if kind == 'journey':
        j = parse_journey(code)
        return render_journey(j) if j else None
    return None


def process_file(md_path, out_dir):
    text = md_path.read_text(encoding='utf-8')
    blocks = MERMAID_RE.findall(text)
    made = []
    for i, code in enumerate(blocks, 1):
        kind = detect_type(code)
        if kind is None:
            print(f'  uebersprungen (nicht unterstuetzter Diagrammtyp): Block {i}')
            continue
        try:
            img = _run(kind, code)
        except Exception as exc:
            print(f'  uebersprungen (Fehler in Block {i}: {exc})')
            continue
        if img is None:
            print(f'  uebersprungen (keine verwertbaren Elemente): Block {i}')
            continue
        name = f'{md_path.stem}-diagramm-{i}.png'
        out = (out_dir / name) if out_dir else (md_path.parent / name)
        img.save(out, optimize=True)
        with Image.open(out) as check:
            check.verify()
        made.append(out)
        print(f'  erstellt: {out}')
    return made


def main(argv):
    out_dir = None
    skip = set()
    if '--out' in argv:
        i = argv.index('--out')
        out_dir = Path(argv[i + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        skip = {i, i + 1}
    args = [a for i, a in enumerate(argv) if i not in skip and not a.startswith('--')]
    if not args:
        print(__doc__)
        return 1
    files = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            files.extend(sorted(p.glob('*.md')))
        elif p.is_file():
            files.append(p)
        else:
            print(f'nicht gefunden: {p}')
    if not files:
        print('Keine Markdown-Dateien gefunden.')
        return 1
    total = 0
    for f in files:
        print(f'{f}:')
        total += len(process_file(f, out_dir))
    print(f'Fertig – {total} Bild(er) erzeugt.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
