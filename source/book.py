from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from music import Staff, Note, P, parse, keysig_alters, Ops
import scales as S
from scales import B, ORD, ROMAN, MODE_NAME, pretty

W, H = 612, 792
M = 54
CW = W - 2 * M
WINE = (0.42, 0.11, 0.18); GOLD = (0.72, 0.54, 0.23); INK = (0.13, 0.11, 0.11)
GREY = (0.42, 0.40, 0.40); CREAM = (0.99, 0.975, 0.945); SOFT = (0.965, 0.94, 0.90); LINE = (0.85, 0.80, 0.72)
TEAL = (0.16, 0.42, 0.45); SLATE = (0.30, 0.33, 0.45)
FCOL = {1: WINE, 2: GOLD, 3: TEAL, 4: SLATE}
TITLE = '100 Violin Scales'
SP = 6.0
st = Staff(SP)


def para(c, text, x, y, w, font='Serif', size=10.5, lead=None, color=INK, align='l'):
    lead = lead or size * 1.32
    c.setFont(font, size); c.setFillColorRGB(*color)
    for ln in simpleSplit(text, font, size, w):
        if align == 'c': c.drawCentredString(x + w / 2, y, ln)
        else: c.drawString(x, y, ln)
        y -= lead
    return y


def para_h(text, w, font='Serif', size=10.5, lead=None):
    lead = lead or size * 1.32
    return len(simpleSplit(text, font, size, w)) * lead


def key_of(tonic, mode):
    m = 'major' if mode == 'major' else 'minor'
    return keysig_alters(tonic, m)


def engrave(seq, bw, fingers=None, posmarks=None, width=CW, tonic=None, mode=None, staff=None):
    notes, slurs, hair, meter = S.build(seq, bw, fingers, posmarks=posmarks)
    al, n = key_of(tonic, mode)
    return (staff or st).engrave(notes, meter, n, al, width, slurs=slurs, hairpins=hair)


# ---------------------------------------------------------------- mixed-font canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
SPECIAL = set('\u266D\u266F\u266E\u2669\u2605')


class MC(canvas.Canvas):
    def _runs(s, text):
        runs = []
        for ch in text:
            sp = ch in SPECIAL
            if runs and runs[-1][0] == sp: runs[-1][1] += ch
            else: runs.append([sp, ch])
        return runs

    def _mw(s, text):
        f, z = s._fontname, s._fontsize
        return sum(stringWidth(t, 'Music' if sp else f, z) for sp, t in s._runs(text))

    def drawString(s, x, y, text, *a, **k):
        if not any(ch in SPECIAL for ch in text) or s._fontname.startswith('Music'):
            return super().drawString(x, y, text, *a, **k)
        f, z = s._fontname, s._fontsize
        for sp, t in s._runs(text):
            fn = 'Music' if sp else f
            s.setFont(fn, z * (1.05 if sp else 1)); super().drawString(x, y, t)
            x += stringWidth(t, fn, z * (1.05 if sp else 1))
        s.setFont(f, z)

    def drawRightString(s, x, y, text, *a, **k):
        if not any(ch in SPECIAL for ch in text): return super().drawRightString(x, y, text, *a, **k)
        s.drawString(x - s._mw(text), y, text)

    def drawCentredString(s, x, y, text, *a, **k):
        if not any(ch in SPECIAL for ch in text): return super().drawCentredString(x, y, text, *a, **k)
        s.drawString(x - s._mw(text) / 2, y, text)


# ---------------------------------------------------------------- page furniture
class Book:
    def __init__(s, fn):
        s.c = MC(fn, pagesize=(W, H))
        s.c.setTitle('100 Violin Scales: Positions 1-5, Every Bowing, Every Slur Pattern')
        s.c.setAuthor('Bruce Bowers')
        s.c.setSubject('Intermediate violin scales and bowing workbook')
        s.page = 1; s.section = ''; s.toc = []; s.started = False; s.gear_page = None

    def new_page(s, furniture=True):
        if s.started:
            s.c.showPage(); s.page += 1
        s.started = True
        s.c.setFillColorRGB(1, 1, 1); s.c.rect(0, 0, W, H, stroke=0, fill=1)
        if furniture:
            c = s.c
            c.setFillColorRGB(*GOLD); c.setFont('SansSB', 7.5)
            c.drawString(M, H - 34, TITLE.upper() + '  ·  POSITIONS 1–5')
            c.setFillColorRGB(*GREY); c.setFont('Sans', 7.5)
            c.drawRightString(W - M, H - 34, s.section.upper())
            c.setStrokeColorRGB(*LINE); c.setLineWidth(0.6); c.line(M, H - 40, W - M, H - 40)
            c.setFont('Serif', 9.5); c.setFillColorRGB(*GREY)
            c.drawCentredString(W / 2, 30, str(s.page))
            c.setFont('Sans', 6.5); c.drawString(M, 30, '© 2026 Bruce Bowers')
            if not s.section.startswith('Gear Guide') and getattr(s, 'gear_page', None):
                t = f'Strings, rosin & gear for your level: Gear Guide, p. {s.gear_page}'
                c.setFillColorRGB(*WINE); c.setFont('SansSB', 6.5); c.drawRightString(W - M, 30, t)
                tw = c.stringWidth(t, 'SansSB', 6.5)
                c.linkRect('', 'gear', (W - M - tw, 27, W - M, 38), relative=0)
        return H - 62

    def heading(s, y, kicker, title, sub=None):
        c = s.c
        c.setFillColorRGB(*GOLD); c.setFont('SansSB', 8.5); c.drawString(M, y, kicker.upper())
        y -= 26
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 25); c.drawString(M, y, title)
        y -= 10
        c.setStrokeColorRGB(*GOLD); c.setLineWidth(1.4); c.line(M, y, M + 60, y)
        y -= 18
        if sub:
            y = para(c, sub, M, y, CW, 'SerifI', 11.5, color=GREY) - 4
        return y

    def save(s): s.c.save()


def render_systems(c, systems, x, ytop, gap=6, color=INK, bg=(1, 1, 1)):
    y = ytop
    for o in systems:
        o.render(c, x, y - o.ymax, color, bg)
        y -= (o.ymax - o.ymin) + gap
    return y


def systems_h(systems, gap=6):
    return sum((o.ymax - o.ymin) + gap for o in systems)


# ---------------------------------------------------------------- exercise block
def exercise_block(num, e):
    bw = B[e['bow']]
    systems = engrave(e['seq'], bw, e['fingers'], e.get('posmarks'), tonic=e['tonic'], mode=e['mode'])
    tip = bw['tip']
    if e['kind'] == 'one':
        tip = 'Stay on the ' + e['title'].split(' on the ')[1].replace(' String', '') + \
              ' string the whole way. Slide on the finger you are leaving and lighten it during the shift. ' + tip
    elif e['kind'] == 'shift':
        tip = 'Each shift is marked with its new position. Slide lightly on the old finger, land the new one in tune, and keep the bow moving. ' + tip
    tip_w = CW - 8
    h = 40 + para_h(tip, tip_w, 'SerifI', 9.6, 12) + 8 + systems_h(systems) + 10
    return dict(num=num, e=e, bw=bw, systems=systems, tip=tip, h=h)


def draw_exercise(c, blk, y):
    e, bw, num = blk['e'], blk['bw'], blk['num']
    c.setStrokeColorRGB(*LINE); c.setLineWidth(0.6); c.line(M, y, W - M, y)
    y -= 6
    # badge
    c.setFillColorRGB(*WINE); c.roundRect(M, y - 24, 34, 22, 4, stroke=0, fill=1)
    c.setFillColorRGB(*CREAM); c.setFont('SansB', 12); c.drawCentredString(M + 17, y - 18.5, str(num))
    avail = CW - 44 - c.stringWidth(bw['title'], 'SansSB', 9.5) - 20
    fs = 15
    while c.stringWidth(e['title'], 'SerifB', fs) > avail and fs > 11: fs -= 0.5
    c.setFillColorRGB(*INK); c.setFont('SerifB', fs); c.drawString(M + 44, y - 13, e['title'])
    c.setFillColorRGB(*GREY); c.setFont('Sans', 8.5); c.drawString(M + 44, y - 25, e['sub'])
    c.setFillColorRGB(*WINE); c.setFont('SansSB', 9.5); c.drawRightString(W - M, y - 12, bw['title'])
    c.setFillColorRGB(*GREY); c.setFont('Music', 9.5); c.drawRightString(W - M, y - 25, 'Tempo goal  ' + bw['tempo'])
    y -= 40
    y = para(c, blk['tip'], M + 4, y, CW - 8, 'SerifI', 9.6, 12, color=(0.30, 0.27, 0.27))
    y -= 4
    y = render_systems(c, blk['systems'], M, y)
    return y - 6


# ---------------------------------------------------------------- front matter pages
def cover(bk):
    c = bk.c
    bk.new_page(False)
    c.setFillColorRGB(*WINE); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setStrokeColorRGB(*GOLD); c.setLineWidth(2.2); c.rect(26, 26, W - 52, H - 52)
    c.setLineWidth(0.7); c.rect(33, 33, W - 66, H - 66)
    c.setFillColorRGB(*GOLD); c.setFont('SansSB', 10)
    c.drawCentredString(W / 2, H - 112, 'AN INTERMEDIATE SCALE & BOWING WORKBOOK')
    c.setFillColorRGB(*CREAM); c.setFont('SerifB', 86); c.drawCentredString(W / 2, H - 215, '100')
    c.setFont('SerifB', 46); c.drawCentredString(W / 2, H - 268, 'Violin Scales')
    c.setFillColorRGB(*GOLD); c.setFont('SerifI', 19)
    c.drawCentredString(W / 2, H - 302, 'Positions 1 through 5  ·  Every Bowing  ·  Every Slur Pattern')
    # gold engraved scale
    seq, _ = S.scale_seq(parse('D4'), 'major')
    seq = seq + seq[::-1][1:]
    bw = dict(B['LEG4_S'])
    notes, slurs, hair, meter = S.build(seq, bw)
    for n in notes: n.text = None; n.dyn = None; n.bow = None
    al, kn = keysig_alters(parse('D4'), 'major')
    syss = st.engrave(notes[:16] + [Note(seq[15], 12)], (4, 4), kn, al, CW - 40, slurs=[(0, 3), (4, 7), (8, 11), (12, 15)])
    o = syss[0]
    o.render(c, M + 20, H - 400 - o.ymax / 2, GOLD, WINE)
    c.setFillColorRGB(*CREAM); c.setFont('Sans', 10.5)
    items = ['100 scales in major, harmonic minor and melodic minor', '36 bowing patterns: détaché, legato, staccato, martelé, spiccato,',
             'collé, louré, hooked bowing, slurred staccato and more', 'Shifting scales on one string and across the fingerboard',
             'Bonus: 28 arpeggios, a bowing guide, fingerboard map,', 'rhythm variations, a 12-week plan and printable trackers',
             'Plus a full-page practice edition: every scale on its own page']
    y = H - 510
    for it in items:
        c.drawCentredString(W / 2, y, it); y -= 17
    c.setStrokeColorRGB(*GOLD); c.setLineWidth(0.8); c.line(W / 2 - 40, 140, W / 2 + 40, 140)
    c.setFillColorRGB(*CREAM); c.setFont('SerifB', 22); c.drawCentredString(W / 2, 108, 'Bruce Bowers')
    c.setFillColorRGB(*GOLD); c.setFont('Sans', 9)
    c.drawCentredString(W / 2, 88, 'Registered Suzuki Violin Teacher  ·  47 Years at the Violin')


def copyright_page(bk):
    c = bk.c; bk.section = ''
    y = bk.new_page(False) - 120
    c.setFillColorRGB(*WINE); c.setFont('SerifB', 22); c.drawCentredString(W / 2, y, '100 Violin Scales')
    y -= 22; c.setFillColorRGB(*GREY); c.setFont('SerifI', 13)
    c.drawCentredString(W / 2, y, 'Positions 1 through 5, Every Bowing, Every Slur Pattern')
    y -= 18; c.setFont('Sans', 10); c.drawCentredString(W / 2, y, 'by Bruce Bowers')
    y = 430
    c.setFillColorRGB(*INK); c.setFont('SansSB', 9); c.drawString(M + 60, y, 'COPYRIGHT'); y -= 16
    y = para(c, '© 2026 Bruce Bowers. All rights reserved. This book may not be sold, changed or republished under another name.', M + 60, y, CW - 120, 'Serif', 10.5) - 14
    c.setFont('SansSB', 9); c.drawString(M + 60, y, 'FREE TO PRINT AND SHARE'); y -= 16
    y = para(c, 'This book is free. Print as many copies as you like, and share the PDF with students, teachers and friends, as long as it is shared whole and unchanged and is never sold.', M + 60, y, CW - 120, 'Serif', 10.5) - 14
    c.setFont('SansSB', 9); c.drawString(M + 60, y, 'AMAZON AFFILIATE DISCLOSURE'); y -= 16
    y = para(c, DISCLOSURE, M + 60, y, CW - 120, 'Serif', 10.5) - 14
    c.setFont('SansSB', 9); c.drawString(M + 60, y, 'A NOTE ON FINGERINGS'); y -= 16
    y = para(c, 'Fingerings in this book are one sound choice among several. Your teacher may suggest different fingerings to suit your hand, and that is exactly how it should be.', M + 60, y, CW - 120, 'Serif', 10.5)


def toc_page(bk, entries):
    c = bk.c; bk.section = 'Contents'
    y = bk.new_page()
    y = bk.heading(y, 'Inside this book', 'Contents')
    y -= 4
    for title, sub, pg, lvl in entries:
        if lvl == 0:
            y -= 6
            c.setFillColorRGB(*WINE); c.setFont('SerifB', 13); c.drawString(M, y, title)
            c.setFont('SerifB', 12); c.drawRightString(W - M, y, str(pg))
            if sub:
                c.setFillColorRGB(*GREY); c.setFont('Sans', 8.5); c.drawString(M + 4, y - 12, sub); y -= 12
            y -= 18
        else:
            c.setFillColorRGB(*INK); c.setFont('Serif', 11); c.drawString(M + 16, y, title)
            tw = c.stringWidth(title, 'Serif', 11)
            c.setFillColorRGB(*LINE); c.setFont('Serif', 11)
            dots = '.' * int((CW - 16 - tw - 30) / c.stringWidth('.', 'Serif', 11))
            c.drawString(M + 20 + tw, y, dots)
            c.setFillColorRGB(*INK); c.drawRightString(W - M, y, str(pg)); y -= 15


def how_to_use(bk):
    c = bk.c; bk.section = 'Getting Started'
    y = bk.new_page()
    y = bk.heading(y, 'Getting started', 'How to Use This Book',
                   'Scales are where tone, intonation, shifting and bow control all get built at the same time. Here is how to get the most out of every one of these 100.')
    blocks = [
        ('Play the same notes, change the bow', 'Each key appears several times with a different bowing. The notes stay familiar so your attention can go to the right arm. When a new bowing feels awkward, go back to an earlier key you already know and try it there first.'),
        ('Work in this order every time', '1. Play the scale slowly with separate bows and listen only for pitch. 2. Add the written bowing at a slow tempo. 3. Climb the metronome a few clicks at a time toward the tempo goal. 4. Finish by playing it once beautifully, as if someone were listening.'),
        ('Use the metronome ladder', 'Start at a tempo where every note is clean. Play the scale twice in a row without a mistake, then move the metronome up 4 clicks. If you miss, drop back 8 clicks and climb again. Write your best tempo in the Scale Tracker at the back.'),
        ('Check your intonation with ringing tones', 'Every G, D, A and E you play can be checked against an open string. When the note is in tune, the open string vibrates in sympathy and the violin rings. If it sounds dull, the note is not quite in tune yet.'),
        ('Read the markings', 'Finger numbers appear above the notes: every note on the first page of each key, then at each string crossing. Labels such as 3rd pos. show where to shift in the shifting scales. The bowing name is printed at the start of each scale and explained in the Bowing Guide.'),
        ('A little every day beats a lot once a week', 'Ten to fifteen focused minutes of scales a day will change your playing more than an hour on Saturday. The 12-week plan near the back gives you a ready-made path through the whole book.'),
    ]
    for t, body in blocks:
        c.setFillColorRGB(*GOLD); c.circle(M + 5, y + 3.5, 3.2, stroke=0, fill=1)
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 13.5); c.drawString(M + 16, y, t); y -= 17
        y = para(c, body, M + 16, y, CW - 16, 'Serif', 11, 14.5) - 12


def legend(bk):
    c = bk.c; bk.section = 'Getting Started'
    y = bk.new_page()
    y = bk.heading(y, 'Getting started', 'Reading the Markings', 'Every symbol used in this book, in one place.')
    rows = [
        ('down', 'Down-bow', 'Pull the bow from the frog toward the tip.'),
        ('up', 'Up-bow', 'Push the bow from the tip toward the frog.'),
        ('finger', 'Finger number', '0 = open string, 1 = index, 2 = middle, 3 = ring, 4 = pinky.'),
        ('roman', 'Position', 'Shows which position to play in. Used in the shifting scales wherever the hand moves.'),
        ('stacc', 'Staccato dot', 'Short. Stop the bow between notes (on the string unless it says spiccato or collé).'),
        ('ten', 'Tenuto line', 'Full length. In a slur it means louré: a gentle pulse without stopping the bow.'),
        ('acc', 'Accent', 'Start the note with extra bow speed and weight, then release.'),
        ('wedge', 'Martelé wedge', 'Pinch, release, stop. A biting start with silence after each note.'),
        ('slur', 'Slur', 'All notes under the curved line are played in one bow.'),
        ('hair', 'Crescendo / diminuendo', 'Grow louder, or grow softer, by changing bow speed and weight.'),
    ]
    from music import Staff as _St
    sl = _St(8.0)
    for kind, name, desc in rows:
        o = Ops(); x0 = 30
        c.setFillColorRGB(*SOFT); c.roundRect(M, y - 38, 110, 46, 5, stroke=0, fill=1)
        if kind in ('down', 'up'):
            sl.bow_mark(o, x0, 0, kind); o.render(c, M + 25, y - 22, INK)
        elif kind == 'finger':
            o.text(x0, 0, '0  1  2  3  4', 'SansB', 12, 'c'); o.render(c, M + 25, y - 20, INK)
        elif kind == 'roman':
            o.text(x0, 0, '3rd pos.', 'SerifBI', 13, 'c'); o.render(c, M + 25, y - 20, INK)
        elif kind == 'slur':
            o.slur((x0 - 26, 0), (x0 - 13, 11), (x0 + 13, 11), (x0 + 26, 0), 1.6); o.render(c, M + 25, y - 22, INK)
        elif kind == 'hair':
            o.line(x0 - 32, 4, x0 - 4, 10, 0.9); o.line(x0 - 32, 4, x0 - 4, -2, 0.9)
            o.line(x0 + 4, 10, x0 + 32, 4, 0.9); o.line(x0 + 4, -2, x0 + 32, 4, 0.9); o.render(c, M + 25, y - 20, INK)
        else:
            n = Note(parse('G4'), 12, art=[kind]); n.x = 55
            n.idx = 0; n.beam = None; n.showacc = None
            ops = Ops()
            for i in range(5): ops.line(22, i * 8.0, 88, i * 8.0, 0.5)
            sl._notes(ops, [n], [n], [], [])
            ops.render(c, M, y - 30, INK)
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 13); c.drawString(M + 126, y - 6, name)
        para(c, desc, M + 126, y - 21, CW - 126, 'Serif', 10.5, 13)
        y -= 56


def fingerboard_map(bk):
    c = bk.c; bk.section = 'Getting Started'
    y = bk.new_page()
    y = bk.heading(y, 'Getting started', 'Fingerboard Map: Positions 1 to 5',
                   'The natural note under each finger, on each string, in each position. A sharp or flat uses the same finger, placed a little higher or lower.')
    strings = [('G', 4), ('D', 1), ('A', 5), ('E', 2)]  # letter index in CDEFGAB
    colw = (CW - 70) / 4
    c.setFillColorRGB(*INK); c.setFont('SansB', 11)
    for i, (sname, _) in enumerate(strings):
        c.drawCentredString(M + 70 + colw * i + colw / 2, y, f'{sname} string')
    y -= 12
    for pos in range(1, 6):
        rh = 74
        c.setFillColorRGB(*(SOFT if pos % 2 else CREAM)); c.rect(M, y - rh, CW, rh, stroke=0, fill=1)
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 15); c.drawString(M + 8, y - 30, ORD[pos])
        c.setFont('Sans', 8.5); c.setFillColorRGB(*GREY); c.drawString(M + 8, y - 43, 'position')
        for i, (sname, li) in enumerate(strings):
            cx = M + 70 + colw * i
            for f in range(1, 5):
                letter = 'CDEFGAB'[(li + pos - 1 + f) % 7]
                yy = y - 12 - (f - 1) * 15.5
                c.setFillColorRGB(*FCOL[f]); c.circle(cx + 22, yy - 3.5, 6.2, stroke=0, fill=1)
                c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 8); c.drawCentredString(cx + 22, yy - 6.3, str(f))
                c.setFillColorRGB(*INK); c.setFont('SerifB', 12); c.drawString(cx + 34, yy - 7.5, letter)
        y -= rh + 4
    y -= 10
    tips = [('Position is named by the 1st finger.', 'In 1st position your 1st finger plays the note one step above the open string. In 3rd position it plays the note three steps above, and so on.'),
            ('The open-string trick.', 'In 4th position your 1st finger plays the same note as the next higher open string. In 5th position your 4th finger plays the octave of the next higher open string. Use both as tuning checks.'),
            ('Same shape, different place.', 'Each position uses the same finger shape as 1st position. What changes is where your hand sits and which notes are whole steps or half steps apart.')]
    for t, b in tips:
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 11.5); c.drawString(M, y, t); y -= 14
        y = para(c, b, M, y, CW, 'Serif', 10.5, 13.5) - 8


GUIDE = [
    ('Détaché', 'DET_E', 'Middle of the bow', 'Smooth, separate strokes with no gap and no accent. The bow changes direction for every note and the sound never stops.', 'Bumps at each bow change.', 'Keep the bow hand soft and let the fingers flex a tiny bit at each change.'),
    ('Legato (slurs)', 'LEG4_E', 'Anywhere; plan the distribution', 'Several notes in one bow. The left hand changes notes while the bow keeps a steady speed and contact point.', 'Running out of bow, or the last notes of the slur fading.', 'Divide the bow into equal parts before you start, and keep the speed even.'),
    ('On-the-string staccato', 'STAC_E', 'Middle to upper half', 'Short notes with the bow staying in the string. The bow stops after every note.', 'Notes that are short but scratchy.', 'Release a little weight at the moment the bow stops, then set it again for the next note.'),
    ('Martelé', 'MART_Q', 'Upper half', 'A hammered stroke: pre-weight the string, release with a quick bow, stop completely. The start has a consonant-like bite.', 'Pressing during the note, which chokes the sound.', 'All the weight goes in before the note. During the stroke the arm lets go.'),
    ('Spiccato', 'SPIC_E', 'Near the balance point, lower half', 'An off-the-string stroke. The bow drops and bounces in a shallow arc and the hair leaves the string between notes.', 'Bouncing too high, so the rhythm becomes uneven.', 'Lower the arm and make the arc flatter. Let the stick bounce; do not throw it.'),
    ('Collé', 'COLLE_Q', 'At the frog', 'A tiny pinched stroke made mostly by the fingers. Set the bow, pinch, release, and lift.', 'Using the whole arm, which makes the stroke too big.', 'Hold the arm still and let only the fingers and wrist make the stroke.'),
    ('Louré (portato)', 'LOURE2', 'Middle of the bow', 'Several notes in one bow, each gently separated by a small release of weight. The bow does not stop.', 'Stopping the bow, which turns it into slurred staccato.', 'Think of each note as a soft swell, like saying "da-da-da" in one breath.'),
    ('Hooked bowing', 'HOOK', 'Middle to upper half', 'A long and a short note in the same bow direction with a small stop between them. Used for dotted rhythms.', 'The short note comes too early or too long.', 'Count the sixteenth carefully and give it a quick, light bow.'),
    ('Slurred staccato', 'SLST2', 'Upper half for up-bow, lower half for down-bow', 'Several short, stopped notes in one bow direction. The bow stops, the finger changes, the bow moves again.', 'Notes running together.', 'Exaggerate the stops at first. Clarity first, speed later.'),
    ('Accented détaché', 'ACC_E', 'Middle of the bow', 'Each note starts with a quick burst of bow speed, then relaxes while the bow keeps moving.', 'Squeezing to make the accent.', 'Make the accent with speed, not pressure.'),
    ('Whole bows', 'WB_Q', 'Frog to tip', 'Use the entire bow on every note with a steady, ringing tone.', 'Arriving at the tip early, then crawling.', 'Mark the middle of the bow and check that you pass it exactly halfway through each note.'),
    ('Bow distribution patterns', 'S3S1', 'Varies', 'Mixed slurs and separate notes (slur 3 + 1, slur 2 + 2, and so on) train the bow to change speed while the tone stays even.', 'Drifting toward the tip or the frog over several beats.', 'Use the same amount of bow for the slur as for the separate note, which means the separate note moves faster.'),
]


def bowing_guide(bk):
    c = bk.c; bk.section = 'Bowing Guide'
    y = bk.new_page()
    y = bk.heading(y, 'Getting started', 'The Bowing Guide',
                   'Twelve families of strokes used in this book. Each one shows what it looks like on the page, where in the bow it lives, and the most common mistake.')
    ex = S.scale_seq(parse('A4'), 'major', 1)[0]
    for name, key, where, how, mistake, fix in GUIDE:
        bw = dict(B[key])
        seq = ex[:5] if bw['rhythm'] != 'd' else ex[:5]
        notes, slurs, hair, meter = S.build(ex[:8] + [ex[7]], bw)
        cut = []; t = 0
        for n in notes:
            if t >= 24: break
            cut.append(n); t += n.dur
        for n in cut: n.text = None; n.dyn = None
        slurs2 = [(a, b) for a, b in slurs if b < len(cut)]
        al, kn = keysig_alters(parse('A4'), 'major')
        syss = st.engrave(cut, (2, 4), kn, al, 170, first_timesig=False, slurs=slurs2, final_bar=False)
        o = syss[0]
        block_h = 14 + para_h(how, CW - 200, 'Serif', 10, 12.5) + 30
        block_h = max(block_h, (o.ymax - o.ymin) + 26)
        if y - block_h < 50:
            y = bk.new_page()
        c.setFillColorRGB(*SOFT); c.roundRect(M, y - block_h + 6, 184, block_h - 4, 5, stroke=0, fill=1)
        o.render(c, M + 8, y - 4 - (block_h - 10 - (o.ymax - o.ymin)) / 2 - o.ymax, INK)
        x2 = M + 198
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 14); c.drawString(x2, y - 8, name)
        c.setFillColorRGB(*GOLD); c.setFont('SansSB', 8); c.drawRightString(W - M, y - 7, where.upper())
        yy = para(c, how, x2, y - 23, CW - 198, 'Serif', 10, 12.5)
        c.setFillColorRGB(*INK); c.setFont('SansSB', 8.5)
        yy -= 2
        yy = para(c, 'Watch for: ' + mistake + ' Fix: ' + fix, x2, yy, CW - 198, 'SerifI', 9.6, 12, color=(0.3, 0.27, 0.27))
        y = min(y - block_h, yy) - 10


def section_intro(bk, y, kicker, title, text, pos=None, rules=None):
    c = bk.c
    c.setFillColorRGB(*WINE); c.roundRect(M, y - 118, CW, 118, 8, stroke=0, fill=1)
    c.setFillColorRGB(*GOLD); c.setFont('SansSB', 9); c.drawString(M + 20, y - 26, kicker.upper())
    c.setFillColorRGB(*CREAM); c.setFont('SerifB', 28); c.drawString(M + 20, y - 58, title)
    para(c, text, M + 20, y - 80, CW - 40, 'Serif', 11, 14, color=CREAM)
    y -= 134
    if pos:
        strings = [('G', 4), ('D', 1), ('A', 5), ('E', 2)]
        c.setFillColorRGB(*INK); c.setFont('SansSB', 8.5); c.drawString(M, y, f'NOTES UNDER YOUR FINGERS IN {ORD[pos].upper()} POSITION')
        y -= 16
        colw = CW / 4
        for i, (sn, li) in enumerate(strings):
            cx = M + colw * i
            c.setFillColorRGB(*SOFT); c.roundRect(cx + 2, y - 26, colw - 4, 32, 4, stroke=0, fill=1)
            c.setFillColorRGB(*GREY); c.setFont('SansSB', 8); c.drawString(cx + 10, y - 4, f'{sn} STRING')
            xx = cx + 10
            for f in range(1, 5):
                letter = 'CDEFGAB'[(li + pos - 1 + f) % 7]
                c.setFillColorRGB(*FCOL[f]); c.circle(xx + 5, y - 16, 5.2, stroke=0, fill=1)
                c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 7); c.drawCentredString(xx + 5, y - 18.4, str(f))
                c.setFillColorRGB(*INK); c.setFont('SerifB', 11); c.drawString(xx + 13, y - 20, letter)
                xx += (colw - 20) / 4
        y -= 40
        y = para(c, S.POS_TIPS[pos], M, y, CW, 'SerifI', 10.5, 13.5, color=(0.3, 0.27, 0.27)) - 8
    if rules:
        for i, r in enumerate(rules, 1):
            c.setFillColorRGB(*WINE); c.setFont('SansB', 10); c.drawString(M, y, f'{i}.')
            y = para(c, r, M + 16, y, CW - 16, 'Serif', 10.5, 13.5) - 4
        y -= 6
    return y


SHIFT_RULES = [
    'Slide on the finger you are leaving. Lighten its pressure during the slide so the string stays clean.',
    'The thumb travels with the hand. Never leave it behind in the old position.',
    'Hear the new note before you arrive. Sing it in your head while you shift.',
    'Use a guide note: practice the shift slowly with the slide audible, then make it faster and quieter.',
    'Keep the bow moving at an even speed through the shift so the shift does not stick out.',
]


def arpeggio_pages(bk, toc):
    c = bk.c; bk.section = 'Bonus: Arpeggios'
    y = bk.new_page()
    toc.append(('Bonus: 28 Arpeggios', 'Two-octave arpeggios for every key and position in the book', bk.page, 0))
    y = bk.heading(y, 'Bonus section', '28 Arpeggios',
                   'Every key from the position chapters as a two-octave arpeggio in the same position. Play each one right after its matching scales. Slur three, then try them with separate bows.')
    bw = dict(B['LEG3_E']); bw['label'] = 'legato'; bw['dyn'] = 'mf'
    for i, a in enumerate(S.arpeggios(), 1):
        notes, slurs, hair, meter = S.build(a['seq'], bw, a['fingers'])
        al, kn = key_of(a['tonic'], a['mode'])
        syss = st.engrave(notes, meter, kn, al, CW - 150, slurs=slurs)
        o = syss[0]
        h = (o.ymax - o.ymin) + 14
        if y - h < 50:
            y = bk.new_page()
        mode = 'Major' if a['mode'] == 'major' else 'Minor'
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 12.5); c.drawString(M, y - 14, f"{pretty(a['tonic'])} {mode}")
        c.setFillColorRGB(*GREY); c.setFont('Sans', 8.5); c.drawString(M, y - 27, f"{ORD[a['pos']]} position")
        c.setFont('Sans', 8.5); c.drawString(M, y - 39, f'Arpeggio {i}')
        o.render(c, M + 150, y - 4 - o.ymax)
        y -= h
        c.setStrokeColorRGB(*LINE); c.setLineWidth(0.4); c.line(M, y + 4, W - M, y + 4)


def rhythm_page(bk, toc):
    c = bk.c; bk.section = 'Bonus: Rhythm Variations'
    y = bk.new_page()
    toc.append(('Bonus: Rhythm Variations', 'Eight rhythms that turn any scale into a new exercise', bk.page, 0))
    y = bk.heading(y, 'Bonus section', 'Rhythm Variations',
                   'Apply any of these rhythms to any scale in the book. Rhythms force the fingers to move at different speeds, which exposes weak spots and makes even scales faster and cleaner.')
    fr = S.scale_seq(parse('A4'), 'major', 1)[0]
    pats = [('Long-short', [9, 3, 9, 3], None, 'Great for finger speed: the short note forces the next finger to drop fast.'),
            ('Short-long', [3, 9, 3, 9], None, 'The reverse. Snap the finger down on the short note, relax on the long one.'),
            ('Gallop', [6, 3, 3, 6, 3, 3], None, 'One eighth and two sixteenths. Keep the sixteenths exactly even.'),
            ('Reverse gallop', [3, 3, 6, 3, 3, 6], None, 'Two sixteenths and an eighth. Land precisely on the beat.'),
            ('Triplets', [4] * 6, 'trip', 'Three even notes per beat. Count "trip-o-let" out loud at first.'),
            ('Sixteenths', [3] * 8, None, 'Four even notes per beat with a steady metronome click.'),
            ('Quarter and two eighths', [12, 6, 6], None, 'A long note to listen for pitch, then two quick ones.'),
            ('Syncopation', [6, 12, 6], None, 'Short, long, short. Keep the bow even on the long note.')]
    al, kn = keysig_alters(parse('A4'), 'major')
    for name, durs, trip, tip in pats:
        notes = []
        for k, d in enumerate(durs):
            n = Note(fr[k], d)
            if trip: n.trip = k // 3
            notes.append(n)
        syss = st.engrave(notes, (2, 4), kn, al, 190, slurs=[], final_bar=False)
        o = syss[0]
        h = max(o.ymax - o.ymin, 30) + 14
        c.setFillColorRGB(*SOFT); c.roundRect(M, y - h + 4, 200, h - 2, 5, stroke=0, fill=1)
        o.render(c, M + 6, y - (h - (o.ymax - o.ymin)) / 2 - o.ymax + 3)
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 13); c.drawString(M + 214, y - 14, name)
        para(c, tip, M + 214, y - 29, CW - 214, 'Serif', 10.5, 13)
        y -= h + 6


PLAN = [
    ('1', 'Scales 1–12', 'Détaché, slurs of 2, 3 and 4, first martelé', 'Clean intonation at a slow tempo'),
    ('2', 'Scales 13–22', 'Mixed bowings, hooked bowing, triplets', 'Even bow distribution'),
    ('3', 'Scales 23–29', '2nd position: long slurs, collé, dotted rhythms', 'Comfort in 2nd position'),
    ('4', 'Scales 30–36', '2nd position: slurred staccato, louré, spiccato triplets', 'Light, clear off-the-string strokes'),
    ('5', 'Scales 37–44', '3rd position: staccato, martelé, legato', 'Hand frame resting on the violin body'),
    ('6', 'Scales 45–52', '3rd position: louré, hooked, whole bows', 'Full tone in a higher position'),
    ('7', 'Scales 53–60', '4th position: martelé, long slurs, collé', 'Open-string checks for the 1st finger'),
    ('8', 'Scales 61–67', '4th position: triplets, slurred staccato, slur 14', 'Long legato with crescendo and diminuendo'),
    ('9', 'Scales 68–82', '5th position: every bowing family', 'Relaxed thumb under the neck'),
    ('10', 'Scales 83–90', 'One-string scales through 1st, 3rd and 5th', 'Quiet, accurate shifts'),
    ('11', 'Scales 91–100', 'Two-octave shifting scales', 'Shifts that do not interrupt the bow'),
    ('12', 'Your choice', 'Pick your 10 weakest scales from the tracker', 'Every scale at its tempo goal'),
]


def plan_page(bk, toc):
    c = bk.c; bk.section = 'Practice Plan'
    y = bk.new_page()
    toc.append(('Practice Plan & Trackers', '12-week plan, daily routine, scale tracker and practice log', bk.page, 0))
    y = bk.heading(y, 'Your path through the book', 'The 12-Week Plan',
                   'One week per row. Play the scales listed every day, add the matching arpeggios, and log your tempos in the tracker.')
    cols = [(M, 'WEEK', 40), (M + 44, 'SCALES', 86), (M + 134, 'BOWING FOCUS', 210), (M + 350, 'GOAL', CW - 296)]
    c.setFillColorRGB(*WINE); c.rect(M, y - 6, CW, 20, stroke=0, fill=1)
    c.setFillColorRGB(*CREAM); c.setFont('SansSB', 8)
    for x, t, _ in cols: c.drawString(x + 6, y, t)
    y -= 8
    for i, row in enumerate(PLAN):
        rh = 26
        c.setFillColorRGB(*(SOFT if i % 2 == 0 else (1, 1, 1))); c.rect(M, y - rh, CW, rh, stroke=0, fill=1)
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 13); c.drawString(cols[0][0] + 10, y - 17, row[0])
        for (x, _, w), txt in zip(cols[1:], row[1:]):
            c.setFillColorRGB(*INK); c.setFont('Serif', 10)
            lines = simpleSplit(txt, 'Serif', 10, w - 10)
            yy = y - 11 if len(lines) > 1 else y - 16
            for ln in lines: c.drawString(x + 6, yy, ln); yy -= 11
        y -= rh
    y -= 24
    c.setFillColorRGB(*WINE); c.setFont('SerifB', 17); c.drawString(M, y, 'A 20-Minute Daily Scale Routine'); y -= 22
    routine = [('3 min', 'Open strings with whole bows. Listen for one clean, ringing tone on each string.'),
               ('5 min', 'Today’s scale with separate bows, slowly. Fix every note that does not ring.'),
               ('7 min', 'The written bowing with the metronome ladder. Two clean runs, then four clicks faster.'),
               ('3 min', 'The matching arpeggio from the bonus section.'),
               ('2 min', 'One rhythm variation, then play the scale once more as music, not as an exercise.')]
    for t, d in routine:
        c.setFillColorRGB(*GOLD); c.roundRect(M, y - 6, 46, 18, 4, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 9); c.drawCentredString(M + 23, y - 0.5, t)
        para(c, d, M + 58, y, CW - 58, 'Serif', 10.5); y -= 24


def tracker_pages(bk, allex):
    c = bk.c; bk.section = 'Scale Tracker'
    per = 36; i = 0
    while i < len(allex):
        y = bk.new_page()
        if i == 0:
            y = bk.heading(y, 'Printable', 'Scale Tracker',
                           'Check a box each time you play a scale cleanly twice in a row at that tempo. Star the scale when it reaches its tempo goal.')
        cols = [('NO.', 0), ('SCALE', 30), ('POSITION', 196), ('BOWING', 262), ('60', 400), ('72', 422), ('84', 444), ('96', 466), ('★', 488)]
        c.setFillColorRGB(*WINE); c.rect(M, y - 6, CW, 18, stroke=0, fill=1)
        c.setFillColorRGB(*CREAM); c.setFont('SansSB', 7.5)
        for t, x in cols: c.drawString(M + x + 4, y - 0.5, t)
        y -= 7
        rows = allex[i:i + per] if i == 0 else allex[i:i + per + 4]
        if i == 0: rows = allex[i:i + 26]
        for j, (num, e) in enumerate(rows):
            rh = 16.5
            c.setFillColorRGB(*(SOFT if j % 2 == 0 else (1, 1, 1))); c.rect(M, y - rh, CW, rh, stroke=0, fill=1)
            c.setFillColorRGB(*WINE); c.setFont('SansB', 8.5); c.drawString(M + 5, y - 11.5, str(num))
            c.setFillColorRGB(*INK); c.setFont('Serif', 9.5)
            title = e['title'].replace(' on the ', ', ')
            c.drawString(M + 34, y - 11.5, title[:34])
            pos = ORD[e['pos']] if e['pos'] else ('shifting' if e['kind'] != 'one' else '1st-3rd-5th')
            c.setFont('Sans', 8); c.drawString(M + 200, y - 11.5, pos)
            c.drawString(M + 266, y - 11.5, B[e['bow']]['title'][:30])
            c.setStrokeColorRGB(*GREY); c.setLineWidth(0.6)
            for x in (400, 422, 444, 466, 488):
                c.rect(M + x + 3, y - 13, 9, 9, stroke=1, fill=0)
            y -= rh
        i += len(rows)


def log_page(bk):
    c = bk.c; bk.section = 'Practice Log'
    y = bk.new_page()
    y = bk.heading(y, 'Printable', 'Weekly Practice Log', 'Print one copy per week. Write down what you played, how fast, and one thing that got better.')
    c.setFillColorRGB(*INK); c.setFont('Sans', 9)
    c.drawString(M, y, 'Week of: ______________________     Weekly goal: ___________________________________________')
    y -= 22
    cols = [('DAY', 0, 46), ('SCALES PLAYED (NO.)', 46, 120), ('BOWINGS', 166, 110), ('BEST TEMPO', 276, 64), ('MINUTES', 340, 50), ('WHAT GOT BETTER', 390, CW - 390)]
    c.setFillColorRGB(*WINE); c.rect(M, y - 6, CW, 18, stroke=0, fill=1)
    c.setFillColorRGB(*CREAM); c.setFont('SansSB', 7.5)
    for t, x, w in cols: c.drawString(M + x + 4, y - 0.5, t)
    y -= 6
    for d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
        rh = 56
        c.setStrokeColorRGB(*LINE); c.setLineWidth(0.6); c.rect(M, y - rh, CW, rh, stroke=1, fill=0)
        for t, x, w in cols[1:]: c.line(M + x, y, M + x, y - rh)
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 12); c.drawString(M + 8, y - 20, d)
        y -= rh
    y -= 22
    c.setFillColorRGB(*WINE); c.setFont('SerifB', 13); c.drawString(M, y, 'Notes from my teacher'); y -= 10
    c.setStrokeColorRGB(*LINE)
    for k in range(4):
        y -= 20; c.line(M, y, W - M, y)


def about_page(bk):
    c = bk.c; bk.section = 'About the Author'
    y = bk.new_page()
    y = bk.heading(y, 'About the author', 'Bruce Bowers')
    text = ['Bruce Bowers has played the violin for 47 years and has taught for more than 20. He is a registered Suzuki Method teacher through Book 6, and he has performed as concertmaster, assistant concertmaster and principal second violin in local symphony orchestras.',
            'He teaches Suzuki violin in the Pulaski and Green Bay area of Wisconsin, where he works with students of every age and stage, from first lessons to advanced repertoire.',
            'This book brings together the scale and bowing work an intermediate player needs in one place: every major position from 1st to 5th, every core bow stroke, and every common slur pattern, laid out so a student can practice it a little at a time and actually see the progress.']
    for t in text:
        y = para(c, t, M, y, CW, 'Serif', 12, 17) - 10
    y -= 20
    c.setFillColorRGB(*SOFT); c.roundRect(M, y - 92, CW, 92, 8, stroke=0, fill=1)
    c.setFillColorRGB(*WINE); c.setFont('SerifB', 15); c.drawString(M + 20, y - 28, 'Thank you for practicing with this book.')
    para(c, 'If it helps you, the best thank-you is to share this free book with a friend or your teacher. Need strings, rosin or a new shoulder rest? The Gear Guide links help support more free resources like this one. More violin music: fiddlemusicstore.com', M + 20, y - 48, CW - 40, 'Serif', 11, 14.5)


# ---------------------------------------------------------------- full-page practice edition
from music import Staff as _Staff
stL = _Staff(7.4)
stM = _Staff(6.4)
OPEN = {'G': parse('G3'), 'D': parse('D4'), 'A': parse('A4'), 'E': parse('E5')}
CHECKS = ['Every note rings in tune', 'Even bow distribution', 'Smooth bow changes and string crossings',
          'Steady with the metronome', 'Bowing played exactly as written']


def open_string_bar(bw, e, stm=None):
    stm = stm or stM
    sname = e['strings'][0][0]
    p = OPEN[sname]
    notes, slurs, hair, meter = S.build([p] * 29, bw)
    num, den = meter; bar = num * (48 // den)
    cut = []; t = 0
    for n in notes:
        if t + n.dur > bar * 2: break
        cut.append(n); t += n.dur
    for n in cut: n.text = None; n.dyn = None; n.finger = None
    cut[0].finger = 0; cut[0].dyn = bw['dyn']
    sl = [(a, b) for a, b in slurs if b < len(cut)]
    al, kn = key_of(e['tonic'], e['mode'])
    return stm.engrave(cut, meter, kn, al, CW - 150, slurs=sl), sname


def arpeggio_for(e, stm=None):
    t = e['tonic']; pos = e['pos']
    up, _ = S.scale_seq(t, 'harmonic' if e['mode'] != 'major' else 'major')
    idx = [0, 2, 4, 7, 9, 11, 14]
    a_up = [up[i] for i in idx]; seq = a_up + a_up[::-1][1:]
    res, marks = S.finger_seq(seq, [pos] * len(seq), show='all')
    bw = dict(B['LEG3_E']); bw['label'] = 'legato, slur three'
    return engrave(seq, bw, marks, tonic=t, mode=e['mode'], staff=stm or stM)


def slow_pass(e, stm=None):
    bw = dict(B['DET_Q']); bw['label'] = 'slow, separate bows'; bw['dyn'] = 'mf'
    fingers = None
    if e['kind'] in ('one', 'shift'):
        n = len(e['seq'])
        upn = n // 2 + 1
        # recompute full fingering (all notes)
        fingers = [f for (_, f, _) in e['strings']]
    return engrave(e['seq'], bw, fingers, e.get('posmarks'), tonic=e['tonic'], mode=e['mode'], staff=stm or stM)


def sub_label(c, y, title, note):
    c.setFillColorRGB(*WINE); c.setFont('SansB', 9); c.drawString(M, y, title.upper())
    c.setFillColorRGB(*GREY); c.setFont('SerifI', 9.8)
    c.drawString(M + c.stringWidth(title.upper(), 'SansB', 9) + 10, y, note)
    return y - 8


def full_page(bk, num, e):
    c = bk.c; bw = B[e['bow']]
    y = bk.new_page()
    # header band
    c.setFillColorRGB(*SOFT); c.roundRect(M, y - 58, CW, 62, 7, stroke=0, fill=1)
    c.setFillColorRGB(*WINE); c.roundRect(M + 10, y - 47, 48, 40, 6, stroke=0, fill=1)
    c.setFillColorRGB(*CREAM); c.setFont('SansB', 19); c.drawCentredString(M + 34, y - 34, str(num))
    avail = CW - 70 - c.stringWidth(bw['title'], 'SansSB', 11) - 30
    fs = 21
    while c.stringWidth(e['title'], 'SerifB', fs) > avail and fs > 13: fs -= 0.5
    c.setFillColorRGB(*INK); c.setFont('SerifB', fs); c.drawString(M + 70, y - 24, e['title'])
    c.setFillColorRGB(*GREY); c.setFont('Sans', 9.5); c.drawString(M + 70, y - 40, e['sub'])
    c.setFillColorRGB(*WINE); c.setFont('SansSB', 11); c.drawRightString(W - M - 12, y - 22, bw['title'])
    c.setFillColorRGB(*GREY); c.setFont('Music', 10.5); c.drawRightString(W - M - 12, y - 38, 'Tempo goal  ' + bw['tempo'])
    y -= 74
    # focus
    focus = bw['tip']
    if e['kind'] == 'pos': extra = S.POS_TIPS[e['pos']]
    elif e['kind'] == 'one': extra = 'Stay on one string the whole way. Slide on the finger you are leaving and lighten it during each shift.'
    else: extra = 'Each shift is marked with its new position. Slide lightly on the old finger and keep the bow moving through the shift.'
    c.setFillColorRGB(*GOLD); c.rect(M, y - para_h(focus + ' ' + extra, CW - 16, 'Serif', 10.5, 13.5) + 6, 3, para_h(focus + ' ' + extra, CW - 16, 'Serif', 10.5, 13.5) + 4, stroke=0, fill=1)
    c.setFillColorRGB(*WINE); c.setFont('SansB', 8.5); c.drawString(M + 12, y + 2, "TODAY'S FOCUS")
    y = para(c, focus + ' ' + extra, M + 12, y - 12, CW - 16, 'Serif', 10.5, 13.5) - 10
    # choose sizes so everything fits above the tracker strip
    ffing = [f for (_, f, _) in e['strings']]
    for bigsp, medsp in [(7.4, 6.4), (6.8, 6.0), (6.2, 5.6), (5.8, 5.2)]:
        sL, sM = _Staff(bigsp), _Staff(medsp)
        big = engrave(e['seq'], bw, ffing, e.get('posmarks'), tonic=e['tonic'], mode=e['mode'], staff=sL)
        rh, sname = open_string_bar(bw, e, sM)
        sec = arpeggio_for(e, sM) if e['kind'] == 'pos' else slow_pass(e, sM)
        need = 8 + systems_h(big, 4) + 6 + 8 + (rh[0].ymax - rh[0].ymin) + 14 + 8 + systems_h(sec, 2) + 8
        if y - need > 50 + 112 + 6: break
    y = sub_label(c, y, 'The scale', 'large print, with the written bowing')
    y = render_systems(c, big, M, y - 2, gap=4) - 6
    o = rh[0]
    y = sub_label(c, y, 'Right hand first', f'the bowing alone on the open {sname} string, before adding the left hand')
    h = (o.ymax - o.ymin)
    c.setFillColorRGB(*SOFT); c.roundRect(M, y - h - 8, 140, h + 6, 5, stroke=0, fill=1)
    para(c, 'Play these two bars until the stroke feels easy and the sound is even. Then play the scale.', M + 10, y - 16, 122, 'SerifI', 9.2, 11.5, color=(0.3, 0.27, 0.27))
    o.render(c, M + 150, y - 4 - o.ymax)
    y -= h + 14
    if e['kind'] == 'pos':
        y = sub_label(c, y, 'Matching arpeggio', f'same key, same {ORD[e["pos"]]} position')
    else:
        y = sub_label(c, y, 'Slow-motion pass', 'separate bows, every finger shown; listen to each shift')
    y = render_systems(c, sec, M, y - 2, gap=2) - 8
    return y, c


def finish_page(bk, y):
    c = bk.c
    # tracker strip pinned to the bottom of the page
    bottom = 50
    th = 112 if y - 6 >= 162 else 88
    if y - 6 < 50 + th: bottom = max(42, y - 6 - th)
    top = bottom + th
    compact = th < 112
    if y - 10 > top + 30:
        # notes lines in leftover space
        c.setFillColorRGB(*WINE); c.setFont('SansB', 8.5); c.drawString(M, y - 4, 'MY NOTES')
        c.setStrokeColorRGB(*LINE); c.setLineWidth(0.5)
        yy = y - 24
        while yy > top + 14:
            c.line(M, yy, W - M, yy); yy -= 20
    c.setFillColorRGB(*SOFT); c.roundRect(M, bottom, CW, th, 7, stroke=0, fill=1)
    c.setFillColorRGB(*WINE); c.setFont('SansB', 8.5); c.drawString(M + 14, top - 18, 'TEMPO LOG')
    c.setFillColorRGB(*GREY); c.setFont('Sans', 7.5); c.drawString(M + 80, top - 18, 'write your best clean tempo each day')
    bx = M + 14; bwid = (CW * 0.56 - 14) / 7
    for d in range(7):
        x = bx + d * bwid
        c.setStrokeColorRGB(*GREY); c.setLineWidth(0.6); c.setFillColorRGB(1, 1, 1)
        bh = 26 if compact else 34
        c.roundRect(x, bottom + (28 if compact else 34), bwid - 6, bh, 3, stroke=1, fill=1)
        c.setFillColorRGB(*GREY); c.setFont('SansSB', 7); c.drawCentredString(x + (bwid - 6) / 2, bottom + (17 if compact else 22), f'DAY {d + 1}')
    cx = M + CW * 0.6
    c.setFillColorRGB(*WINE); c.setFont('SansB', 8.5); c.drawString(cx, top - 18, 'CHECKLIST')
    yy = top - (30 if compact else 34)
    for ch in CHECKS:
        c.setStrokeColorRGB(*GREY); c.setFillColorRGB(1, 1, 1); c.rect(cx, yy - 1, 8.5, 8.5, stroke=1, fill=1)
        c.setFillColorRGB(*INK); c.setFont('Serif', 9.5); c.drawString(cx + 14, yy, ch); yy -= 12 if compact else 14.5


def full_section(bk, toc, exs):
    bk.section = 'Part 7: Full-Page Practice Edition'
    y = bk.new_page()
    toc.append(('Part 7: Full-Page Practice Edition', 'Scales 1–100 again, one full page each, with practice tools', bk.page, 0))
    y = section_intro(bk, y, 'Part 7  ·  Scales 1–100', 'Full-Page Practice Edition',
                      'Every scale in this book again, one per page, in larger print. Each page adds a right-hand warm-up, a matching arpeggio or slow-motion pass, a tempo log and a checklist. Print the page you are working on and put it on your stand.')
    c = bk.c
    items = [('Today’s focus', 'The one thing to listen for, plus a reminder about the position or the shifts.'),
             ('The scale', 'Large print with every finger number shown, so it is easy to read from the stand.'),
             ('Right hand first', 'The bowing pattern on an open string. Master the stroke before the notes.'),
             ('Matching arpeggio', 'The arpeggio of the same key in the same position (pages 1–82).'),
             ('Slow-motion pass', 'The shifting scales in slow quarter notes so every shift can be heard (pages 83–100).'),
             ('Tempo log and checklist', 'Seven days of tempos and five quality checks. When every box is checked, move on.')]
    for t, d in items:
        c.setFillColorRGB(*GOLD); c.circle(M + 5, y + 3.5, 3.2, stroke=0, fill=1)
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 13); c.drawString(M + 16, y, t); y -= 16
        y = para(c, d, M + 16, y, CW - 16, 'Serif', 11, 14) - 10
    for num, e in enumerate(exs, 1):
        y, _ = full_page(bk, num, e)
        if y < 42 + 88 + 6: print('OVERFLOW', num, y)
        finish_page(bk, y)


# ---------------------------------------------------------------- gear guide (Amazon affiliate)
from urllib.parse import quote_plus
TAG = 'bumblepickleb-20'
DISCLOSURE = ('As an Amazon Associate I earn from qualifying purchases. This book contains Amazon affiliate links. '
              'If you buy something through one of them, I may earn a small commission at no extra cost to you. '
              'Each link opens an Amazon search for that item, so you can compare sellers, sizes and current prices.')


def amz(q):
    return f'https://www.amazon.com/s?k={quote_plus(q)}&tag={TAG}'


GEAR = [
    ('Strings', 'A good set of strings is the fastest upgrade in tone at this level. Change them every 6 to 12 months.', [
        ('Thomastik Dominant', 'The classic synthetic-core set: warm, even and reliable.', 'Thomastik Dominant violin strings 4/4 set'),
        ('Pirastro Tonica', 'Warm and easy to play, and a great value.', 'Pirastro Tonica violin strings 4/4 set'),
        ("D'Addario Pro-Arte", 'A smooth, mellow set for students moving up from steel.', "D'Addario Pro-Arte violin strings 4/4"),
        ("D'Addario Helicore", 'Steel core: bright, stable and long-lasting.', "D'Addario Helicore violin strings 4/4"),
        ('Pirastro Gold Label E', 'A favorite single E string that tames a shrill top end.', 'Pirastro Gold Label violin E string'),
        ('Fine tuners', 'Make tuning steel or synthetic strings quick and precise.', 'violin fine tuners 4/4 set'),
    ]),
    ('Rosin', 'Fresh rosin gives a clean start to every note, especially in martelé and spiccato.', [
        ('Hill Dark Rosin', 'Smooth grip that works for most players and climates.', 'Hill dark violin rosin'),
        ('Pirastro Goldflex', 'Rosin with gold flakes for a clear, focused sound.', 'Pirastro Goldflex rosin violin'),
        ("Jade L'Opera", 'Very low dust, and a fine choice for sensitive players.', "Jade L'Opera rosin violin"),
        ('Bernardel Rosin', 'Light, low-dust rosin for a sweet tone.', 'Bernardel rosin violin'),
    ]),
    ('Shoulder Rests', 'The right rest frees the left hand for shifting into 3rd, 4th and 5th position.', [
        ('Kun Original', 'Adjustable and the most widely used rest.', 'Kun Original violin shoulder rest 4/4'),
        ('Bon Musica', 'Shapeable metal frame for a secure hold.', 'Bon Musica violin shoulder rest'),
        ('Wolf Forte Secondo', 'Very adjustable in height and angle.', 'Wolf Forte Secondo violin shoulder rest'),
        ('Everest EZ', 'Affordable and comfortable.', 'Everest EZ violin shoulder rest 4/4'),
    ]),
    ('Tuners & Metronomes', 'Every scale in this book has a tempo goal. A metronome is not optional.', [
        ('Korg TM-60', 'Tuner and metronome in one, with a sound-back tone for intonation.', 'Korg TM-60 tuner metronome'),
        ('Clip-on tuner', 'Tunes quietly without a phone.', 'Snark clip-on tuner violin'),
        ('Korg MA-2 Metronome', 'Small, loud and simple.', 'Korg MA-2 metronome'),
        ('Wittner Mechanical Metronome', 'A classic pendulum metronome for the practice room.', 'Wittner mechanical metronome'),
    ]),
    ('Mutes', 'For practicing late or early without bothering the house, and for soft orchestra passages.', [
        ('Heavy rubber practice mute', 'Cuts the sound way down for quiet practice.', 'violin practice mute heavy rubber'),
        ('Tourte mute', 'The standard orchestra mute.', 'Tourte violin mute'),
    ]),
    ('Care & Humidity', 'Dry winter air cracks wood and slips pegs. Keep the instrument clean and humidified.', [
        ('Dampit humidifier', 'Sits inside the f-hole to keep the violin from drying out.', 'Dampit violin humidifier'),
        ('Case hygrometer', 'Shows the humidity inside your case at a glance.', 'violin case hygrometer'),
        ('Microfiber polishing cloth', 'Wipe off rosin dust after every practice.', 'violin microfiber polishing cloth'),
        ('Peg compound', 'Stops slipping or sticking pegs.', 'Hill peg compound violin'),
    ]),
    ('Bows, Cases & Stands', 'Upgrades that make practice easier and protect your instrument.', [
        ('Carbon fiber bow', 'Durable, well balanced and good for off-the-string strokes.', 'carbon fiber violin bow 4/4'),
        ('Oblong violin case', 'Room for music, rosin and spare strings.', 'oblong violin case 4/4 with hygrometer'),
        ('Manhasset music stand', 'The sturdy stand used by orchestras everywhere.', 'Manhasset music stand'),
        ('Music stand light', 'Clip-on LED light for reading small print.', 'music stand light clip on LED'),
    ]),
    ('Practice Tools', 'Tools that help you see and hear what you are doing.', [
        ('Practice mirror', 'Check that the bow stays parallel to the bridge.', 'full length standing mirror'),
        ('Zoom H1n recorder', 'Record yourself and hear your intonation honestly.', 'Zoom H1n handy recorder'),
        ('Pencils for your music', 'Mark fingerings, bowings and reminders.', 'pencils with erasers bulk'),
    ]),
    ('Next-Step Books', 'Studies and method books that pair well with this book.', [
        ('Whistler: Introducing the Positions, Vol. 1', '3rd and 5th positions, step by step.', 'Whistler Introducing the Positions violin volume 1'),
        ('Whistler: Introducing the Positions, Vol. 2', '2nd, 4th, 6th and 7th positions.', 'Whistler Introducing the Positions violin volume 2'),
        ('Wohlfahrt: 60 Studies, Op. 45', 'The classic first etudes for bowing and positions.', 'Wohlfahrt 60 Studies Op 45 violin'),
        ('Ševčík: Changes of Position, Op. 8', 'Focused shifting exercises.', 'Sevcik Op 8 changes of position violin'),
        ('Schradieck: School of Violin Technics, Book 1', 'Left-hand finger strength and accuracy.', 'Schradieck School of Violin Technics book 1'),
        ('Kreutzer: 42 Studies', 'The next big step in bowing and technique.', 'Kreutzer 42 studies violin'),
    ]),
]


def gear_pages(bk, toc):
    c = bk.c; bk.section = 'Gear Guide'
    y = bk.new_page()
    c.bookmarkPage('gear')
    toc.append(('Gear Guide', 'Strings, rosin, shoulder rests, tuners, care and next-step books', bk.page, 0))
    y = bk.heading(y, 'For the intermediate violinist', 'Gear Guide',
                   'Everything a violinist at this level needs, from strings and rosin to the next books to study. Tap any button to see the item on Amazon.')
    # disclosure box
    h = para_h(DISCLOSURE, CW - 28, 'Serif', 9.5, 12) + 24
    c.setFillColorRGB(*SOFT); c.roundRect(M, y - h + 8, CW, h, 6, stroke=0, fill=1)
    c.setFillColorRGB(*WINE); c.setFont('SansB', 8); c.drawString(M + 14, y - 6, 'AMAZON AFFILIATE DISCLOSURE')
    y = para(c, DISCLOSURE, M + 14, y - 20, CW - 28, 'Serif', 9.5, 12, color=(0.3, 0.27, 0.27)) - 18
    colw = (CW - 14) / 2
    for cat, intro, items in GEAR:
        need = 40 + 54
        if y - need < 56:
            y = bk.new_page()
        c.setFillColorRGB(*WINE); c.setFont('SerifB', 16); c.drawString(M, y, cat)
        c.setStrokeColorRGB(*GOLD); c.setLineWidth(1.2); c.line(M, y - 6, M + 40, y - 6)
        y = para(c, intro, M, y - 20, CW, 'SerifI', 10, 12.5, color=GREY) - 4
        for i in range(0, len(items), 2):
            row = items[i:i + 2]
            ch = 58
            if y - ch < 50:
                y = bk.new_page()
            for j, (name, why, q) in enumerate(row):
                x = M + j * (colw + 14)
                c.setStrokeColorRGB(*LINE); c.setLineWidth(0.7); c.setFillColorRGB(1, 1, 1)
                c.roundRect(x, y - ch, colw, ch - 4, 6, stroke=1, fill=1)
                c.setFillColorRGB(*INK); c.setFont('SerifB', 11.5)
                nm = name
                while c.stringWidth(nm, 'SerifB', 11.5) > colw - 20: nm = nm[:-2]
                c.drawString(x + 10, y - 17, nm)
                para(c, why, x + 10, y - 30, colw - 100, 'Serif', 8.8, 10.5, color=(0.3, 0.27, 0.27))
                bx, bw_, bh = x + colw - 84, 74, 20
                c.setFillColorRGB(*GOLD); c.roundRect(bx, y - ch + 10, bw_, bh, 10, stroke=0, fill=1)
                c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 8); c.drawCentredString(bx + bw_ / 2, y - ch + 17, 'See on Amazon')
                url = amz(q)
                c.linkURL(url, (bx, y - ch + 10, bx + bw_, y - ch + 10 + bh), relative=0)
                c.linkURL(url, (x, y - ch, x + colw, y - 4), relative=0)
            y -= ch + 4
        y -= 14
    y -= 4
    if y < 90: y = bk.new_page()
    para(c, 'Prices and availability change on Amazon. Ask your teacher before changing strings or a shoulder rest if you are unsure what fits your violin.', M, y, CW, 'SerifI', 9.5, 12, color=GREY)


# ---------------------------------------------------------------- build
def build(fn):
    exs = S.make_exercises() + S.make_shift_exercises()
    blocks = [exercise_block(i, e) for i, e in enumerate(exs, 1)]
    allex = list(enumerate(exs, 1))

    def run(bk, toc_entries=None):
        toc = []
        cover(bk)
        copyright_page(bk)
        toc_page(bk, toc_entries or [])
        if toc_entries is None:
            pass
        toc.append(('Getting Started', 'How to use this book, markings, fingerboard map', bk.page + 1, 0))
        how_to_use(bk); toc.append(('How to Use This Book', None, bk.page, 1))
        legend(bk); toc.append(('Reading the Markings', None, bk.page, 1))
        fingerboard_map(bk); toc.append(('Fingerboard Map: Positions 1 to 5', None, bk.page, 1))
        toc.append(('The Bowing Guide', None, bk.page + 1, 1))
        bowing_guide(bk)
        # scale sections
        sections = [(1, 'Part 1', 'First Position', 'Scales 1–22',
                     'Eight keys in 1st position, each with several bowings. Open strings are used for ringing-tone checks. Get comfortable with the bowings here, then carry them up the fingerboard.'),
                    (2, 'Part 2', 'Second Position', 'Scales 23–36',
                     'Second position has no open strings, so every note is under a finger. That makes it the best position for building a steady hand frame.'),
                    (3, 'Part 3', 'Third Position', 'Scales 37–52',
                     'The most-used position after 1st. Your hand now rests lightly against the violin body, which gives you a dependable landmark.'),
                    (4, 'Part 4', 'Fourth Position', 'Scales 53–67',
                     'Fourth position sounds like 1st position one string higher. Use the open strings to check your 1st and 4th fingers.'),
                    (5, 'Part 5', 'Fifth Position', 'Scales 68–82',
                     'Fifth position brings the brightest sound on each string. Bring the thumb partly under the neck and keep the elbow swinging forward for the G string.'),
                    (None, 'Part 6', 'Shifting Scales', 'Scales 83–100',
                     'Now connect the positions. First, one-octave scales on a single string through 1st, 3rd and 5th positions. Then two-octave scales that shift on the same string.')]
        bi = 0
        for pos, kick, title, rng, text in sections:
            bk.section = f'{kick}: {title}'
            y = bk.new_page()
            toc.append((f'{kick}: {title}', rng, bk.page, 0))
            y = section_intro(bk, y, f'{kick}  ·  {rng}', title, text, pos=pos, rules=None if pos else SHIFT_RULES)
            while bi < len(blocks):
                blk = blocks[bi]; e = blk['e']
                if (pos and e['pos'] != pos) or (pos is None and e['kind'] == 'pos'):
                    break
                if y - blk['h'] < 46:
                    y = bk.new_page()
                y = draw_exercise(bk.c, blk, y)
                bi += 1
        full_section(bk, toc, exs)
        arpeggio_pages(bk, toc)
        rhythm_page(bk, toc)
        plan_page(bk, toc)
        toc.append(('Scale Tracker', None, bk.page + 1, 1))
        tracker_pages(bk, allex)
        toc.append(('Weekly Practice Log', None, bk.page + 1, 1))
        log_page(bk)
        gear_pages(bk, toc)
        about_page(bk)
        toc.append(('About the Author', None, bk.page, 0))
        return toc

    import os
    dry = Book(os.devnull)
    toc = run(dry)
    gp = [p for t, s_, p, l in toc if t == 'Gear Guide'][0]
    bk = Book(fn); bk.gear_page = gp
    run(bk, toc)
    bk.save()
    return bk.page


if __name__ == '__main__':
    import sys
    print(build(sys.argv[1] if len(sys.argv) > 1 else 'out.pdf'))
