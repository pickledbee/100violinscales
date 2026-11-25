"""Generate the 100 Violin Scales website into docs/."""
import json, os, html
import book as BK
import scales as S

D = json.load(open('/home/claude/site_data.json'))
OUT = '/home/claude/100violinscales/docs'
SITE = 'https://pickledbee.github.io/100violinscales/'
E = html.escape

NAV = [('index.html', 'Scales'), ('start.html', 'Getting Started'), ('bowing.html', 'Bowing Guide'),
       ('arpeggios.html', 'Arpeggios'), ('rhythms.html', 'Rhythms'), ('plan.html', 'Practice Plan'),
       ('tracker.html', 'My Tracker'), ('gear.html', 'Gear Guide')]


def page(fn, title, desc, body, active=None, script=''):
    nav = ''.join(f'<a href="{h}"{" class=on" if h == active else ""}>{t}</a>' for h, t in NAV)
    doc = f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;0,700;1,400&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎻</text></svg>">
</head><body>
<header class="top"><div class="wrap"><a class="brand" href="index.html">100 Violin <span>Scales</span></a>
<button class="menu-btn" aria-label="Menu">Menu</button><nav class="nav">{nav}</nav></div></header>
<main>{body}</main>
<footer><div class="wrap cols">
<div><b>100 Violin Scales</b> · free for every violinist<br>© 2026 Bruce Bowers. Free to use; please do not copy or resell.</div>
<div style="max-width:520px">Amazon affiliate disclosure: As an Amazon Associate I earn from qualifying purchases. Links on the <a href="gear.html">Gear Guide</a> are affiliate links; buying through them costs you nothing extra.</div>
</div></footer>
<script src="app.js"></script>{script}
</body></html>'''
    open(os.path.join(OUT, fn), 'w').write(doc)


def player(events, meter, lo, hi, met=True, label='Play'):
    lo2 = max(30, lo)
    return f'''<div class="player" data-events='{json.dumps(events)}' data-meter='{json.dumps(meter)}'>
<button class="btn wine play">▶ {label}</button>
{'<button class="btn line met">Metronome</button>' if met else ''}
<span class="bpm"></span><input type="range" min="30" max="{max(160, hi + 20)}" value="{lo2}" aria-label="Tempo">
<label><input type="checkbox" class="clk" checked> click</label><label><input type="checkbox" class="cnt" checked> count-in</label>
<div class="prog"><i></i></div></div>'''


def fname(n): return f'scale-{n:03d}.html'


def pic(big, small, alt, scale=1.0):
    if scale < 0.85:
        return (f'<img src="{big[0]}" width="{big[1]}" height="{big[2]}" alt="{alt}" loading="lazy" style="--mw:640px">'
                '<div class="swipe">Swipe to see the whole line \u2192</div>')
    return f'<picture><source media="(max-width:640px)" srcset="{small[0]}"><img src="{big[0]}" width="{big[1]}" height="{big[2]}" alt="{alt}" loading="lazy"></picture>'


def posname(s):
    return S.ORD[s['pos']] + ' position' if s['pos'] else ('Shifting, one string' if s['kind'] == 'one' else 'Shifting')


# ------------------------------------------------------------------ home
def home():
    sc = D['scales']
    lite = [dict(num=s['num'], title=s['title'], sub=s['sub'], bowing=s['bowing'], cat=s['cat'], pos=s['pos'],
                 mode=s['mode'], kind=s['kind'], tempo=s['tempo'], thi=s['thi']) for s in sc]
    cats = sorted(set(s['cat'] for s in sc))
    chips = lambda f, opts: ''.join(f'<button class="chip{" on" if v == "all" else ""}" data-f="{f}" data-v="{v}">{t}</button>' for v, t in opts)
    body = f'''
<div class="hero"><div class="wrap">
<div class="kick">A FREE INTERMEDIATE SCALE & BOWING WORKBOOK</div>
<h1>100 Violin Scales</h1>
<p class="sub">Positions 1 through 5 · Every bowing · Every slur pattern</p>
<img class="staff-art" src="{D['scales'][90]['main'][0]}" alt="" style="background:#fff;border-radius:12px;padding:10px">
<p class="lead">Every scale is written out in clear notation with fingerings and bowings. Each one has a tempo goal, a play-along with metronome, a right-hand warm-up, a matching arpeggio and a practice tracker that saves your progress.</p>
<a class="btn gold" href="scale-001.html">Start with Scale 1</a> &nbsp; <a class="btn ghost" href="start.html">How to use this site</a>
<div class="stats"><div><b>100</b><span>scales</span></div><div><b>36</b><span>bowing patterns</span></div><div><b>5</b><span>positions + shifting</span></div><div><b>28</b><span>arpeggios</span></div></div>
</div></div>
<section><div class="wrap">
<div class="kicker">Choose a scale</div><h2 class="sec">All 100 Scales</h2><div class="rule"></div>
<div class="filters">
<div><label>Position</label><span class="chips">{chips('pos', [('all', 'All'), ('1', '1st'), ('2', '2nd'), ('3', '3rd'), ('4', '4th'), ('5', '5th'), ('shift', 'Shifting')])}</span></div>
<div><label>Type</label><span class="chips">{chips('mode', [('all', 'All'), ('major', 'Major'), ('minor', 'Minor')])}</span></div>
<div><label>Bowing</label><span class="chips">{chips('cat', [('all', 'All')] + [(c, c) for c in cats])}</span></div>
<div style="flex:1 1 200px"><input id="q" type="search" placeholder="Search: key, bowing, number…" style="width:100%"></div>
</div>
<p class="count" id="count"></p>
<div class="grid" id="grid"></div>
</div></section>
<section style="background:var(--soft)"><div class="wrap">
<div class="kicker">On every scale page</div><h2 class="sec">Everything you need to practice</h2><div class="rule"></div>
<div class="cards3">
<div class="card"><h3>Play-along</h3><p>Hear the scale at any tempo with an optional click and count-in, then play along.</p></div>
<div class="card"><h3>Right hand first</h3><p>The bowing pattern on an open string, so you learn the stroke before the notes.</p></div>
<div class="card"><h3>Matching arpeggio</h3><p>The arpeggio in the same key and position, ready to play right after the scale.</p></div>
<div class="card"><h3>Tempo log and checklist</h3><p>Write in your tempos and check off five quality goals. Your progress saves on your device.</p></div>
</div></div></section>'''
    page('index.html', '100 Violin Scales: Free Intermediate Violin Scales, Positions 1 to 5',
         'Free violin scales in 1st through 5th position with every bowing and slur pattern, fingerings, play-along audio, metronome and practice tracker.',
         body, 'index.html', f'<script>setupHome({json.dumps(lite)});</script>')


# ------------------------------------------------------------------ scale pages
def scale_pages():
    sc = D['scales']
    for i, s in enumerate(sc):
        n = s['num']
        prev = f'<a class="btn line" href="{fname(n - 1)}">← Scale {n - 1}</a>' if n > 1 else '<span></span>'
        nxt = f'<a class="btn wine" href="{fname(n + 1)}">Scale {n + 1} →</a>' if n < 100 else '<a class="btn wine" href="tracker.html">My Tracker →</a>'
        if s['sec_kind'] == 'arp':
            sec_t, sec_n = 'Matching arpeggio', f'Same key, same {S.ORD[s["pos"]]} position. Slur three.'
            sec_play = player(s['sec_audio'], s['sec_meter'], 40, 66)
        else:
            sec_t, sec_n = 'Slow-motion pass', 'Separate bows, every finger shown. Listen to each shift.'
            sec_play = player(s['sec_audio'], s['sec_meter'], 50, 72)
        checks = ''.join(f'<label><input type="checkbox"> {c}</label>' for c in BK.CHECKS)
        days = ''.join(f'<div>DAY {d + 1}<input inputmode="numeric" maxlength="3" placeholder="♩"></div>' for d in range(7))
        body = f'''<div class="wrap">
<div class="crumbs"><a href="index.html">All scales</a> › {posname(s)} › Scale {n}</div>
<div class="shead"><div class="num">{n}</div><div><h1>{E(s['title'])}</h1><div class="meta">{E(s['sub'])}</div></div>
<div class="right"><b>{E(s['bowing'])}</b><span>Tempo goal {E(s['tempo'])}</span></div></div>
<div class="focus"><b>TODAY'S FOCUS</b><p>{E(s['focus'])} {E(s['extra'])}</p></div>
<div class="block"><h2>The scale</h2><p class="note">Written bowing, every finger number shown.</p>
<div class="notation">{pic(s['main'], s['main_m'], E(s['title']) + ', ' + E(s['sub']) + ', ' + E(s['bowing']), s['mscale'])}</div>
{player(s['audio'], s['meter'], s['tlo'], s['thi'])}</div>
<div class="block"><h2>Right hand first</h2>
<div class="two"><p class="note" style="margin:0">Play the bowing alone on the open {s['string']} string until the stroke feels easy and the sound is even. Then play the scale.</p>
<div class="notation small"><img src="{s['rh'][0]}" alt="Bowing pattern on the open {s['string']} string"></div></div></div>
<div class="block"><h2>{sec_t}</h2><p class="note">{sec_n}</p>
<div class="notation">{pic(s['sec'], s['sec_m'], sec_t)}</div>{sec_play}</div>
<div class="block"><h2>My practice</h2><p class="note">Saved on this device. Write your best clean tempo each day; check each box when it is true.</p>
<div class="tracker"><div><div class="days">{days}</div></div><div class="checks">{checks}</div></div></div>
<div class="pn">{prev}<button class="btn line no-print" onclick="window.print()">Print this scale</button>{nxt}</div>
</div>'''
        page(fname(n), f"Scale {n}: {s['title']}, {s['sub']} – {s['bowing']} | 100 Violin Scales",
             f"Free violin scale: {s['title']}, {s['sub']}, with {s['bowing'].lower()} bowing, fingerings, play-along audio and metronome.",
             body, None, f'<script>setupPlayers();setupTracker({n});</script>')


# ------------------------------------------------------------------ getting started
HOWTO = [
    ('Play the same notes, change the bow', 'Each key appears several times with a different bowing. The notes stay familiar so your attention can go to the right arm. When a new bowing feels awkward, go back to an earlier key you already know and try it there first.'),
    ('Work in this order every time', '1. Play the scale slowly with separate bows and listen only for pitch. 2. Add the written bowing at a slow tempo. 3. Climb the metronome a few clicks at a time toward the tempo goal. 4. Finish by playing it once beautifully, as if someone were listening.'),
    ('Use the metronome ladder', 'Start at a tempo where every note is clean. Play the scale twice in a row without a mistake, then move the metronome up 4 clicks. If you miss, drop back 8 clicks and climb again. Log your best tempo on the scale page.'),
    ('Check your intonation with ringing tones', 'Every G, D, A and E you play can be checked against an open string. When the note is in tune, the open string vibrates in sympathy and the violin rings. If it sounds dull, the note is not quite in tune yet.'),
    ('Use the play-along wisely', 'Listen once before you play. Then play along softly with the click on. Finally turn the sound off and play with the metronome alone: that is the real test.'),
    ('A little every day beats a lot once a week', 'Ten to fifteen focused minutes of scales a day will change your playing more than an hour on Saturday. The Practice Plan gives you a ready-made path through all 100.'),
]


def start():
    L = D['legend']
    leg = [('img', L['down'][0], 'Down-bow', 'Pull the bow from the frog toward the tip.'),
           ('img', L['up'][0], 'Up-bow', 'Push the bow from the tip toward the frog.'),
           ('txt', '1 2 3 4', 'Finger number', '0 = open string, 1 = index, 2 = middle, 3 = ring, 4 = pinky.'),
           ('txt', '3rd pos.', 'Position', 'Shows which position to play in. Used in the shifting scales wherever the hand moves.'),
           ('img', L['stacc'][0], 'Staccato dot', 'Short. Stop the bow between notes (on the string unless it says spiccato or collé).'),
           ('img', L['ten'][0], 'Tenuto line', 'Full length. Under a slur it means louré: a gentle pulse without stopping the bow.'),
           ('img', L['acc'][0], 'Accent', 'Start the note with extra bow speed and weight, then release.'),
           ('img', L['wedge'][0], 'Martelé wedge', 'Pinch, release, stop. A biting start with silence after each note.'),
           ('txt', '⌢', 'Slur', 'All notes under the curved line are played in one bow.'),
           ('txt', '&lt; &gt;', 'Crescendo / diminuendo', 'Grow louder, or grow softer, by changing bow speed and weight.')]
    legh = ''.join(f'<div class="leg"><div class="sym">{"<img src=" + chr(34) + v + chr(34) + " alt=" + chr(34) + chr(34) + ">" if k == "img" else v}</div><div><b>{t}</b><p>{d}</p></div></div>' for k, v, t, d in leg)
    strings = [('G', 4), ('D', 1), ('A', 5), ('E', 2)]
    fb = '<div class="fb"><div></div>' + ''.join(f'<div class="h">{s} string</div>' for s, _ in strings)
    for pos in range(1, 6):
        fb += f'<div class="p">{S.ORD[pos]}</div>'
        for s, li in strings:
            fb += '<div class="cell">' + ''.join(f'<span class="fn"><i class="f{f}">{f}</i>{"CDEFGAB"[(li + pos - 1 + f) % 7]}</span>' for f in range(1, 5)) + '</div>'
    fb += '</div>'
    how = ''.join(f'<div class="card"><h3>{t}</h3><p>{b}</p></div>' for t, b in HOWTO)
    postips = ''.join(f'<tr><td><b>{S.ORD[p]}</b></td><td>{S.POS_TIPS[p]}</td></tr>' for p in range(1, 6))
    body = f'''<section><div class="wrap">
<div class="kicker">Getting started</div><h1 class="page">How to Use This Site</h1><div class="rule"></div>
<p class="intro">Scales are where tone, intonation, shifting and bow control all get built at the same time. Here is how to get the most out of every one of these 100.</p>
<div class="cards3">{how}</div></div></section>
<section style="background:var(--soft)"><div class="wrap">
<div class="kicker">Getting started</div><h2 class="sec">Reading the Markings</h2><div class="rule"></div>
<div class="legend">{legh}</div></div></section>
<section><div class="wrap">
<div class="kicker">Getting started</div><h2 class="sec">Fingerboard Map: Positions 1 to 5</h2><div class="rule"></div>
<p class="intro">The natural note under each finger, on each string, in each position. A sharp or flat uses the same finger, placed a little higher or lower.</p>
{fb}
<h3 style="color:var(--wine);margin-top:30px">Position by position</h3>
<table class="t"><tr><th>POSITION</th><th>WHAT TO KNOW</th></tr>{postips}</table>
<h3 style="color:var(--wine);margin-top:30px">Five rules for clean shifts</h3>
<ol>{''.join(f'<li>{r}</li>' for r in BK.SHIFT_RULES)}</ol>
</div></section>'''
    page('start.html', 'Getting Started: How to Use 100 Violin Scales', 'How to practice the 100 free violin scales, read the markings, and find every note in positions 1 to 5.', body, 'start.html')


def bowing():
    cards = ''
    for g in D['guide']:
        bw = S.B[g['key']]
        notes, *_ = S.build(S.scale_seq(S.parse('A4'), 'major', 1)[0][:8] + [S.parse('A5')], bw)
        ev, t = [], 0
        for n in notes:
            if t >= 24: break
            ev.append([n.p.semi + 12, n.dur]); t += n.dur
        ex = [x['num'] for x in D['scales'] if x['cat'] == bw['cat']][:6]
        exl = ', '.join(f'<a href="{fname(k)}">{k}</a>' for k in ex)
        cards += f'''<div class="gcard"><div class="ex"><img src="{g['img'][0]}" alt="{E(g['name'])} example">{player(ev, [2, 4], 60, 90, met=False, label='Hear it')}</div>
<div><div class="where">{E(g['where'])}</div><h3>{E(g['name'])}</h3><p>{E(g['how'])}</p>
<p class="watch"><b>Watch for:</b> {E(g['mistake'])} <b>Fix:</b> {E(g['fix'])}</p>
<p style="font-family:var(--sans);font-size:14px">Practice it in scales: {exl}</p></div></div>'''
    body = f'''<section><div class="wrap"><div class="kicker">Technique</div><h1 class="page">The Bowing Guide</h1><div class="rule"></div>
<p class="intro">Twelve families of strokes used on this site. Each one shows what it looks like, where in the bow it lives, the most common mistake and which scales use it.</p>
<div style="margin-top:20px">{cards}</div></div></section>'''
    page('bowing.html', 'Violin Bowing Guide: Détaché, Martelé, Spiccato, Collé and More', 'Free violin bowing guide with notation examples: détaché, legato, staccato, martelé, spiccato, collé, louré, hooked bowing and slurred staccato.', body, 'bowing.html', '<script>setupPlayers();</script>')


def arpeggios():
    rows = ''
    for a in D['arps']:
        rows += f'''<div class="block"><h2>{a['key']} {a['mode']} · {S.ORD[a['pos']]} position</h2><p class="note">Arpeggio {a['num']}</p>
<div class="notation">{pic(a['img'], a['img_m'], a['key'] + ' ' + a['mode'] + ' arpeggio')}</div>{player(a['audio'], [6, 8], 40, 66)}</div>'''
    body = f'''<section><div class="wrap"><div class="kicker">Bonus</div><h1 class="page">28 Arpeggios</h1><div class="rule"></div>
<p class="intro">Every key from the position scales as a two-octave arpeggio in the same position. Play each one right after its matching scales. Slur three, then try separate bows.</p>{rows}</div></section>'''
    page('arpeggios.html', '28 Free Violin Arpeggios in Positions 1 to 5', 'Two-octave violin arpeggios in 1st through 5th position with fingerings and play-along audio.', body, 'arpeggios.html', '<script>setupPlayers();</script>')


def rhythms():
    rows = ''
    for r in D['rhythms']:
        rows += f'''<div class="gcard"><div class="ex"><img src="{r['img'][0]}" alt="{E(r['name'])} rhythm">{player(r['audio'], [2, 4], 60, 90, met=False, label='Hear it')}</div>
<div><h3>{E(r['name'])}</h3><p>{E(r['tip'])}</p></div></div>'''
    body = f'''<section><div class="wrap"><div class="kicker">Bonus</div><h1 class="page">Rhythm Variations</h1><div class="rule"></div>
<p class="intro">Apply any of these rhythms to any scale on the site. Rhythms make the fingers move at different speeds, which exposes weak spots and makes even scales faster and cleaner.</p>
<div style="margin-top:20px">{rows}</div></div></section>'''
    page('rhythms.html', 'Violin Scale Rhythm Variations', 'Eight rhythm variations that turn any violin scale into a new exercise.', body, 'rhythms.html', '<script>setupPlayers();</script>')


def plan():
    import re
    def linkify(txt):
        m = re.match(r'Scales (\d+)–(\d+)', txt)
        return f'<a href="{fname(int(m.group(1)))}">{txt}</a>' if m else txt
    rows = ''.join(f'<tr><td><b>{w}</b></td><td>{linkify(sc)}</td><td>{bf}</td><td>{g}</td></tr>' for w, sc, bf, g in BK.PLAN)
    routine = [(3, 'Open strings with whole bows. Listen for one clean, ringing tone on each string.'),
               (5, 'Today’s scale with separate bows, slowly. Fix every note that does not ring.'),
               (7, 'The written bowing with the metronome ladder. Two clean runs, then four clicks faster.'),
               (3, 'The matching arpeggio.'),
               (2, 'One rhythm variation, then play the scale once more as music, not as an exercise.')]
    rl = ''.join(f'<li data-min="{m}"><b>{m} min</b> · {t}</li>' for m, t in routine)
    body = f'''<section><div class="wrap"><div class="kicker">Your path</div><h1 class="page">The 12-Week Plan</h1><div class="rule"></div>
<p class="intro">One week per row. Play the scales listed every day, add the matching arpeggios, and log your tempos on each scale page.</p>
<table class="t"><tr><th>WEEK</th><th>SCALES</th><th>BOWING FOCUS</th><th>GOAL</th></tr>{rows}</table></div></section>
<section style="background:var(--soft)"><div class="wrap"><div class="kicker">Every day</div><h2 class="sec">A 20-Minute Scale Routine</h2><div class="rule"></div>
<div class="card"><div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap"><div class="timer" id="tdisp">20:00</div>
<button class="btn wine" id="tgo">Start routine</button><span style="font-family:var(--sans);color:var(--grey);font-size:14px">The timer moves to the next step automatically.</span></div>
<ol class="routine">{rl}</ol></div></div></section>'''
    page('plan.html', '12-Week Violin Scale Practice Plan', 'A free 12-week plan and 20-minute daily routine with timer for 100 violin scales.', body, 'plan.html', '<script>setupTimer();</script>')


def tracker():
    lite = [dict(num=s['num'], title=s['title'], sub=s['sub'], bowing=s['bowing'], tempo=s['tempo'], thi=s['thi']) for s in D['scales']]
    body = f'''<section><div class="wrap"><div class="kicker">Your progress</div><h1 class="page">My Scale Tracker</h1><div class="rule"></div>
<p class="intro">Everything you log on the scale pages shows up here. Your progress is saved in this browser on this device.</p>
<p style="font-family:var(--sans);font-weight:600;color:var(--wine)" id="sum"></p>
<div style="overflow-x:auto"><table class="t"><tr><th>NO.</th><th>SCALE</th><th>BOWING</th><th>GOAL</th><th>BEST</th><th>CHECKS</th><th>STATUS</th></tr><tbody id="tbody"></tbody></table></div>
<p><button class="btn line" id="reset">Clear my progress</button></p></div></section>'''
    page('tracker.html', 'My Violin Scale Tracker | 100 Violin Scales', 'Track your tempos and progress across all 100 violin scales.', body, 'tracker.html', f'<script>setupTrackerPage({json.dumps(lite)});</script>')


def gear():
    secs = ''
    for cat, intro, items in BK.GEAR:
        cards = ''.join(f'<div class="gitem"><h3>{E(n)}</h3><p>{E(w)}</p><a class="btn gold" href="{E(BK.amz(q))}" target="_blank" rel="sponsored noopener">See on Amazon</a></div>' for n, w, q in items)
        secs += f'<h2 class="sec" style="font-size:28px;margin-top:24px">{cat}</h2><div class="rule"></div><p class="intro" style="font-size:18px">{E(intro)}</p><div class="ggrid">{cards}</div>'
    body = f'''<section><div class="wrap"><div class="kicker">For the intermediate violinist</div><h1 class="page">Gear Guide</h1><div class="rule"></div>
<p class="intro">Everything a violinist at this level needs, from strings and rosin to the next books to study.</p>
<div class="disclose"><b>AMAZON AFFILIATE DISCLOSURE</b>{E(BK.DISCLOSURE.replace('This book contains', 'This site contains'))}</div>
{secs}
<p class="intro" style="font-size:16px">Prices and availability change on Amazon. Ask your teacher before changing strings or a shoulder rest if you are unsure what fits your violin.</p>
</div></section>'''
    page('gear.html', 'Violin Gear Guide: Strings, Rosin, Shoulder Rests and More', 'What intermediate violinists need: strings, rosin, shoulder rests, tuners, mutes, care, bows, stands and next-step books.', body, 'gear.html')


def about():
    body = '''<section><div class="wrap" style="max-width:800px"><div class="kicker">About the author</div><h1 class="page">Bruce Bowers</h1><div class="rule"></div>
<p>Bruce Bowers has played the violin for 47 years and has taught for more than 20. He is a registered Suzuki Method teacher through Book 6, and he has performed as concertmaster, assistant concertmaster and principal second violin in local symphony orchestras.</p>
<p>He teaches Suzuki violin in the Pulaski and Green Bay area of Wisconsin, where he works with students of every age and stage, from first lessons to advanced repertoire.</p>
<p>This site brings together the scale and bowing work an intermediate player needs in one place: every position from 1st to 5th, every core bow stroke, and every common slur pattern, free for anyone to use.</p>
<div class="card" style="margin-top:24px"><h3>Thank you for practicing here</h3><p>If this site helps you, share it with a friend or your teacher. Need strings, rosin or a new shoulder rest? The <a href="gear.html">Gear Guide</a> links help keep this site free.</p></div>
</div></section>'''
    page('about.html', 'About Bruce Bowers | 100 Violin Scales', 'About Bruce Bowers, Suzuki violin teacher and author of 100 Violin Scales.', body, None)


def extras():
    urls = ['index.html', 'start.html', 'bowing.html', 'arpeggios.html', 'rhythms.html', 'plan.html', 'tracker.html', 'gear.html', 'about.html'] + [fname(n) for n in range(1, 101)]
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'<url><loc>{SITE}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n')
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')
    page('404.html', 'Page not found | 100 Violin Scales', 'Page not found.',
         '<section><div class="wrap"><h1 class="page">Page not found</h1><p><a class="btn wine" href="index.html">Go to all 100 scales</a></p></div></section>')


if __name__ == '__main__':
    home(); scale_pages(); start(); bowing(); arpeggios(); rhythms(); plan(); tracker(); gear(); about(); extras()
    print(len(os.listdir(OUT)))
