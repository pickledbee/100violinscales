"""Scale content: pitches, fingerings, bowing catalog, the 100 exercises."""
from music import P, parse, Note, keysig_alters

STRINGS = [('E', parse('E5')), ('A', parse('A4')), ('D', parse('D4')), ('G', parse('G3'))]
ROMAN = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V'}
ORD = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th'}
STEPS = {'major': [2, 2, 1, 2, 2, 2, 1], 'harmonic': [2, 1, 2, 2, 1, 3, 1],
         'melodic': [2, 1, 2, 2, 2, 2, 1], 'natural': [2, 1, 2, 2, 1, 2, 2]}
MODE_NAME = {'major': 'Major', 'harmonic': 'Harmonic Minor', 'melodic': 'Melodic Minor'}


def pretty(p):
    return 'ABCDEFG'['CDEFGAB'[p.l] and 'ABCDEFG'.index('CDEFGAB'[p.l])] + {-1: '♭', 0: '', 1: '♯'}[p.a]


def run(tonic, steps, n):
    out = [tonic]
    i = 0
    while len(out) < n:
        out.append(out[-1].up(steps[i % 7])); i += 1
    return out


def scale_seq(tonic, mode, octaves=2):
    n = 7 * octaves + 1
    up = run(tonic, STEPS[mode], n)
    if mode == 'melodic':
        down = run(tonic, STEPS['natural'], n)[::-1][1:]
    else:
        down = up[::-1][1:]
    return up, down


def fingering(p, pos, allow_open=True, string=None):
    """Return (string_name, finger) for pitch p in position pos."""
    cands = []
    for name, op in STRINGS:
        if string and name != string: continue
        f = (p.d - op.d) - (pos - 1)
        if f == 0 and pos == 1:
            if p.semi == op.semi: cands.append((name, 0))
            continue
        if 1 <= f <= 4:
            if p.semi - op.semi < 1: continue
            cands.append((name, f))
    if not cands:
        return None
    if pos == 1 and not allow_open:
        nz = [c for c in cands if c[1] != 0]
        if nz: return nz[0]
    return cands[0]


def finger_seq(pitches, positions, allow_open=True, string=None, show='changes'):
    res = []
    prev = None
    for p, pos in zip(pitches, positions):
        fs = fingering(p, pos, allow_open, string)
        if fs is None:
            raise ValueError(f'unplayable {p} in pos {pos}')
        res.append((fs[0], fs[1], pos))
    marks = []
    for i, (st, f, pos) in enumerate(res):
        if show == 'all': marks.append(f)
        elif i == 0 or st != res[i - 1][0] or pos != res[i - 1][2]: marks.append(f)
        else: marks.append(None)
    return res, marks


# ------------------------------------------------------------------ bowings
B = {}
def bowing(key, title, label, rhythm, groups, art=None, art_where='all', meter=(4, 4), dyn='mf',
           tempo='', tip='', hair=False, cat=''):
    B[key] = dict(key=key, title=title, label=label, rhythm=rhythm, groups=groups, art=art or [],
                  art_where=art_where, meter=meter, dyn=dyn, tempo=tempo, tip=tip, hair=hair, cat=cat)

Q = '♩'
bowing('DET_Q', 'Détaché, quarter notes', 'détaché', 'q', [1], tempo=f'{Q} = 60–100', cat='Détaché',
       tip='One smooth, connected stroke per note with no gaps and no accents. Keep the bow parallel to the bridge and use the same amount of bow on every note.')
bowing('DET_E', 'Détaché, eighth notes', 'détaché', 'e', [1], tempo=f'{Q} = 60–96', cat='Détaché',
       tip='Middle of the bow, about a third of the bow per note. Let the arm lead from the elbow so the string crossings are smooth, not lifted.')
bowing('DET_S', 'Fast détaché, sixteenth notes', 'détaché, middle of the bow', 's', [1], tempo=f'{Q} = 50–80', cat='Détaché',
       tip='Small strokes from the forearm with a relaxed hand. Left and right hands must change together: the finger lands exactly as the bow changes.')
bowing('WB_Q', 'Whole bows', 'whole bows, full sound', 'q', [1], art=['ten'], dyn='f', tempo=f'{Q} = 50–66', cat='Détaché',
       tip='Frog to tip on every note. Plan your bow speed so you arrive at the tip exactly on the next beat, and keep the contact point steady.')
bowing('ACC_E', 'Accented détaché', 'accented détaché', 'e', [1], art=['acc'], dyn='f', tempo=f'{Q} = 60–88', cat='Détaché',
       tip='Start each note with extra speed and weight, then release while the bow keeps moving. The accent comes from bow speed, not from squeezing.')
bowing('STAC_Q', 'On-the-string staccato', 'staccato (on the string)', 'q', [1], art=['stacc'], tempo=f'{Q} = 60–92', cat='Staccato',
       tip='Short notes with the bow staying on the string. Stop the bow after each note and let the string ring for a tiny moment of silence.')
bowing('STAC_E', 'Staccato, eighth notes', 'staccato', 'e', [1], art=['stacc'], tempo=f'{Q} = 60–92', cat='Staccato',
       tip='Short, crisp and even. The bow stays in the string; the stop between notes is as important as the note itself.')
bowing('MART_Q', 'Martelé, quarter notes', 'martelé, upper half', 'q', [1], art=['wedge'], dyn='f', tempo=f'{Q} = 50–80', cat='Martelé',
       tip='Pinch (pre-weight the string), release with a fast stroke, stop. Silence between every note. Set the weight before the note, never during it.')
bowing('MART_E', 'Martelé, eighth notes', 'martelé, upper half', 'e', [1], art=['wedge'], dyn='f', tempo=f'{Q} = 50–76', cat='Martelé',
       tip='Shorter martelé strokes in the upper half. Each note: catch, release, stop. Keep the stops completely still so every note starts clean.')
bowing('SPIC_E', 'Spiccato, eighth notes', 'spiccato, near the balance point', 'e', [1], art=['stacc'], dyn='mf', tempo=f'{Q} = 72–112', cat='Spiccato',
       tip='Let the bow drop and bounce from the air in a shallow smile shape. Use the natural bounce of the stick near the balance point, not your fingers.')
bowing('SPIC_S', 'Spiccato, sixteenth notes', 'spiccato', 's', [1], art=['stacc'], tempo=f'{Q} = 60–92', cat='Spiccato',
       tip='Lower and smaller bounces. Find the spot on the bow where it bounces by itself, then keep the stroke the same width for every note.')
bowing('SPIC_T', 'Spiccato triplets', 'spiccato', 't', [1], art=['stacc'], tempo=f'{Q} = 56–88', cat='Spiccato',
       tip='Triplets alternate the bow direction on each beat. Keep the bounce even so the down-bow beats are not louder than the up-bow beats.')
bowing('COLLE_Q', 'Collé', 'collé, at the frog', 'q', [1], art=['stacc'], tempo=f'{Q} = 50–72', cat='Collé',
       tip='Set the bow on the string at the frog, pinch with the fingers, and make a tiny, clean stroke. Lift between notes. The fingers do the work.')
bowing('LEG2_E', 'Slur 2', 'legato', 'e', [2], dyn='mf', tempo=f'{Q} = 60–96', cat='Legato',
       tip='Two notes in each bow with a seamless finger change in the middle. Keep the bow speed steady through the slur so the second note is not weaker.')
bowing('LEG2_S', 'Slur 2, sixteenth notes', 'legato', 's', [2], tempo=f'{Q} = 50–80', cat='Legato',
       tip='Short, quick slurs. Use less bow than you think, and keep the left-hand fingers falling with a firm, rhythmic tap.')
bowing('LEG3_E', 'Slur 3', 'legato', 'e', [3], meter=(6, 8), dyn='mf', tempo=f'{Q}. = 40–66', cat='Legato',
       tip='Three notes per bow, alternating down and up. Divide the bow into three equal parts so every note gets the same amount of bow.')
bowing('LEG4_E', 'Slur 4', 'legato', 'e', [4], dyn='mf', tempo=f'{Q} = 60–92', cat='Legato',
       tip='Four notes per bow. Watch the string crossings inside the slur: move the arm early and smoothly so there is no bump between strings.')
bowing('LEG4_S', 'Slur 4, sixteenth notes', 'legato', 's', [4], tempo=f'{Q} = 50–80', cat='Legato',
       tip='Each beat is one bow. Keep the sound even across all four notes and let the bow change happen exactly on the beat.')
bowing('LEG4_Q', 'Slur 4, quarter notes', 'legato, sustained', 'q', [4], dyn='p', tempo=f'{Q} = 50–72', cat='Legato',
       tip='A whole bar in one bow. Use a slow, even bow speed and a contact point closer to the bridge to keep a full, round tone at a soft dynamic.')
bowing('LEG3_T', 'Triplets, slur 3', 'legato', 't', [3], tempo=f'{Q} = 50–80', cat='Legato',
       tip='The first note is played alone, then each triplet goes in one bow. Keep the triplets exactly even, not long-short-short.')
bowing('LEG6_T', 'Triplets, slur 6', 'legato', 't', [6], tempo=f'{Q} = 50–76', cat='Legato',
       tip='Two beats in each bow. Plan your bow distribution so you do not run out on the up-bow.')
bowing('LEG7_E', 'Slur 7', 'legato', 'e', [7], dyn='mf', tempo=f'{Q} = 50–80', cat='Legato',
       tip='Seven notes per bow means the bow change lands in a new place every time. Count carefully and let the bow change be invisible.')
bowing('LEG8_S', 'Slur 8', 'legato', 's', [8], tempo=f'{Q} = 50–72', cat='Legato',
       tip='Two beats per bow. Slow bow speed, steady weight, and a clear left hand: lift the fingers as cleanly as you place them.')
bowing('LEG14_E', 'Slur 14, one bow per direction', 'legato', 'e', [14], dyn='p', hair=True, tempo=f'{Q} = 50–72', cat='Legato',
       tip='All the way up in one bow and all the way down in the next. Crescendo going up and diminuendo coming down while the bow speed stays even.')
bowing('S2S2', 'Slur 2, détaché 2', 'slur two, separate two', 's', [2, 1, 1], tempo=f'{Q} = 50–80', cat='Mixed',
       tip='The slurred pair uses the same amount of bow as each single note, so slow the bow down on the slur and speed it up on the separate notes.')
bowing('S1S2', 'Détaché 2, slur 2', 'separate two, slur two', 's', [1, 1, 2], tempo=f'{Q} = 50–80', cat='Mixed',
       tip='Watch the bow distribution: the slur moves slower than the separate notes. Keep the tone even across the whole beat.')
bowing('S1S3', 'Détaché 1, slur 3', 'one separate, three slurred', 's', [1, 3], tempo=f'{Q} = 50–80', cat='Mixed',
       tip='The single note is quick and the slur of three is slow. Same bow length for both, so the speeds must be very different.')
bowing('S3S1', 'Slur 3, détaché 1', 'three slurred, one separate', 's', [3, 1], tempo=f'{Q} = 50–80', cat='Mixed',
       tip='A classic bow-distribution pattern. Do not let the separate note pull you to the tip; return to the same part of the bow each beat.')
bowing('S2STAC', 'Slur 2, staccato 2', 'slur two, two staccato', 'e', [2, 1, 1], art=['stacc'], art_where='sep', tempo=f'{Q} = 60–88', cat='Mixed',
       tip='Smooth slur, then two short notes stopped in the string. The contrast between the legato pair and the crisp staccato is the point.')
bowing('SLST2', 'Slurred staccato pairs', 'slurred staccato', 'e', [2], art=['stacc'], art_where='slur', tempo=f'{Q} = 60–88', cat='Slurred Staccato',
       tip='Two short notes in the same bow direction with a stop between them. Stop the bow, change the finger, and go again.')
bowing('SLST4', 'Slurred staccato, 4 per bow', 'slurred staccato', 's', [4], art=['stacc'], art_where='slur', tempo=f'{Q} = 40–66', cat='Slurred Staccato',
       tip='Four little stopped strokes in one bow. Start slow and keep every stroke the same size; this builds toward up-bow staccato.')
bowing('LOURE2', 'Louré (portato), 2 per bow', 'louré (portato)', 'e', [2], art=['ten'], art_where='slur', dyn='p', tempo=f'{Q} = 50–76', cat='Louré',
       tip='Gently pulse each note inside the slur with a little release of the weight, without stopping the bow. A soft, speaking sound.')
bowing('LOURE4', 'Louré (portato), 4 per bow', 'louré (portato)', 'q', [4], art=['ten'], art_where='slur', dyn='p', tempo=f'{Q} = 50–72', cat='Louré',
       tip='Four gentle pulses in each bow. Keep the bow moving the whole time; shape each note with a slight swell of weight.')
bowing('HOOK', 'Hooked bowing', 'hooked bowing', 'd', [2], art=['stacc'], art_where='hook', tempo=f'{Q} = 50–80', cat='Hooked',
       tip='The dotted eighth and the sixteenth share one bow with a small stop before the short note. Keep the rhythm exact: the sixteenth is short and late.')
bowing('DOTSEP', 'Dotted rhythm, separate bows', 'separate bows', 'd', [1], tempo=f'{Q} = 50–76', cat='Détaché',
       tip='Long note slow bow, short note fast bow, same amount of bow for both. This trains bow-speed control better than almost anything.')
bowing('TRIP_DET', 'Détaché triplets', 'détaché', 't', [1], tempo=f'{Q} = 56–88', cat='Détaché',
       tip='Each beat starts on a new bow direction. Keep the triplets even and let the accent fall naturally, not with extra pressure.')


def build(seq, bw, fingers=None, bow_first=True, posmarks=None):
    """seq: list of pitches (29 or 15). Returns notes, slurs, hairpins, meter."""
    r = bw['rhythm']; meter = bw['meter']
    num, den = meter; bar = num * (48 // den)
    body = seq[:-1]; final = seq[-1]
    nb = len(body)
    if r == 'q': durs = [12] * nb
    elif r == 'e': durs = [6] * nb
    elif r == 's': durs = [3] * nb
    elif r == 'd': durs = [9 if i % 2 == 0 else 3 for i in range(nb)]
    elif r == 't': durs = [12] + [4] * (nb - 1)
    T = sum(durs); rem = bar - (T % bar)
    if rem not in (12, 18, 24, 36, 48):
        raise ValueError(f'bad final {rem} for {bw["key"]}')
    notes = [Note(p, d) for p, d in zip(body, durs)] + [Note(final, rem)]
    for i, n in enumerate(notes):
        if r == 't' and 1 <= i < nb: n.trip = (i - 1) // 3
    # groups
    start = 1 if r == 't' else 0
    slurs = []; i = start; gi = 0; pat = bw['groups']
    groups = []
    if start: groups.append((0, 0))
    while i < nb:
        g = pat[gi % len(pat)]; j = min(nb - 1, i + g - 1)
        groups.append((i, j)); i = j + 1; gi += 1
    groups.append((nb, nb))
    for a, b in groups:
        if b > a: slurs.append((a, b))
    inslur = set()
    for a, b in slurs:
        for k in range(a, b + 1): inslur.add(k)
    for k, n in enumerate(notes[:-1]):
        w = bw['art_where']
        if not bw['art']: break
        if w == 'all' or (w == 'sep' and k not in inslur) or (w == 'slur' and k in inslur):
            n.art = list(bw['art'])
        elif w == 'hook':
            if k % 2 == 1: n.art = list(bw['art'])
    if bw['key'] == 'WB_Q': notes[-1].art = ['ten']
    # bow marks
    if bow_first:
        notes[groups[0][0]].bow = 'down'
        if len(groups) > 1: notes[groups[1][0]].bow = 'up'
    notes[0].dyn = bw['dyn']; notes[0].text = bw['label']
    hair = []
    if bw['hair']:
        top = len(seq) // 2
        hair = [(0, top - 1, '<'), (top, nb, '>')]
    if fingers:
        for n, f in zip(notes, fingers): n.finger = f
    if posmarks:
        for n, pm in zip(notes, posmarks): n.pos = pm
    return notes, slurs, hair, meter


# ------------------------------------------------------------------ exercises
KEYS = {
    1: [('G3', 'major'), ('A3', 'major'), ('A3', 'harmonic'), ('A3', 'melodic'), ('Bb3', 'major'),
        ('B3', 'melodic'), ('G3', 'melodic'), ('G3', 'harmonic')],
    2: [('Bb3', 'major'), ('B3', 'major'), ('B3', 'harmonic'), ('C4', 'major'), ('C4', 'melodic')],
    3: [('C4', 'major'), ('C4', 'harmonic'), ('D4', 'major'), ('D4', 'melodic'), ('D4', 'harmonic')],
    4: [('D4', 'major'), ('Eb4', 'major'), ('E4', 'major'), ('E4', 'melodic'), ('D4', 'harmonic')],
    5: [('E4', 'major'), ('E4', 'harmonic'), ('F4', 'major'), ('F4', 'melodic'), ('Eb4', 'major')],
}
COUNTS = {1: [3, 3, 3, 3, 3, 3, 2, 2], 2: [3, 3, 3, 3, 2], 3: [4, 3, 3, 3, 3], 4: [3, 3, 3, 3, 3], 5: [3, 3, 3, 3, 3]}
MASTER = ['DET_Q', 'LEG2_E', 'DET_E', 'STAC_Q', 'LEG4_E', 'MART_Q', 'LEG3_E', 'DET_S', 'LEG4_S', 'SPIC_E',
          'S2S2', 'LOURE2', 'HOOK', 'LEG3_T', 'S1S3', 'WB_Q', 'ACC_E', 'SLST2', 'S3S1', 'MART_E', 'LEG7_E',
          'TRIP_DET', 'LEG8_S', 'S1S2', 'SPIC_S', 'COLLE_Q', 'DOTSEP', 'LEG6_T', 'SLST4', 'S2STAC', 'LOURE4',
          'SPIC_T', 'LEG14_E', 'LEG2_S', 'STAC_E', 'LEG4_Q']
START = {1: 0, 2: 22, 3: 3, 4: 19, 5: 30}

POS_TIPS = {
    1: 'Ringing-tone check: every G, D, A and E you play should make the matching open string vibrate in sympathy.',
    2: 'In 2nd position your 1st finger sits where your 2nd finger used to be in 1st position. Keep the thumb opposite the 1st or 2nd finger.',
    3: 'In 3rd position the heel of your hand lightly touches the violin body. Use that contact as your guide for every shift into 3rd.',
    4: 'In 4th position your 1st finger plays the same note as the next string up in 1st position (open string pitch, one string higher). Check it.',
    5: 'In 5th position the hand starts to come around the shoulder of the violin. Bring the thumb partly under the neck and keep the elbow forward.',
}


def two_oct_names(tonic, mode):
    t = parse(tonic)
    return f"{pretty(t)} {MODE_NAME[mode]}"


def make_exercises():
    ex = []
    for pos in range(1, 6):
        k = START[pos]
        for (ton, mode), cnt in zip(KEYS[pos], COUNTS[pos]):
            t = parse(ton)
            up, down = scale_seq(t, mode)
            seq = up + down
            for j in range(cnt):
                bk = MASTER[k % len(MASTER)]; k += 1
                allow_open = True
                res, marks = finger_seq(seq, [pos] * len(seq), allow_open, show='all' if j == 0 else 'changes')
                ex.append(dict(kind='pos', pos=pos, tonic=t, mode=mode, seq=seq, bow=bk, fingers=marks,
                               title=f"{two_oct_names(ton, mode)}", sub=f"{ORD[pos]} Position, two octaves",
                               strings=res))
    return ex


ONE_STRING = [('G', 'G3', 'major'), ('D', 'D4', 'major'), ('A', 'A4', 'major'), ('E', 'E5', 'major'),
              ('G', 'G3', 'melodic'), ('D', 'D4', 'melodic'), ('A', 'A4', 'melodic'), ('E', 'E5', 'harmonic')]
ONE_BOWS = ['DET_Q', 'LEG2_E', 'LEG4_E', 'LEG7_E', 'DET_E', 'STAC_Q', 'LOURE2', 'MART_Q']
SHIFT2 = [  # tonic, mode, plan [(from_index, position)], bowing
    ('D4', 'major', [(0, 1), (8, 3)], 'LEG4_S'),
    ('C4', 'major', [(0, 1), (9, 3)], 'DET_E'),
    ('Bb3', 'major', [(0, 1), (10, 3)], 'LEG2_E'),
    ('E4', 'major', [(0, 1), (7, 3), (13, 4)], 'S3S1'),
    ('Eb4', 'major', [(0, 1), (8, 4)], 'LEG4_E'),
    ('F4', 'major', [(0, 1), (5, 3), (12, 5)], 'LEG8_S'),
    ('D4', 'melodic', [(0, 1), (8, 3)], 'S2S2'),
    ('C4', 'melodic', [(0, 1), (9, 3)], 'LEG3_T'),
    ('E4', 'melodic', [(0, 1), (7, 3), (13, 4)], 'SPIC_E'),
    ('F4', 'harmonic', [(0, 1), (5, 3), (12, 5)], 'LEG7_E'),
]


def plan_positions(n_up, plan):
    pos = []
    for i in range(n_up):
        p = [pp for (a, pp) in plan if a <= i][-1]
        pos.append(p)
    return pos


def make_shift_exercises():
    ex = []
    for (st, ton, mode), bk in zip(ONE_STRING, ONE_BOWS):
        t = parse(ton)
        up, down = scale_seq(t, mode, 1)
        seq = up + down
        upos = [1, 1, 1, 3, 3, 3, 5, 5]
        posl = upos + upos[::-1][1:]
        res, marks = finger_seq(seq, posl, string=st, show='all')
        pm = [None] * len(seq)
        for i in range(len(seq)):
            if i == 0 or posl[i] != posl[i - 1]: pm[i] = ORD[posl[i]] + ' pos.'
        ex.append(dict(kind='one', pos=None, tonic=t, mode=mode, seq=seq, bow=bk, fingers=marks, posmarks=pm,
                       title=f"{two_oct_names(ton, mode)} on the {st} String", sub="One octave on one string: 1st, 3rd and 5th positions",
                       strings=res))
    for ton, mode, plan, bk in SHIFT2:
        t = parse(ton)
        up, down = scale_seq(t, mode, 2)
        seq = up + down
        upos = plan_positions(15, plan)
        posl = upos + upos[::-1][1:]
        res, marks = finger_seq(seq, posl)
        # show finger on every shift and string change; also note before shift
        pm = [None] * len(seq)
        for i in range(len(seq)):
            if i == 0 or posl[i] != posl[i - 1]: pm[i] = ORD[posl[i]] + ' pos.'
        names = ' → '.join(ORD[p] for _, p in plan)
        ex.append(dict(kind='shift', pos=None, tonic=t, mode=mode, seq=seq, bow=bk, fingers=marks, posmarks=pm,
                       title=f"{two_oct_names(ton, mode)}", sub=f"Two octaves with shifts: {names} position",
                       strings=res, plan=plan))
    return ex


def arpeggios():
    out = []
    for pos in range(1, 6):
        for ton, mode in KEYS[pos]:
            t = parse(ton)
            up, _ = scale_seq(t, 'harmonic' if mode != 'major' else 'major')
            idx = [0, 2, 4, 7, 9, 11, 14]
            a_up = [up[i] for i in idx]
            seq = a_up + a_up[::-1][1:]
            res, marks = finger_seq(seq, [pos] * len(seq), show='all')
            out.append(dict(pos=pos, tonic=t, mode=mode, seq=seq, fingers=marks, ton=ton))
    return out


def out_keys(out):
    return [(o['ton'], o['mode']) for o in out]


if __name__ == '__main__':
    exs = make_exercises() + make_shift_exercises()
    print(len(exs))
    for i, e in enumerate(exs, 1):
        print(i, e['title'], '|', e['sub'], '|', e['bow'])
        print('   ', ' '.join(f"{p.name()}:{s}{f}" for p, (s, f, pp) in zip(e['seq'][:15], e['strings'][:15])))
    for a in arpeggios():
        print('ARP', a['ton'], a['mode'], a['pos'], a['fingers'])
