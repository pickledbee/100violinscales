/* 100 Violin Scales: menu, audio play-along, metronome, tracker storage */
(function () {
  var btn = document.querySelector('.menu-btn'), nav = document.querySelector('.nav');
  if (btn) btn.addEventListener('click', function () { nav.classList.toggle('open'); });
})();

/* ---------- analytics events ---------- */
function track(name, params) { try { if (typeof gtag === 'function') gtag('event', name, params || {}); } catch (e) { } }
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[rel~="sponsored"]');
  if (a) { var card = a.closest('.gitem'); track('amazon_click', { item_name: card ? card.querySelector('h3').textContent : a.href, link_url: a.href }); }
});

/* ---------- storage (per browser) ---------- */
var Store = {
  key: 'v100-tracker',
  all: function () { try { return JSON.parse(localStorage.getItem(this.key) || '{}'); } catch (e) { return {}; } },
  get: function (n) { var a = this.all(); return a[n] || { log: ['', '', '', '', '', '', ''], checks: [false, false, false, false, false] }; },
  set: function (n, v) { try { var a = this.all(); a[n] = v; localStorage.setItem(this.key, JSON.stringify(a)); } catch (e) { } },
  clear: function () { try { localStorage.removeItem(this.key); } catch (e) { } }
};

/* ---------- audio: bowed-string violin model ---------- */
var Audio = (function () {
  var ctx = null, live = [], timers = [], chain = null, wave = null, noiseBuf = null;
  function ac() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === 'suspended' && ctx.resume) { try { var r = ctx.resume(); if (r && r.catch) r.catch(function () { }); } catch (e) { } }
    return ctx;
  }
  function freq(m) { return 440 * Math.pow(2, (m - 69) / 12); }

  /* Bowed string: sawtooth-like Helmholtz motion. Bowing at about 1/9 of the string
     length notches every 9th harmonic, which is what gives a real violin its colour. */
  function violinWave(c) {
    var N = 48, re = new Float32Array(N + 1), im = new Float32Array(N + 1), beta = 1 / 9.2;
    for (var n = 1; n <= N; n++) {
      var comb = Math.abs(Math.sin(Math.PI * n * beta)) / Math.sin(Math.PI * beta);
      im[n] = (1 / n) * (0.35 + 0.65 * comb) * (n > 24 ? Math.pow(0.93, n - 24) : 1);
    }
    return c.createPeriodicWave(re, im);
  }
  function impulse(c, secs, decay) {
    var len = Math.floor(c.sampleRate * secs), buf = c.createBuffer(2, len, c.sampleRate);
    for (var ch = 0; ch < 2; ch++) {
      var d = buf.getChannelData(ch), lp = 0;
      for (var i = 0; i < len; i++) {
        var t = i / len, x = (Math.random() * 2 - 1) * Math.pow(1 - t, decay);
        lp += (x - lp) * (0.45 - 0.35 * t);  /* darker as the room tail fades */
        d[i] = i < c.sampleRate * 0.012 ? 0 : lp;
      }
    }
    return buf;
  }
  function getChain() {
    if (chain) return chain;
    var c = ac();
    wave = violinWave(c);
    noiseBuf = c.createBuffer(1, c.sampleRate * 2, c.sampleRate);
    var nd = noiseBuf.getChannelData(0);
    for (var i = 0; i < nd.length; i++) nd[i] = Math.random() * 2 - 1;
    var input = c.createGain();
    /* violin body: air mode, main wood modes, nasal dip, bridge hill, top roll-off */
    var specs = [['highpass', 185, 0.7, 0], ['peaking', 285, 2.2, 5], ['peaking', 470, 2.8, 4], ['peaking', 560, 3, 2.5],
                 ['peaking', 1150, 1.2, -3], ['peaking', 2400, 1.6, 4.5], ['peaking', 3100, 1.8, 3.5],
                 ['peaking', 4600, 1.5, -4], ['lowpass', 7800, 0.6, 0]];
    var node = input;
    specs.forEach(function (sp) {
      var f = c.createBiquadFilter(); f.type = sp[0]; f.frequency.value = sp[1]; f.Q.value = sp[2];
      if (sp[0] === 'peaking') f.gain.value = sp[3];
      node.connect(f); node = f;
    });
    var comp = c.createDynamicsCompressor();
    comp.threshold.value = -16; comp.ratio.value = 3; comp.attack.value = 0.01; comp.release.value = 0.25;
    var dry = c.createGain(); dry.gain.value = 0.82;
    var rev = c.createConvolver(); rev.buffer = impulse(c, 2.4, 3.2);
    var wet = c.createGain(); wet.gain.value = 0.32;
    var mix = c.createGain(); node.connect(mix);
    mix.connect(dry); dry.connect(comp);
    mix.connect(rev); rev.connect(wet); wet.connect(comp);
    var master = c.createGain(); master.gain.value = 0.9;
    comp.connect(master); master.connect(c.destination);
    chain = { input: input, mix: mix, master: master, wet: wet };
    return chain;
  }

  /* One bow stroke = one oscillator. Notes inside a slur change pitch on the same
     oscillator, so legato is truly connected; separate bows get a new stroke. */
  function stroke(notes, out, dyn, sec, startT) {
    var c = ac(), L = 0.2 * dyn;
    var t0 = notes[0].t, tEnd = notes[notes.length - 1].t + notes[notes.length - 1].d;
    var osc = c.createOscillator(); osc.setPeriodicWave(wave);
    var amp = c.createGain(); amp.gain.value = 0;
    /* vibrato and a little natural pitch drift, in cents */
    var vib = c.createOscillator(), vg = c.createGain();
    vib.frequency.value = 5.3 + Math.random() * 0.7; vg.gain.value = 0;
    var drift = c.createOscillator(), dg = c.createGain();
    drift.frequency.value = 0.4 + Math.random() * 0.5; dg.gain.value = 2.5;
    vib.connect(vg); vg.connect(osc.detune); drift.connect(dg); dg.connect(osc.detune);
    /* bow noise: rosin hiss that follows the stroke, plus a bite at each attack */
    var nz = c.createBufferSource(); nz.buffer = noiseBuf; nz.loop = true;
    var bp = c.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 2600; bp.Q.value = 0.9;
    var ng = c.createGain(); ng.gain.value = 0;
    nz.connect(bp); bp.connect(ng); ng.connect(out);
    osc.connect(amp); amp.connect(out);
    /* rosin hiss shaped by the string's own motion, so it follows every stroke */
    var hissG = c.createGain(); hissG.gain.value = 0; bp.connect(hissG); amp.connect(hissG.gain);
    var hs = c.createGain(); hs.gain.value = 0.3; hissG.connect(hs); hs.connect(out);
    var g = amp.gain, n = ng.gain, v = vg.gain;
    g.setValueAtTime(0, t0); n.setValueAtTime(0, t0); v.setValueAtTime(0, t0);
    notes.forEach(function (nt, i) {
      var t = nt.t, d = nt.d, f = freq(nt.m), a = nt.a, first = (i === 0);
      if (first) { osc.frequency.setValueAtTime(f * 0.996, t); osc.frequency.setTargetAtTime(f, t, 0.02); }
      else osc.frequency.setTargetAtTime(f, t, a === 'ss' ? 0.004 : 0.012);
      /* vibrato blooms on longer notes, stays narrow on fast ones */
      var vmax = d > 0.5 ? 17 : d > 0.25 ? 12 : 5;
      v.setTargetAtTime(3, t, 0.02);
      v.setTargetAtTime(vmax, t + Math.min(0.18, d * 0.35), Math.max(0.05, d * 0.25));
      var end = t + d;
      function bite(k, len) { n.setValueAtTime(L * k, t); n.setTargetAtTime(0, t + 0.005, len); }
      if (!first && (a === '' || a === 'te' || a === 'ac')) {
        /* connected note in a slur: tiny finger articulation, no new attack */
        g.setTargetAtTime(L * 0.9, t, 0.01); g.setTargetAtTime(L, t + 0.03, 0.03);
        return;
      }
      if (!first && a === 'lo') { g.setTargetAtTime(L * 0.55, t - 0.02, 0.012); g.setTargetAtTime(L, t + 0.02, 0.04); g.setTargetAtTime(L * 0.78, t + d * 0.55, d * 0.3); return; }
      if (a === 'ss') {
        g.setTargetAtTime(L, t, 0.008); bite(0.35, 0.02);
        g.setTargetAtTime(0, t + Math.max(0.05, d * 0.5), 0.012); return;
      }
      if (first && a === 'lo') { g.setTargetAtTime(L, t, 0.03); bite(0.2, 0.03); g.setTargetAtTime(L * 0.78, t + d * 0.55, d * 0.3); return; }
      if (a === 'ma') {
        g.setValueAtTime(0, t); g.linearRampToValueAtTime(L * 1.55, t + 0.008); g.setTargetAtTime(L * 0.75, t + 0.01, 0.05);
        bite(0.9, 0.025); g.setTargetAtTime(0, t + Math.min(d * 0.6, 0.45), 0.015); return;
      }
      if (a === 'sp') {
        g.setValueAtTime(0, t); g.linearRampToValueAtTime(L * 1.05, t + 0.004); g.setTargetAtTime(0, t + 0.01, Math.min(0.045, d * 0.3));
        bite(0.7, 0.012); return;
      }
      if (a === 'cl') {
        g.setValueAtTime(0, t); g.linearRampToValueAtTime(L * 0.9, t + 0.003); g.setTargetAtTime(0, t + 0.008, 0.025);
        bite(1.0, 0.01); return;
      }
      if (a === 'st') {
        g.setTargetAtTime(L, t, 0.012); bite(0.45, 0.02); g.setTargetAtTime(0, t + Math.max(0.06, d * 0.5), 0.015); return;
      }
      if (a === 'ac') {
        g.setValueAtTime(0, t); g.linearRampToValueAtTime(L * 1.45, t + 0.012); g.setTargetAtTime(L * 0.9, t + 0.015, 0.07);
        bite(0.6, 0.03); return;
      }
      /* plain détaché / first note of a slur / tenuto: smooth bow start */
      g.setTargetAtTime(L * (a === 'te' ? 1.05 : 1), t, d < 0.2 ? 0.012 : 0.03); bite(d < 0.2 ? 0.3 : 0.4, 0.035);
    });
    /* end of the bow: brief release before the bow changes direction */
    var last = notes[notes.length - 1].a;
    if (['ma', 'sp', 'cl', 'st', 'ss'].indexOf(last) < 0) g.setTargetAtTime(0, tEnd - Math.min(0.035, (tEnd - t0) * 0.15), 0.012);
    n.setTargetAtTime(0, tEnd - 0.02, 0.02);
    [osc, vib, drift, nz].forEach(function (o) { o.start(Math.max(c.currentTime, t0 - 0.01)); o.stop(tEnd + 0.3); live.push(o); });
  }

  /* ---------- real violin recordings (VSCO-2 via tonejs-instruments, CC BY 3.0) ---------- */
  var SAMPLES = [['G3',55,-1.7,0.018],['A3',57,-1.2,0.009],['C4',60,2.0,0.046],['E4',64,0.4,0.019],['G4',67,3.2,0.101],['A4',69,11.7,0.04],['C5',72,5.9,0.053],['E5',76,14.0,0.039],['G5',79,4.7,0.042],['A5',81,3.5,0.032],['C6',84,-6.6,0.066],['E6',88,11.5,0.059],['G6',91,9.0,0.031],['A6',93,10.0,0.01]];
  var bufs = {}, loading = null, ready = false;
  function load() {
    if (ready) return Promise.resolve(true);
    if (loading) return loading;
    var c = ac();
    loading = Promise.all(SAMPLES.map(function (sm) {
      return fetch('samples/violin/' + sm[0] + '.mp3').then(function (r) { return r.arrayBuffer(); }).then(function (ab) {
        return new Promise(function (res, rej) { c.decodeAudioData(ab, function (b) { bufs[sm[0]] = b; res(); }, rej); });
      });
    })).then(function () { ready = true; return true; }).catch(function () { loading = null; return false; });
    return loading;
  }
  function nearest(m) {
    var best = SAMPLES[0];
    SAMPLES.forEach(function (sm) { if (Math.abs(sm[1] - m) < Math.abs(best[1] - m) || (Math.abs(sm[1] - m) === Math.abs(best[1] - m) && sm[1] < best[1])) best = sm; });
    return best;
  }
  function voiceNote(m, t, d, offset, out, env, crisp) {
    var c = ac(), sm = nearest(m), buf = bufs[sm[0]];
    if (crisp) offset = Math.max(offset, sm[3] + 0.012);
    var src = c.createBufferSource(); src.buffer = buf;
    src.detune.value = (m - sm[1]) * 100 - sm[2];
    var g = c.createGain(); g.gain.value = 0;
    src.connect(g); g.connect(out);
    var rate = Math.pow(2, src.detune.value / 1200);
    if ((offset + d * rate) > buf.duration - 0.6) { src.loop = true; src.loopStart = 1.6; src.loopEnd = buf.duration - 0.7; }
    env(g.gain);
    src.start(Math.max(c.currentTime, t), offset); src.stop(t + d + 0.4); live.push(src);
  }
  function sampledStroke(notes, out, dyn) {
    var L = 0.95 * dyn;
    notes.forEach(function (nt, i) {
      var t = nt.t, d = nt.d, a = nt.a, first = (i === 0), last = (i === notes.length - 1);
      var connected = !first && (a === '' || a === 'te' || a === 'ac' || a === 'lo');
      var tail = last ? 0.03 : 0.045;   /* bow change vs. finger change */
      var off, env;
      if (connected) {
        off = 0.16;
        env = function (g) {
          var lv = a === 'lo' ? L * 0.82 : L;
          g.setValueAtTime(0, t - 0.012); g.linearRampToValueAtTime(lv, t + 0.03);
          if (a === 'lo') g.setTargetAtTime(L * 0.7, t + d * 0.5, d * 0.3);
          g.setTargetAtTime(0, t + d - 0.006, tail * 0.5);
        };
      } else if (a === 'ma') {
        off = 0.012;
        env = function (g) { g.setValueAtTime(L * 1.45, t); g.setTargetAtTime(L * 0.8, t + 0.02, 0.05); g.setTargetAtTime(0, t + Math.min(d * 0.6, 0.45), 0.014); };
      } else if (a === 'sp') {
        off = 0.02;
        env = function (g) { g.setValueAtTime(L * 1.15, t); g.setTargetAtTime(0, t + 0.012, Math.min(0.045, d * 0.28)); };
      } else if (a === 'cl') {
        off = 0.02;
        env = function (g) { g.setValueAtTime(L * 1.05, t); g.setTargetAtTime(0, t + 0.01, 0.024); };
      } else if (a === 'st' || a === 'ss') {
        off = a === 'ss' && !first ? 0.06 : 0.015;
        env = function (g) { g.setValueAtTime(0, t); g.linearRampToValueAtTime(L * (a === 'ss' ? 0.92 : 1), t + 0.012); g.setTargetAtTime(0, t + Math.max(0.06, d * 0.5), 0.016); };
      } else if (a === 'ac') {
        off = 0.01;
        env = function (g) { g.setValueAtTime(L * 1.4, t); g.setTargetAtTime(L * 0.95, t + 0.02, 0.07); g.setTargetAtTime(0, t + d - 0.006, tail * 0.5); };
      } else {
        off = d < 0.2 ? 0.025 : 0;
        env = function (g) {
          g.setValueAtTime(0, t); g.linearRampToValueAtTime(L * (a === 'te' ? 1.05 : 1), t + (d < 0.2 ? 0.012 : 0.02));
          if (a === 'lo') g.setTargetAtTime(L * 0.75, t + d * 0.5, d * 0.3);
          g.setTargetAtTime(0, t + d - 0.006, tail * 0.5);
        };
      }
      voiceNote(nt.m, t, d, off, out, env, !connected && ['ma', 'sp', 'cl', 'st', 'ss', 'ac'].indexOf(a) >= 0 || (!connected && d < 0.2));
    });
  }
  function click(t, accent, out) {
    var c = ac(), o = c.createOscillator(), g = c.createGain();
    o.type = 'triangle'; o.frequency.value = accent ? 1760 : 1320;
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(accent ? 0.3 : 0.18, t + 0.002);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.045);
    o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.06); live.push(o);
  }
  function stop() {
    live.forEach(function (o) { try { o.stop(); } catch (e) { } }); live = [];
    timers.forEach(clearTimeout); timers = [];
  }
  /* events: [midi, ticks, strokeId, articulation]; 12 ticks = quarter note */
  function play(events, bpm, meter, opts) {
    stop(); var c = ac(), ch = getChain();
    var voice = c.createGain(); voice.gain.value = 1; voice.connect(ready ? ch.mix : ch.input);
    ch.wet.gain.value = ready ? 0.2 : 0.32;
    var clickOut = c.createGain(); clickOut.gain.value = 0.8; clickOut.connect(c.destination);
    var beatTicks = meter[1] === 8 ? 18 : 12, barTicks = meter[0] * (48 / meter[1]);
    var sec = 60 / (bpm * beatTicks), t0 = c.currentTime + 0.15, lead = 0;
    if (opts.countIn) {
      for (var b = 0; b < barTicks / beatTicks; b++) click(t0 + b * beatTicks * sec, b === 0, clickOut);
      lead = barTicks * sec;
    }
    var start = t0 + lead, t = 0, strokes = [], cur = null, total = 0;
    events.forEach(function (e, i) {
      var sid = e.length > 2 ? e[2] : i, art = e.length > 3 ? e[3] : '';
      var nt = { m: e[0], t: start + t * sec, d: e[1] * sec, a: art };
      if (!cur || cur.sid !== sid) { cur = { sid: sid, notes: [] }; strokes.push(cur); }
      cur.notes.push(nt); t += e[1];
    });
    total = t;
    var dyn = opts.dyn || 0.8;
    strokes.forEach(function (s) { if (ready) sampledStroke(s.notes, voice, dyn); else stroke(s.notes, voice, dyn, sec, start); });
    if (opts.click) for (var k = 0; k <= total; k += beatTicks) click(start + k * sec, k % barTicks === 0, clickOut);
    var dur = (lead + total * sec) * 1000 + 600;
    if (opts.onProgress) {
      var st = performance.now();
      (function tick() {
        var p = Math.min(1, (performance.now() - st) / dur);
        opts.onProgress(p);
        if (p < 1) timers.push(setTimeout(tick, 60));
      })();
    }
    timers.push(setTimeout(function () { if (opts.onEnd) opts.onEnd(); }, dur));
  }
  var metroOn = false;
  function metro(bpm, meter) {
    stop(); metroOn = true; var c = ac(), out = c.createGain(); out.gain.value = 0.8; out.connect(c.destination);
    var beatTicks = meter[1] === 8 ? 18 : 12, beats = meter[0] * (48 / meter[1]) / beatTicks;
    var period = 60 / bpm, next = c.currentTime + 0.1, i = 0;
    (function sched() {
      if (!metroOn) return;
      while (next < c.currentTime + 0.25) { click(next, i % beats === 0, out); next += period; i++; }
      timers.push(setTimeout(sched, 50));
    })();
  }
  function metroStop() { metroOn = false; stop(); }
  return { play: play, stop: stop, metro: metro, metroStop: metroStop, load: load, isReady: function () { return ready; } };
})();

/* ---------- player widgets ---------- */
function setupPlayers() {
  document.querySelectorAll('.player').forEach(function (p) {
    var ev = JSON.parse(p.dataset.events), meter = JSON.parse(p.dataset.meter), dyn = +(p.dataset.dyn || 0.8);
    var range = p.querySelector('input[type=range]'), bpm = p.querySelector('.bpm');
    var play = p.querySelector('.play'), met = p.querySelector('.met');
    var clickBox = p.querySelector('.clk'), countBox = p.querySelector('.cnt'), bar = p.querySelector('.prog i');
    var unit = meter[1] === 8 ? '♩. = ' : '♩ = ';
    function show() { bpm.textContent = unit + range.value; }
    range.addEventListener('input', show); show();
    var playing = false, ticking = false;
    function reset() { playing = false; ticking = false; play.textContent = '▶ Play'; if (met) met.textContent = 'Metronome'; bar.style.width = '0'; }
    play.addEventListener('click', function () {
      if (playing) { Audio.stop(); reset(); return; }
      document.querySelectorAll('.player').forEach(function (q) { if (q !== p && q._reset) q._reset(); });
      Audio.metroStop(); playing = true;
      var go = function () {
        if (!playing) return;
        play.textContent = '■ Stop';
        Audio.play(ev, +range.value, meter, {
          click: clickBox && clickBox.checked, countIn: countBox && countBox.checked, dyn: dyn,
          onProgress: function (x) { bar.style.width = (x * 100) + '%'; }, onEnd: reset
        });
      };
      track('play_scale', { page_title: document.title, tempo: +range.value });
      if (Audio.isReady()) go();
      else { play.textContent = 'Loading violin…'; Audio.load().then(go); }
    });
    if (met) met.addEventListener('click', function () {
      if (ticking) { Audio.metroStop(); reset(); return; }
      document.querySelectorAll('.player').forEach(function (q) { if (q !== p && q._reset) q._reset(); });
      Audio.stop(); ticking = true; met.textContent = '■ Stop metronome'; play.textContent = '▶ Play';
      Audio.metro(+range.value, meter);
    });
    p._reset = function () { Audio.stop(); Audio.metroStop(); reset(); };
  });
}

/* ---------- scale page tracker ---------- */
function setupTracker(n) {
  var box = document.querySelector('.tracker'); if (!box) return;
  var v = Store.get(n);
  box.querySelectorAll('.days input').forEach(function (inp, i) {
    inp.value = v.log[i] || '';
    inp.addEventListener('input', function () { v.log[i] = inp.value.replace(/[^0-9]/g, ''); Store.set(n, v); });
  });
  box.querySelectorAll('.checks input').forEach(function (cb, i) {
    cb.checked = !!v.checks[i];
    cb.addEventListener('change', function () { v.checks[i] = cb.checked; Store.set(n, v); });
  });
}

/* ---------- home filters ---------- */
function setupHome(data) {
  var state = { pos: 'all', mode: 'all', cat: 'all', q: '' };
  var grid = document.getElementById('grid'), count = document.getElementById('count');
  var all = Store.all();
  function render() {
    var q = state.q.toLowerCase();
    var list = data.filter(function (s) {
      if (state.pos !== 'all') { if (state.pos === 'shift' ? s.pos !== null : String(s.pos) !== state.pos) return false; }
      if (state.mode !== 'all' && (state.mode === 'major') !== (s.mode === 'major')) return false;
      if (state.cat !== 'all' && s.cat !== state.cat) return false;
      if (q && (s.title + ' ' + s.bowing + ' ' + s.sub + ' ' + s.num).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    count.textContent = list.length + (list.length === 1 ? ' scale' : ' scales');
    grid.innerHTML = list.map(function (s) {
      var r = all[s.num], done = r && r.checks && r.checks.every(Boolean);
      return '<a class="scard" href="scale-' + ('00' + s.num).slice(-3) + '.html"><div class="num">' + s.num + '</div><div><h3>' + s.title +
        (done ? '<span class="done-badge">mastered</span>' : '') + '</h3><div class="meta">' + s.sub + '</div><div class="bow">' + s.bowing + '</div></div></a>';
    }).join('');
  }
  document.querySelectorAll('[data-f]').forEach(function (ch) {
    ch.addEventListener('click', function () {
      var f = ch.dataset.f;
      document.querySelectorAll('[data-f="' + f + '"]').forEach(function (x) { x.classList.remove('on'); });
      ch.classList.add('on'); state[f] = ch.dataset.v; render();
    });
  });
  document.getElementById('q').addEventListener('input', function (e) { state.q = e.target.value; render(); });
  render();
}

/* ---------- tracker page ---------- */
function setupTrackerPage(data) {
  var body = document.getElementById('tbody'), all = Store.all(), mastered = 0, started = 0;
  body.innerHTML = data.map(function (s) {
    var r = all[s.num] || { log: [], checks: [] };
    var best = Math.max.apply(null, [0].concat((r.log || []).map(function (x) { return +x || 0; })));
    var nchk = (r.checks || []).filter(Boolean).length;
    var status = nchk === 5 ? 'Mastered' : (best || nchk ? 'In progress' : 'Not started');
    if (nchk === 5) mastered++; if (best || nchk) started++;
    var goal = best >= s.thi ? ' ✓' : '';
    return '<tr><td><b>' + s.num + '</b></td><td><a href="scale-' + ('00' + s.num).slice(-3) + '.html">' + s.title + '</a><br><small>' + s.sub +
      '</small></td><td>' + s.bowing + '</td><td>' + s.tempo + '</td><td>' + (best || '–') + goal + '</td><td>' + nchk + '/5</td><td>' + status + '</td></tr>';
  }).join('');
  document.getElementById('sum').textContent = mastered + ' mastered · ' + started + ' started · ' + (100 - started) + ' not started yet';
  document.getElementById('reset').addEventListener('click', function () {
    if (confirm('Clear all your saved tempos and checklists on this device?')) { Store.clear(); location.reload(); }
  });
}

/* ---------- practice timer ---------- */
function setupTimer() {
  var steps = Array.prototype.slice.call(document.querySelectorAll('.routine li'));
  if (!steps.length) return;
  var disp = document.getElementById('tdisp'), go = document.getElementById('tgo'), idx = -1, left = 0, iv = null;
  function fmt(s) { return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function next() {
    steps.forEach(function (li) { li.classList.remove('now'); });
    idx++;
    if (idx >= steps.length) { clearInterval(iv); iv = null; idx = -1; disp.textContent = 'Done!'; go.textContent = 'Start routine'; return; }
    steps[idx].classList.add('now'); left = +steps[idx].dataset.min * 60; disp.textContent = fmt(left);
  }
  go.addEventListener('click', function () {
    if (iv) { clearInterval(iv); iv = null; go.textContent = 'Resume'; return; }
    if (idx < 0) next();
    go.textContent = 'Pause';
    iv = setInterval(function () { left--; disp.textContent = fmt(Math.max(0, left)); if (left <= 0) next(); }, 1000);
  });
}
