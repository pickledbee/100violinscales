"""Render all notation used by the website to SVG files and collect audio data."""
import os, json, subprocess, tempfile
from reportlab.pdfgen import canvas
import book as BK
import scales as S
from scales import B, ORD
from music import Staff, Note, parse, keysig_alters

OUT = '/home/claude/100violinscales'
IMG = os.path.join(OUT, 'img')
os.makedirs(IMG, exist_ok=True)
TMP = tempfile.mkdtemp()


def save_svg(systems, name, gap=6):
    w = max(getattr(o, 'width', 0) or 0 for o in systems) + 10
    h = sum((o.ymax - o.ymin) + gap for o in systems) + 6
    pdf = os.path.join(TMP, name + '.pdf')
    c = canvas.Canvas(pdf, pagesize=(w, h))
    y = h - 3
    for o in systems:
        o.render(c, 4, y - o.ymax)
        y -= (o.ymax - o.ymin) + gap
    c.save()
    svg = os.path.join(IMG, name + '.svg')
    subprocess.run(['pdftocairo', '-svg', pdf, svg], check=True)
    return 'img/' + name + '.svg', round(w), round(h)


def events(notes, slurs=(), bw=None):
    """[midi, ticks, stroke_id, articulation] for the play-along engine."""
    cat = (bw or {}).get('cat', '')
    inslur = {}
    for a, b in slurs:
        for k in range(a, b + 1): inslur[k] = a
    sid, out = -1, []
    for i, n in enumerate(notes):
        if i not in inslur or inslur[i] == i: sid += 1
        a, art = n.art, ''
        if 'wedge' in a: art = 'ma'
        elif 'acc' in a: art = 'ac'
        elif 'ten' in a: art = 'lo' if i in inslur else 'te'
        elif 'stacc' in a:
            art = 'ss' if i in inslur else {'Spiccato': 'sp', 'Collé': 'cl'}.get(cat, 'st')
        out.append([n.p.semi + 12, n.dur, sid, art])
    return out


DYN = {'p': 0.6, 'mf': 0.8, 'f': 1.0}


def scale_assets():
    exs = S.make_exercises() + S.make_shift_exercises()
    data = []
    for num, e in enumerate(exs, 1):
        bw = B[e['bow']]
        fing = [f for (_, f, _) in e['strings']]
        sL, sM = Staff(7.0), Staff(6.2)
        main = BK.engrave(e['seq'], bw, fing, e.get('posmarks'), tonic=e['tonic'], mode=e['mode'], staff=sL)
        notes, slurs_main, *_ = S.build(e['seq'], bw)
        rh, sname = BK.open_string_bar(bw, e, sM)
        if e['kind'] == 'pos':
            sec = BK.arpeggio_for(e, sM)
            up, _ = S.scale_seq(e['tonic'], 'harmonic' if e['mode'] != 'major' else 'major')
            a_up = [up[i] for i in [0, 2, 4, 7, 9, 11, 14]]
            sec_notes, sec_slurs, *_ = S.build(a_up + a_up[::-1][1:], B['LEG3_E']); sec_bw = B['LEG3_E']
            sec_kind = 'arp'
        else:
            sec = BK.slow_pass(e, sM)
            sec_notes, sec_slurs, *_ = S.build(e['seq'], B['DET_Q']); sec_bw = B['DET_Q']
            sec_kind = 'slow'
        m = save_svg(main, f's{num:03d}', 4)
        r = save_svg(rh, f's{num:03d}-rh')
        s2 = save_svg(sec, f's{num:03d}-{sec_kind}', 2)
        mS = Staff(7.6)
        main_m = BK.engrave(e['seq'], bw, fing, e.get('posmarks'), tonic=e['tonic'], mode=e['mode'], staff=mS, width=330)
        mm = save_svg(main_m, f's{num:03d}-m', 4)
        msc = min(o.scale for o in main_m)
        if e['kind'] == 'pos':
            up2, _ = S.scale_seq(e['tonic'], 'harmonic' if e['mode'] != 'major' else 'major')
            au = [up2[i] for i in [0, 2, 4, 7, 9, 11, 14]]; aseq = au + au[::-1][1:]
            res2, marks2 = S.finger_seq(aseq, [e['pos']] * len(aseq), show='all')
            bwa = dict(B['LEG3_E']); bwa['label'] = 'legato, slur three'
            sec_m = BK.engrave(aseq, bwa, marks2, tonic=e['tonic'], mode=e['mode'], staff=mS, width=330)
        else:
            bws = dict(B['DET_Q']); bws['label'] = 'slow, separate bows'
            sec_m = BK.engrave(e['seq'], bws, fing, e.get('posmarks'), tonic=e['tonic'], mode=e['mode'], staff=mS, width=330)
        s2m = save_svg(sec_m, f's{num:03d}-{sec_kind}-m', 2)
        tip = bw['tip']
        if e['kind'] == 'pos': extra = S.POS_TIPS[e['pos']]
        elif e['kind'] == 'one': extra = 'Stay on one string the whole way. Slide on the finger you are leaving and lighten it during each shift.'
        else: extra = 'Each shift is marked with its new position. Slide lightly on the old finger and keep the bow moving through the shift.'
        lo, hi = [int(''.join(ch for ch in t if ch.isdigit())) for t in bw['tempo'].split('=')[1].split('–')]
        data.append(dict(
            num=num, title=e['title'], sub=e['sub'], kind=e['kind'], pos=e['pos'], mode=e['mode'],
            key=S.pretty(e['tonic']), bowing=bw['title'], cat=bw['cat'], label=bw['label'],
            tempo=bw['tempo'], tlo=lo, thi=hi, meter=list(bw['meter']), focus=tip, extra=extra,
            string=sname, main=m, rh=r, sec=s2, sec_kind=sec_kind, main_m=mm, sec_m=s2m, mscale=msc,
            audio=events(notes, slurs_main, bw), sec_audio=events(sec_notes, sec_slurs, sec_bw), dyn=DYN[bw['dyn']], sec_meter=[6, 8] if sec_kind == 'arp' else [4, 4]))
    return data


def guide_assets():
    out = []
    ex = S.scale_seq(parse('A4'), 'major', 1)[0]
    st = Staff(7.0)
    for name, key, where, how, mistake, fix in BK.GUIDE:
        bw = dict(B[key])
        notes, slurs, hair, meter = S.build(ex[:8] + [ex[7]], bw)
        cut = []; t = 0
        for n in notes:
            if t >= 24: break
            cut.append(n); t += n.dur
        for n in cut: n.text = None; n.dyn = None
        sl = [(a, b) for a, b in slurs if b < len(cut)]
        al, kn = keysig_alters(parse('A4'), 'major')
        syss = st.engrave(cut, (2, 4), kn, al, 260, first_timesig=False, slurs=sl, final_bar=False)
        img = save_svg(syss, 'guide-' + key.lower())
        out.append(dict(audio=events(cut, sl, bw), dyn=DYN[bw['dyn']], name=name, key=key, where=where, how=how, mistake=mistake, fix=fix, img=img))
    return out


def rhythm_assets():
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
    st = Staff(7.0); out = []
    for i, (name, durs, trip, tip) in enumerate(pats):
        notes = []
        for k, d in enumerate(durs):
            n = Note(fr[k], d)
            if trip: n.trip = k // 3
            notes.append(n)
        syss = st.engrave(notes, (2, 4), kn, al, 260, slurs=[], final_bar=False)
        img = save_svg(syss, f'rhythm-{i + 1}')
        out.append(dict(name=name, tip=tip, img=img, audio=events(notes)))
    return out


def arpeggio_assets():
    out = []
    bw = dict(B['LEG3_E']); bw['label'] = 'legato'; bw['dyn'] = 'mf'
    st = Staff(6.6)
    for i, a in enumerate(S.arpeggios(), 1):
        notes, slurs, hair, meter = S.build(a['seq'], bw, a['fingers'])
        al, kn = BK.key_of(a['tonic'], a['mode'])
        syss = st.engrave(notes, meter, kn, al, 470, slurs=slurs)
        img = save_svg(syss, f'arp-{i:02d}')
        imgm = save_svg(Staff(6.6).engrave(S.build(a['seq'], bw, a['fingers'])[0], meter, kn, al, 330, slurs=slurs), f'arp-{i:02d}-m')
        out.append(dict(num=i, img_m=imgm, key=S.pretty(a['tonic']), mode='Major' if a['mode'] == 'major' else 'Minor',
                        pos=a['pos'], img=img, audio=events(notes, slurs, bw)))
    return out


def legend_assets():
    out = {}
    st = Staff(8.0)
    from music import Ops
    for kind in ['stacc', 'ten', 'acc', 'wedge']:
        n = Note(parse('G4'), 12, art=[kind]); n.x = 30; n.idx = 0; n.beam = None; n.showacc = None
        o = Ops()
        for i in range(5): o.line(4, i * 8.0, 56, i * 8.0, 0.5)
        st._notes(o, [n], [n], [], []); o.width = 60
        out[kind] = save_svg([o], 'sym-' + kind)
    for kind in ['down', 'up']:
        o = Ops(); st.bow_mark(o, 14, 0, kind); o.width = 28
        out[kind] = save_svg([o], 'sym-' + kind)
    return out


if __name__ == '__main__':
    d = dict(scales=scale_assets(), guide=guide_assets(), rhythms=rhythm_assets(),
             arps=arpeggio_assets(), legend=legend_assets())
    json.dump(d, open('/home/claude/site_data.json', 'w'))
    print(len(d['scales']), len(os.listdir(IMG)))
