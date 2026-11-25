/* 100 Violin Scales: menu, audio play-along, metronome, tracker storage */
(function () {
  var btn = document.querySelector('.menu-btn'), nav = document.querySelector('.nav');
  if (btn) btn.addEventListener('click', function () { nav.classList.toggle('open'); });
})();

/* ---------- storage (per browser) ---------- */
var Store = {
  key: 'v100-tracker',
  all: function () { try { return JSON.parse(localStorage.getItem(this.key) || '{}'); } catch (e) { return {}; } },
  get: function (n) { var a = this.all(); return a[n] || { log: ['', '', '', '', '', '', ''], checks: [false, false, false, false, false] }; },
  set: function (n, v) { try { var a = this.all(); a[n] = v; localStorage.setItem(this.key, JSON.stringify(a)); } catch (e) { } },
  clear: function () { try { localStorage.removeItem(this.key); } catch (e) { } }
};

/* ---------- audio ---------- */
var Audio = (function () {
  var ctx = null, live = [], timers = [];
  function ac() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }
  function freq(m) { return 440 * Math.pow(2, (m - 69) / 12); }
  function tone(m, t, d, out) {
    var c = ac(), g = c.createGain(), f = c.createBiquadFilter();
    f.type = 'lowpass'; f.frequency.value = 2600; f.Q.value = 0.8;
    var o1 = c.createOscillator(), o2 = c.createOscillator();
    o1.type = 'sawtooth'; o2.type = 'sawtooth';
    o1.frequency.value = freq(m); o2.frequency.value = freq(m) * 1.003;
    var lfo = c.createOscillator(), lg = c.createGain();
    lfo.frequency.value = 5.4; lg.gain.value = freq(m) * 0.0035;
    lfo.connect(lg); lg.connect(o1.frequency); lg.connect(o2.frequency);
    o1.connect(f); o2.connect(f); f.connect(g); g.connect(out);
    var end = t + Math.max(0.08, d * 0.94);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(0.16, t + 0.035);
    g.gain.setValueAtTime(0.14, Math.max(t + 0.04, end - 0.05));
    g.gain.linearRampToValueAtTime(0, end);
    [o1, o2, lfo].forEach(function (o) { o.start(t); o.stop(end + 0.02); live.push(o); });
  }
  function click(t, accent, out) {
    var c = ac(), o = c.createOscillator(), g = c.createGain();
    o.type = 'square'; o.frequency.value = accent ? 1600 : 1050;
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(accent ? 0.22 : 0.14, t + 0.002);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
    o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.06); live.push(o);
  }
  function stop() {
    live.forEach(function (o) { try { o.stop(); } catch (e) { } }); live = [];
    timers.forEach(clearTimeout); timers = [];
  }
  /* events: [[midi, ticks]] with 12 ticks = quarter; meter [num, den] */
  function play(events, bpm, meter, opts) {
    stop(); var c = ac(), out = c.createGain(); out.gain.value = 0.9; out.connect(c.destination);
    var beatTicks = meter[1] === 8 ? 18 : 12;
    var barTicks = meter[0] * (48 / meter[1]);
    var sec = 60 / (bpm * beatTicks);
    var t0 = c.currentTime + 0.12, lead = 0;
    if (opts.countIn) {
      var beats = barTicks / beatTicks;
      for (var b = 0; b < beats; b++) click(t0 + b * beatTicks * sec, b === 0, out);
      lead = barTicks * sec;
    }
    var start = t0 + lead, t = 0, total = 0;
    events.forEach(function (e) { total += e[1]; });
    events.forEach(function (e) { tone(e[0], start + t * sec, e[1] * sec, out); t += e[1]; });
    if (opts.click) for (var k = 0; k <= total; k += beatTicks) click(start + k * sec, k % barTicks === 0, out);
    var dur = (lead + total * sec) * 1000 + 300;
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
    stop(); metroOn = true; var c = ac(), out = c.createGain(); out.connect(c.destination);
    var beatTicks = meter[1] === 8 ? 18 : 12, beats = meter[0] * (48 / meter[1]) / beatTicks;
    var period = 60 / bpm, next = c.currentTime + 0.1, i = 0;
    (function sched() {
      if (!metroOn) return;
      while (next < c.currentTime + 0.25) { click(next, i % beats === 0, out); next += period; i++; }
      timers.push(setTimeout(sched, 50));
    })();
  }
  function metroStop() { metroOn = false; stop(); }
  return { play: play, stop: stop, metro: metro, metroStop: metroStop };
})();

/* ---------- player widgets ---------- */
function setupPlayers() {
  document.querySelectorAll('.player').forEach(function (p) {
    var ev = JSON.parse(p.dataset.events), meter = JSON.parse(p.dataset.meter);
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
      Audio.metroStop(); playing = true; play.textContent = '■ Stop';
      Audio.play(ev, +range.value, meter, {
        click: clickBox && clickBox.checked, countIn: countBox && countBox.checked,
        onProgress: function (x) { bar.style.width = (x * 100) + '%'; }, onEnd: reset
      });
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
