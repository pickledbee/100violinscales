"""Small violin-notation engraver for ReportLab (treble clef, single staff)."""
import math
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

G = '/usr/share/fonts/truetype/google-fonts/ofl/'
pdfmetrics.registerFont(TTFont('Music', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('MusicB', '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('MusicBI', '/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf'))
pdfmetrics.registerFont(TTFont('MusicI', '/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf'))
for n, f in [('Serif', 'crimsontext/CrimsonText-Regular.ttf'), ('SerifB', 'crimsontext/CrimsonText-Bold.ttf'),
             ('SerifI', 'crimsontext/CrimsonText-Italic.ttf'), ('SerifSB', 'crimsontext/CrimsonText-SemiBold.ttf'),
             ('SerifBI', 'crimsontext/CrimsonText-BoldItalic.ttf'),
             ('Sans', 'firasans/FiraSans-Regular.ttf'), ('SansB', 'firasans/FiraSans-Bold.ttf'),
             ('SansM', 'firasans/FiraSans-Medium.ttf'), ('SansSB', 'firasans/FiraSans-SemiBold.ttf'),
             ('SansI', 'firasans/FiraSans-Italic.ttf'), ('SansL', 'firasans/FiraSans-Light.ttf')]:
    pdfmetrics.registerFont(TTFont(n, G + f))

LETTERS = 'CDEFGAB'
SEMI = [0, 2, 4, 5, 7, 9, 11]
SHARP_ORDER = [(3, 38), (0, 35), (4, 39), (1, 36), (5, 33), (2, 37), (6, 34)]  # (letter, d)
FLAT_ORDER = [(6, 34), (2, 37), (5, 33), (1, 36), (4, 32), (0, 35), (3, 31)]


class P:
    """Pitch: letter index 0-6 (C..B), alter (-1,0,1), octave."""
    def __init__(s, l, a, o):
        s.l, s.a, s.o = l, a, o
    @property
    def d(s): return s.o * 7 + s.l
    @property
    def semi(s): return s.o * 12 + SEMI[s.l] + s.a
    def up(s, semis):
        l, o = s.l + 1, s.o
        if l == 7: l, o = 0, o + 1
        target = s.semi + semis
        a = target - (o * 12 + SEMI[l])
        return P(l, a, o)
    def down(s, semis):
        l, o = s.l - 1, s.o
        if l < 0: l, o = 6, o - 1
        target = s.semi - semis
        a = target - (o * 12 + SEMI[l])
        return P(l, a, o)
    def name(s):
        return LETTERS[s.l] + {-1: 'b', 0: '', 1: '#', 2: 'x', -2: 'bb'}[s.a] + str(s.o)
    def __repr__(s): return s.name()


def parse(n):
    l = LETTERS.index(n[0]); rest = n[1:]; a = 0
    while rest and rest[0] in 'b#':
        a += 1 if rest[0] == '#' else -1; rest = rest[1:]
    return P(l, a, int(rest))


class Note:
    def __init__(s, p, dur, **k):
        s.p, s.dur = p, dur           # dur in ticks, 12 = quarter
        s.art = k.get('art', [])      # 'stacc','ten','acc','wedge'
        s.finger = k.get('finger')
        s.bow = k.get('bow')          # 'down'/'up'
        s.pos = k.get('pos')          # position label text
        s.text = k.get('text')        # expression below
        s.dyn = k.get('dyn')
        s.trip = k.get('trip')        # triplet group id
        s.string = k.get('string')


DUR_W = {3: 17.5, 4: 17.0, 6: 18.0, 9: 20.0, 12: 21, 18: 24, 24: 27, 36: 30, 48: 32}


class Ops:
    def __init__(s): s.ops = []; s.ymin = 1e9; s.ymax = -1e9
    def _y(s, *ys):
        for y in ys: s.ymin = min(s.ymin, y); s.ymax = max(s.ymax, y)
    def line(s, x1, y1, x2, y2, w=0.8): s.ops.append(('line', x1, y1, x2, y2, w)); s._y(y1, y2)
    def head(s, x, y, rx, ry, filled, ang=-20): s.ops.append(('head', x, y, rx, ry, filled, ang)); s._y(y - ry, y + ry)
    def text(s, x, y, t, font, size, align='l', track=True):
        s.ops.append(('text', x, y, t, font, size, align))
        if track: s._y(y - size * 0.25, y + size * 0.75)
    def poly(s, pts, fill=True, w=0.8): s.ops.append(('poly', pts, fill, w)); s._y(*[p[1] for p in pts])
    def slur(s, p0, p1, p2, p3, th):
        s.ops.append(('slur', p0, p1, p2, p3, th)); s._y(p0[1], p3[1], 0.25 * p0[1] + 0.75 * p1[1], 0.75 * p2[1] + 0.25 * p3[1])
    def dot(s, x, y, r): s.ops.append(('dot', x, y, r)); s._y(y - r, y + r)

    def render(s, c, ox, oy, color=(0, 0, 0), bg=(1, 1, 1)):
        s.bg = bg
        c.saveState(); c.setFillColorRGB(*color); c.setStrokeColorRGB(*color)
        c.setLineCap(0)
        for op in s.ops:
            k = op[0]
            if k == 'line':
                _, x1, y1, x2, y2, w = op; c.setLineWidth(w); c.line(ox + x1, oy + y1, ox + x2, oy + y2)
            elif k == 'head':
                _, x, y, rx, ry, filled, ang = op
                c.saveState(); c.translate(ox + x, oy + y); c.rotate(ang)
                c.ellipse(-rx, -ry, rx, ry, stroke=0, fill=1)
                if not filled:
                    c.rotate(-ang); c.rotate(-38 if ang < -15 else 55)
                    c.setFillColorRGB(*s.bg)
                    if ang < -15: c.ellipse(-rx * 0.62, -ry * 0.42, rx * 0.62, ry * 0.42, stroke=0, fill=1)
                    else: c.ellipse(-ry * 0.55, -rx * 0.42, ry * 0.55, rx * 0.42, stroke=0, fill=1)
                    c.setFillColorRGB(*color)
                c.restoreState()
            elif k == 'text':
                _, x, y, t, font, size, align = op
                c.setFont(font, size)
                if align == 'c': c.drawCentredString(ox + x, oy + y, t)
                elif align == 'r': c.drawRightString(ox + x, oy + y, t)
                else: c.drawString(ox + x, oy + y, t)
            elif k == 'poly':
                _, pts, fill, w = op
                p = c.beginPath(); p.moveTo(ox + pts[0][0], oy + pts[0][1])
                for q in pts[1:]: p.lineTo(ox + q[0], oy + q[1])
                if fill: p.close(); c.drawPath(p, stroke=0, fill=1)
                else: c.setLineWidth(w); c.drawPath(p, stroke=1, fill=0)
            elif k == 'slur':
                _, p0, p1, p2, p3, th = op
                p = c.beginPath(); p.moveTo(ox + p0[0], oy + p0[1])
                p.curveTo(ox + p1[0], oy + p1[1], ox + p2[0], oy + p2[1], ox + p3[0], oy + p3[1])
                p.curveTo(ox + p2[0], oy + p2[1] + th, ox + p1[0], oy + p1[1] + th, ox + p0[0], oy + p0[1])
                p.close(); c.drawPath(p, stroke=0, fill=1)
            elif k == 'dot':
                _, x, y, r = op; c.circle(ox + x, oy + y, r, stroke=0, fill=1)
        c.restoreState()


def keysig_alters(tonic, mode):
    """Return dict letter->alter and count (+sharps / -flats)."""
    if mode == 'major':
        steps = [2, 2, 1, 2, 2, 2]
    else:
        steps = [2, 1, 2, 2, 1, 2]
    p = P(tonic.l, tonic.a, 4); al = {p.l: p.a}
    for st in steps:
        p = p.up(st); al[p.l] = p.a
    n = sum(1 for v in al.values() if v == 1) - sum(1 for v in al.values() if v == -1)
    return al, n


class Staff:
    """Engrave a list of Notes with meter onto Ops; handles systems."""
    def __init__(s, sp=6.0):
        s.sp = sp

    def y(s, d): return (d - 30) * s.sp / 2.0

    # ---------- glyph helpers
    def clef(s, o, x):
        sp = s.sp
        o.text(x, -0.05 * sp, '\U0001D11E', 'Music', sp * 5.9, track=False)
        o._y(-1.9 * sp, 5.4 * sp)
        return x + sp * 3.7

    def acc(s, o, x, d, a):
        g = {1: '♯', -1: '♭', 0: '♮'}[a]
        sp = s.sp; yy = s.y(d)
        if a == -1: o.text(x, yy - 0.38 * sp, g, 'Music', sp * 2.9, track=False)
        else: o.text(x, yy - 0.57 * sp, g, 'Music', sp * 2.9, track=False)

    def keysig(s, o, x, n):
        sp = s.sp
        order = SHARP_ORDER if n > 0 else FLAT_ORDER
        for i in range(abs(n)):
            s.acc(o, x, order[i][1], 1 if n > 0 else -1); x += sp * 1.05
        return x + (sp * 0.8 if n else sp * 0.2)

    def timesig(s, o, x, num, den):
        sp = s.sp
        o.text(x + sp * 0.9, s.y(34) + 0.15 * sp, str(num), 'MusicB', sp * 2.75, 'c', track=False)
        o.text(x + sp * 0.9, s.y(30) + 0.15 * sp, str(den), 'MusicB', sp * 2.75, 'c', track=False)
        return x + sp * 2.6

    def bow_mark(s, o, x, y, kind):
        sp = s.sp
        if kind == 'down':
            w, h = sp * 1.05, sp * 0.9
            o.poly([(x - w / 2, y), (x - w / 2, y + h), (x + w / 2, y + h), (x + w / 2, y),
                    (x + w / 2 - 0.16 * sp, y), (x + w / 2 - 0.16 * sp, y + h - 0.32 * sp),
                    (x - w / 2 + 0.16 * sp, y + h - 0.32 * sp), (x - w / 2 + 0.16 * sp, y)])
            return y + h
        else:
            w, h = sp * 0.95, sp * 1.25
            o.line(x - w / 2, y + h, x, y, 0.75); o.line(x, y, x + w / 2, y + h, 0.75)
            return y + h

    # ---------- main
    def engrave(s, notes, meter, key_n, keyal, width, first_timesig=True, slurs=(), hairpins=(),
                beam_unit=None, final_bar=True, start_x=0.0):
        """Returns list of Ops (one per system)."""
        sp = s.sp
        num, den = meter
        bar_ticks = num * (48 // den)
        # onsets & bars
        t = 0; bars = [[]]
        for i, n in enumerate(notes):
            n.idx = i; n.onset = t
            if t >= bar_ticks * len(bars) - 1e-9 and bars[-1]:
                bars.append([])
            bars[-1].append(n); t += n.dur
        for b, bar in enumerate(bars):
            for n in bar: n.bar = b; n.bonset = n.onset - b * bar_ticks
        # beam groups
        def bu(n):
            if beam_unit: return beam_unit
            if den == 8: return 18
            if n.dur == 6 and num in (4, 2) and den == 4: return 24
            return 12
        gid = 0; prev = None
        for n in notes:
            if n.dur >= 12: n.beam = None; prev = None; continue
            key = (n.bar, n.bonset // bu(n))
            if prev is not None and prev[0] == key: n.beam = prev[1]
            else:
                gid += 1; n.beam = gid
            prev = (key, n.beam)
        # accidentals
        for bar in bars:
            state = {}
            for n in bar:
                k = (n.p.l, n.p.o); cur = state.get(k, keyal.get(n.p.l, 0))
                n.showacc = None if cur == n.p.a else n.p.a
                state[k] = n.p.a
        # widths
        for n in notes:
            n.w = DUR_W[n.dur] * sp / 6.0 + (sp * 1.2 if n.showacc is not None else 0)
        # systems
        head_w0 = 3.7 * sp + abs(key_n) * 1.05 * sp + 1.0 * sp
        bws = [sum(n.w for n in bar) + sp * 1.6 for bar in bars]
        ts_w = 2.6 * sp if first_timesig else 0
        from itertools import combinations
        best = None
        for k in range(1, len(bars) + 1):
            for cuts in combinations(range(1, len(bars)), k - 1):
                parts = []; prevc = 0
                for cc in list(cuts) + [len(bars)]:
                    parts.append((prevc, cc)); prevc = cc
                ws = [sum(bws[a:b]) + head_w0 + (ts_w if a == 0 else 0) for a, b in parts]
                if max(ws) > width: continue
                score = max(ws) - min(ws)
                if best is None or score < best[0]: best = (score, parts)
            if best: break
            if k > 6: break
        if best is None: best = (0, [(i, i + 1) for i in range(len(bars))])
        systems = [bars[a:b] for a, b in best[1]]
        # balance: if last system has 1 bar and previous many, keep as is
        out = []
        for si, sysbars in enumerate(systems):
            o = Ops()
            x = start_x
            # staff lines drawn later after width known
            x = s.clef(o, x + 0.3 * sp)
            x = s.keysig(o, x, key_n)
            if si == 0 and first_timesig:
                x = s.timesig(o, x, num, den)
            x += sp * 0.6
            content_w = sum(sum(n.w for n in bar) + sp * 1.6 for bar in sysbars)
            avail = width - x
            scale = avail / content_w
            if scale > 2.2:
                scale = 2.2
            line_end = x
            for bi, bar in enumerate(sysbars):
                bx = x + sp * 0.9 * scale
                for n in bar:
                    n.x = bx + sp * 0.75 + (sp * 1.2 if n.showacc is not None else 0)
                    bx += n.w * scale
                x = bx + sp * 0.7 * scale
                last_bar_overall = (si == len(systems) - 1 and bi == len(sysbars) - 1)
                if last_bar_overall and final_bar:
                    o.line(x - 2.2, 0, x - 2.2, 4 * sp, 0.7)
                    o.line(x + 0.6, 0, x + 0.6, 4 * sp, 2.4)
                    x += 1.8
                else:
                    o.line(x, 0, x, 4 * sp, 0.7)
                line_end = x
            for i in range(5):
                o.line(start_x, i * sp, line_end, i * sp, 0.55)
            sysnotes = [n for bar in sysbars for n in bar]
            s._notes(o, sysnotes, notes, slurs, hairpins)
            o.width = line_end
            out.append(o)
        return out

    def _notes(s, o, sysnotes, allnotes, slurs, hairpins):
        sp = s.sp
        rx, ry = 0.66 * sp, 0.47 * sp
        ids = set(n.idx for n in sysnotes)
        mid = s.y(34)
        # stem directions
        groups = {}
        for n in sysnotes:
            if n.beam: groups.setdefault(n.beam, []).append(n)
        for n in sysnotes:
            n.yy = s.y(n.p.d)
            n.up = n.p.d < 34
        for g in groups.values():
            far = max(g, key=lambda n: abs(n.p.d - 34))
            avg = sum(n.p.d for n in g) / len(g)
            up = (avg < 34) if abs(avg - 34) > 0.6 else (far.p.d < 34)
            for n in g: n.up = up
        # heads, ledgers, accidentals, dots
        for n in sysnotes:
            filled = n.dur < 24
            o.head(n.x, n.yy, rx * (1.08 if n.dur == 48 else 1), ry, filled, -20 if n.dur != 48 else -10)
            d = n.p.d
            if d <= 28:
                for ld in range(28, d - 1, -2): o.line(n.x - rx * 1.6, s.y(ld), n.x + rx * 1.6, s.y(ld), 0.8)
            if d >= 40:
                for ld in range(40, d + 1, 2): o.line(n.x - rx * 1.6, s.y(ld), n.x + rx * 1.6, s.y(ld), 0.8)
            if n.showacc is not None:
                s.acc(o, n.x - rx - sp * 1.25, d, n.showacc)
            if n.dur in (9, 18, 36):
                dy = n.yy if d % 2 == 1 else n.yy + sp / 2
                o.dot(n.x + rx + sp * 0.5, dy, sp * 0.17)
        # stems (single)
        L = 3.5 * sp
        for n in sysnotes:
            if n.dur >= 48: n.stem_end = None; continue
            if n.beam is None:
                if n.up:
                    n.sx = n.x + rx * 0.93; n.stem_end = max(n.yy + L, mid if n.p.d < 27 else -1e9)
                else:
                    n.sx = n.x - rx * 0.93; n.stem_end = min(n.yy - L, mid if n.p.d > 41 else 1e9)
                o.line(n.sx, n.yy + (0.15 * sp if n.up else -0.15 * sp), n.sx, n.stem_end, 0.75)
                if n.dur < 12:  # flag
                    nb = 2 if n.dur == 3 else 1
                    for k in range(nb):
                        yb = n.stem_end - (k * 0.85 * sp if n.up else -k * 0.85 * sp)
                        sg = -1 if n.up else 1
                        o.poly([(n.sx, yb), (n.sx + 0.1 * sp, yb + sg * 0.2 * sp), (n.sx + 1.0 * sp, yb + sg * 1.4 * sp),
                                (n.sx + 0.75 * sp, yb + sg * 2.4 * sp), (n.sx + 0.85 * sp, yb + sg * 1.6 * sp),
                                (n.sx + 0.1 * sp, yb + sg * 1.0 * sp)])
        # beams
        bt = 0.48 * sp
        for g in groups.values():
            g.sort(key=lambda n: n.idx)
            up = g[0].up
            for n in g: n.sx = n.x + rx * 0.93 if up else n.x - rx * 0.93
            if len(g) == 1:
                n = g[0]
                n.stem_end = n.yy + L if up else n.yy - L
                o.line(n.sx, n.yy, n.sx, n.stem_end, 0.75)
                nb = 2 if n.dur == 3 else 1
                sg = -1 if up else 1
                for k in range(nb):
                    yb = n.stem_end + sg * k * 0.85 * sp
                    o.poly([(n.sx, yb), (n.sx + 0.1 * sp, yb + sg * 0.2 * sp), (n.sx + 1.0 * sp, yb + sg * 1.4 * sp),
                            (n.sx + 0.75 * sp, yb + sg * 2.4 * sp), (n.sx + 0.85 * sp, yb + sg * 1.6 * sp),
                            (n.sx + 0.1 * sp, yb + sg * 1.0 * sp)])
                continue
            x0, x1 = g[0].sx, g[-1].sx
            slope = (g[-1].yy - g[0].yy) / max(1, (x1 - x0))
            slope = max(-0.12, min(0.12, slope * 0.45))
            nbmax = max(2 if n.dur == 3 else 1 for n in g)
            minL = L if nbmax == 1 else L + 0.4 * sp
            if up:
                b0 = max(n.yy + minL - slope * (n.sx - x0) for n in g)
                b0 = max(b0, mid - slope * 0) if all(n.p.d < 27 for n in g) else b0
            else:
                b0 = min(n.yy - minL - slope * (n.sx - x0) for n in g)
                b0 = min(b0, mid) if all(n.p.d > 41 for n in g) else b0
            by = lambda xx: b0 + slope * (xx - x0)
            for n in g:
                n.stem_end = by(n.sx)
                o.line(n.sx, n.yy, n.sx, n.stem_end, 0.75)
            sg = -1 if up else 1  # inward direction
            def beam(xa, xb, off):
                ya, yb = by(xa) + sg * off, by(xb) + sg * off
                o.poly([(xa - 0.37, ya), (xb + 0.37, yb), (xb + 0.37, yb + sg * bt), (xa - 0.37, ya + sg * bt)])
            beam(x0, x1, 0)
            # secondary beams for 16ths
            k = 0
            while k < len(g):
                if g[k].dur == 3:
                    j = k
                    while j + 1 < len(g) and g[j + 1].dur == 3: j += 1
                    if j > k: beam(g[k].sx, g[j].sx, 0.78 * sp)
                    else:
                        stub = 1.2 * sp
                        if k > 0: beam(g[k].sx - stub, g[k].sx, 0.78 * sp)
                        else: beam(g[k].sx, g[k].sx + stub, 0.78 * sp)
                    k = j + 1
                else: k += 1
            # triplet number
            if g[0].trip is not None and len(g) == 3:
                xm = (x0 + x1) / 2
                ty = by(xm) + (0.9 * sp if up else -2.1 * sp)
                o.text(xm, ty, '3', 'MusicBI', sp * 1.6, 'c')
                for n in g: n.trip_y = ty + (1.5 * sp if up else -0.3 * sp)
        # articulations: notehead side
        for n in sysnotes:
            side = -1 if n.up else 1  # notehead side direction: up stems => below
            side = -side  # side multiplier: -1 means below
            side = -1 if n.up else 1
            # side = +1 above, -1 below (opposite stem)
            yv = n.yy
            ext = n.yy + side * ry
            # special: if dur>=48 (no stem) place above
            for a in n.art:
                if a == 'stacc':
                    yd = ext + side * 0.75 * sp
                    # avoid staff line
                    rel = yd / sp
                    if 0 - 0.1 < rel < 4.1 and abs(rel - round(rel)) < 0.22:
                        yd = (round(rel) + 0.5 * side) * sp
                    o.dot(n.x, yd, sp * 0.19); ext = yd + side * 0.2 * sp
                elif a == 'ten':
                    yd = ext + side * 0.75 * sp
                    rel = yd / sp
                    if -0.1 < rel < 4.1 and abs(rel - round(rel)) < 0.22:
                        yd = (round(rel) + 0.5 * side) * sp
                    o.poly([(n.x - 0.7 * sp, yd - 0.08 * sp), (n.x + 0.7 * sp, yd - 0.08 * sp),
                            (n.x + 0.7 * sp, yd + 0.08 * sp), (n.x - 0.7 * sp, yd + 0.08 * sp)])
                    ext = yd + side * 0.15 * sp
                elif a == 'acc':
                    yc = ext + side * 1.1 * sp
                    w, h = 0.75 * sp, 0.42 * sp
                    o.poly([(n.x - w, yc + h), (n.x + w, yc + 0.06 * sp), (n.x + w, yc - 0.06 * sp), (n.x - w, yc - h),
                            (n.x - w, yc - h + 0.15 * sp), (n.x + w - 0.45 * sp, yc), (n.x - w, yc + h - 0.15 * sp)])
                    ext = yc + side * h
                elif a == 'wedge':
                    tip = ext + side * 0.55 * sp; base = tip + side * 1.1 * sp
                    o.poly([(n.x, tip), (n.x - 0.32 * sp, base), (n.x + 0.32 * sp, base)])
                    ext = base
            n.art_ext = ext; n.art_side = side
        # extents per note
        for n in sysnotes:
            top = n.yy + ry; bot = n.yy - ry
            if n.stem_end is not None:
                if n.up: top = max(top, n.stem_end + (bt if n.beam else 0))
                else: bot = min(bot, n.stem_end - (bt if n.beam else 0))
            if n.art_side > 0: top = max(top, n.art_ext)
            else: bot = min(bot, n.art_ext)
            if getattr(n, 'trip_y', None) is not None:
                if n.up: top = max(top, n.trip_y)
                else: bot = min(bot, n.trip_y - 1.6 * sp)
            n.top, n.bot = top, bot
        # slurs
        slur_above = {}  # idx -> y top of slur at that note
        for (a, b) in slurs:
            if a not in ids and b not in ids: continue
            seg = [n for n in sysnotes if a <= n.idx <= b]
            if len(seg) < 2: continue
            cont_left = a not in ids; cont_right = b not in ids
            ups = set(n.up for n in seg)
            above = (ups == {False})
            if len(ups) > 1: above = True
            sg = 1 if above else -1
            def ep(n):
                if above: return n.top + 0.55 * sp
                return n.bot - 0.55 * sp
            first, last = seg[0], seg[-1]
            xa = first.x + (0.15 * sp if not first.up or not above else 0.5 * sp)
            xb = last.x - (0.15 * sp)
            if above and first.up: xa = first.sx
            if above and last.up: xb = last.sx
            if not above and not first.up: xa = first.sx
            if not above and not last.up: xb = last.sx
            ya, yb = ep(first), ep(last)
            if cont_left: xa = first.x - 2.5 * sp
            if cont_right: xb = last.x + 2.5 * sp
            if above: ya = yb = max(ya, yb) if abs(ya - yb) > 3 * sp else None or ya
            # recompute (keep endpoints individual but limit difference)
            ya, yb = ep(first), ep(last)
            if above:
                lo = max(ya, yb) - 2.5 * sp
                ya, yb = max(ya, lo), max(yb, lo)
            else:
                hi = min(ya, yb) + 2.5 * sp
                ya, yb = min(ya, hi), min(yb, hi)
            span = xb - xa
            h = sg * min(3.2 * sp, 0.7 * sp + span * 0.06)
            for n in seg[1:-1]:
                u = (n.x - xa) / span
                if u <= 0 or u >= 1: continue
                base = ya + (yb - ya) * u
                need = (n.top + 0.55 * sp - base) if above else (n.bot - 0.55 * sp - base)
                f = 3 * u * (1 - u)
                if above and need > 0 and need / f > h: h = need / f
                if not above and need < 0 and need / f < h: h = need / f
            p0 = (xa, ya); p3 = (xb, yb)
            p1 = (xa + span * 0.2, ya + h * 1.0); p2 = (xb - span * 0.2, yb + h * 1.0)
            o.slur(p0, p1, p2, p3, sg * 0.22 * sp)
            for n in seg:
                u = (n.x - xa) / span if span else 0
                yv = ya + (yb - ya) * u + 3 * u * (1 - u) * h * 1.0 + sg * 0.3 * sp
                if above: n.top = max(n.top, yv)
                else: n.bot = min(n.bot, yv)
        # fingerings, bow marks, positions above
        for n in sysnotes:
            y = max(n.top, 4 * sp) + 0.45 * sp
            if n.finger is not None:
                o.text(n.x, y, str(n.finger), 'SansB', sp * 1.35, 'c'); y += sp * 1.55
            if n.bow:
                y = s.bow_mark(o, n.x, y + 0.1 * sp, n.bow) + 0.4 * sp
            if n.pos:
                o.text(n.x, y + 0.1 * sp, n.pos, 'SerifBI', sp * 1.55, 'c'); y += sp * 1.7
            n.top = y
        # expressions below
        lowest = min([n.bot for n in sysnotes] + [0])
        for n in sysnotes:
            yb = min(lowest, 0) - 2.5 * sp
            xx = n.x - rx
            if n.dyn:
                o.text(xx, yb, n.dyn, 'MusicBI', sp * 1.9); xx += sp * (1.25 * len(n.dyn) + 1.0)
            if n.text:
                o.text(xx, yb, n.text, 'SerifI', sp * 1.6)
        for (a, b, kind) in hairpins:
            seg = [n for n in sysnotes if a <= n.idx <= b]
            if len(seg) < 2: continue
            yb = min(lowest, 0) - 1.6 * sp - (2.6 * sp if seg[0].text or seg[0].dyn else 0)
            xa, xb = seg[0].x, seg[-1].x
            hw = 0.55 * sp
            if kind == '<':
                o.line(xa, yb, xb, yb + hw, 0.6); o.line(xa, yb, xb, yb - hw, 0.6)
            else:
                o.line(xa, yb + hw, xb, yb, 0.6); o.line(xa, yb - hw, xb, yb, 0.6)
