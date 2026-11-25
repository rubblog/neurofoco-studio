/* NeuroFoco Studio - motor de audio en tiempo real (Web Audio API, 100 % offline) */
(function () {
  'use strict';
  const NOTAS = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  function notaHz(n) {
    let alt = 0, r = n.slice(1);
    if (r[0] === '#') { alt = 1; r = r.slice(1); } else if (r[0] === 'b') { alt = -1; r = r.slice(1); }
    const midi = 12 * (parseInt(r, 10) + 1) + NOTAS[n[0]] + alt;
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  class NFEngine {
    constructor() {
      this.ctx = null; this.master = null; this.escena = null; this.vol = 0.6;
      this.mezcla = { lecho: 1, aire: 1, pad: 1, prof: 1, campanas: 1 };
      this.hzUsuario = null; this.timerPlan = null;
    }

    iniciar() {
      if (this.ctx) { if (this.ctx.state === 'suspended') this.ctx.resume(); return; }
      const AC = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AC({ latencyHint: 'playback' });
      const c = this.ctx;
      this.master = c.createGain();
      this.master.gain.value = this._curva(this.vol);
      this.limit = c.createDynamicsCompressor();
      this.limit.threshold.value = -8; this.limit.knee.value = 6; this.limit.ratio.value = 12;
      this.limit.attack.value = 0.005; this.limit.release.value = 0.25;
      this.analyser = c.createAnalyser(); this.analyser.fftSize = 2048; this.analyser.smoothingTimeConstant = 0.82;
      this.master.connect(this.limit); this.limit.connect(this.analyser); this.analyser.connect(c.destination);
      this.ruido = { rosa: this._bufferRuido('rosa', 40), marron: this._bufferRuido('marron', 40) };
      this.timerPlan = setInterval(() => this.escena && this.escena.planificar(), 4000);
    }

    _curva(v) { return 0.9 * Math.pow(Math.max(0, Math.min(1, v)), 1.6); }
    setVolumen(v) { this.vol = v; if (this.master) this.master.gain.setTargetAtTime(this._curva(v), this.ctx.currentTime, 0.05); }

    // ---- Ruido con bucle sin costuras (fundido de potencia constante) ----
    _bufferRuido(tipo, seg) {
      const c = this.ctx, fs = c.sampleRate, N = Math.floor(seg * fs), X = Math.floor(3 * fs);
      const buf = c.createBuffer(2, N, fs);
      for (let ch = 0; ch < 2; ch++) {
        const x = new Float32Array(N + X);
        if (tipo === 'rosa') {
          let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
          for (let i = 0; i < x.length; i++) {
            const w = Math.random() * 2 - 1;
            b0 = 0.99886 * b0 + w * 0.0555179; b1 = 0.99332 * b1 + w * 0.0750759;
            b2 = 0.96900 * b2 + w * 0.1538520; b3 = 0.86650 * b3 + w * 0.3104856;
            b4 = 0.55000 * b4 + w * 0.5329522; b5 = -0.7616 * b5 - w * 0.0168980;
            x[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362; b6 = w * 0.115926;
          }
        } else {
          let y = 0;
          for (let i = 0; i < x.length; i++) { y = 0.998 * y + (Math.random() * 2 - 1) * 0.05; x[i] = y; }
        }
        const out = buf.getChannelData(ch);
        for (let i = 0; i < N; i++) out[i] = x[i];
        for (let i = 0; i < X; i++) {            // cierra el bucle: el final enlaza con el inicio
          const u = i / X, wi = Math.sin(0.5 * Math.PI * u), wo = Math.cos(0.5 * Math.PI * u);
          out[i] = x[N + i] * wo + x[i] * wi;
        }
        let s = 0; for (let i = 0; i < N; i++) s += out[i] * out[i];
        const k = 0.2 / Math.sqrt(s / N);        // RMS 0,2
        for (let i = 0; i < N; i++) out[i] *= k;
      }
      return buf;
    }

    // ---- Escena (un modo completo) ----
    reproducir(modoId, fade = 3) {
      this.iniciar();
      const nueva = new Escena(this, window.NF_MODOS[modoId]);
      const t = this.ctx.currentTime;
      nueva.out.gain.setValueAtTime(0, t);
      nueva.out.gain.linearRampToValueAtTime(1, t + fade);
      if (this.escena) this.escena.detener(fade);
      this.escena = nueva;
      return nueva;
    }

    parar(fade = 2) { if (this.escena) { this.escena.detener(fade); this.escena = null; } }
    pausar() { if (this.ctx && this.ctx.state === 'running') return this.ctx.suspend(); }
    reanudar() { if (this.ctx && this.ctx.state === 'suspended') return this.ctx.resume(); }

    setMezcla(clave, v) {
      this.mezcla[clave] = v;
      if (this.escena) this.escena.aplicarMezcla();
    }

    // ---- Campanas tipo cuenco ----
    campana(tipo) {
      this.iniciar();
      const c = this.ctx, t0 = c.currentTime + 0.05;
      const golpes = tipo === 'trabajo' ? [[0, 392.0, 1], [1.15, 587.33, 0.85]]
        : tipo === 'descanso' ? [[0, 261.63, 1], [0.02, 130.81, 0.45]] : [[0, 392.0, 1]];
      const PARC = [1, 2.76, 5.40, 8.93], AMP = [1, 0.45, 0.20, 0.08], TAU = [3.2, 2.0, 1.1, 0.6];
      const nivel = 0.22 * this.mezcla.campanas;
      const bus = c.createGain(); bus.gain.value = nivel; bus.connect(this.master);
      const fin = tipo === 'descanso' ? 12 : 10;
      for (const [ini, f0, a] of golpes) {
        PARC.forEach((p, k) => {
          const f = f0 * p; if (f > 9000) return;
          [[-1, 0.6], [1, -0.6]].forEach(([pan, det]) => {
            const o = c.createOscillator(); o.type = 'sine'; o.frequency.value = f + det;
            const g = c.createGain(); const ts = t0 + ini;
            g.gain.setValueAtTime(0, ts);
            g.gain.linearRampToValueAtTime(AMP[k] * a * 0.5, ts + 0.03);
            g.gain.setTargetAtTime(0, ts + 0.03, TAU[k]);
            const pn = c.createStereoPanner(); pn.pan.value = pan * 0.35;
            o.connect(g); g.connect(pn); pn.connect(bus);
            o.start(ts); o.stop(ts + fin);
          });
        });
      }
      setTimeout(() => { try { bus.disconnect(); } catch (e) { /* ya liberado */ } }, (fin + 2) * 1000);
    }

    espectro(arr) { if (this.analyser) this.analyser.getByteFrequencyData(arr); }
  }

  class Escena {
    constructor(eng, modo) {
      this.eng = eng; this.m = modo; const c = eng.ctx;
      this.out = c.createGain(); this.out.gain.value = 1; this.out.connect(eng.master);
      this.nodos = []; this.fuentes = [];
      const trim = c.createGain(); trim.gain.value = 0.45; trim.connect(this.out); this.trim = trim;

      // Lecho marrón
      const sLecho = c.createBufferSource(); sLecho.buffer = eng.ruido.marron; sLecho.loop = true;
      const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 900; lp.Q.value = 0.7;
      this.gLecho = c.createGain(); this.amLecho = c.createGain();
      sLecho.connect(lp); lp.connect(this.amLecho); this.amLecho.connect(this.gLecho); this.gLecho.connect(trim);
      // Aire rosa
      const sAire = c.createBufferSource(); sAire.buffer = eng.ruido.rosa; sAire.loop = true;
      sAire.loopStart = 0;
      const hp = c.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 180;
      const lp2 = c.createBiquadFilter(); lp2.type = 'lowpass'; lp2.frequency.value = 5200;
      this.gAire = c.createGain(); this.amAire = c.createGain();
      sAire.connect(hp); hp.connect(lp2); lp2.connect(this.amAire); this.amAire.connect(this.gAire); this.gAire.connect(trim);
      const t = c.currentTime;
      sLecho.start(t, Math.random() * 20); sAire.start(t, Math.random() * 20);
      this.fuentes.push(sLecho, sAire);

      // Pad: dos capas (A/B) que se funden de forma continua
      this.padBus = c.createGain(); this.amPad = c.createGain();
      const padLp = c.createBiquadFilter(); padLp.type = 'lowpass'; padLp.frequency.value = modo.padCut; padLp.Q.value = 0.6;
      this.gPad = c.createGain();
      this.padBus.connect(padLp); padLp.connect(this.amPad); this.amPad.connect(this.gPad); this.gPad.connect(trim);
      this.capas = [this._capaPad(), this._capaPad()];

      // Modulación de amplitud (coseno elevado): ganancia base + oscilador
      this.am = c.createOscillator(); this.am.type = 'sine'; this.am.start(t); this.fuentes.push(this.am);
      this.amPads = []; this.amNodos = [[this.amLecho, 0.4], [this.amAire, 1], [this.amPad, 1]].map(([nodo, k]) => {
        const d = c.createGain(); this.am.connect(d); d.connect(nodo.gain); return { nodo, d, k };
      });

      // Cadena de acordes
      this.t0 = t; this.k = 0; this.sigInicio = t;
      this._asignar(this.capas[0], this.m.acordes[0], t);
      this.capas[0].g.gain.setValueAtTime(1, t); this.capas[1].g.gain.setValueAtTime(0, t);
      this.aplicarMezcla(true);
      this.planificar();
    }

    _capaPad() {
      const c = this.eng.ctx, g = c.createGain(); g.gain.value = 0; g.connect(this.padBus);
      const voces = [];
      const PAN = [-0.6, -0.2, 0.2, 0.6], TREM = [0.037, 0.052, 0.061, 0.043];
      for (let k = 0; k < 4; k++) {
        const vg = c.createGain(); vg.gain.value = 1;
        const pn = c.createStereoPanner(); pn.pan.value = PAN[k];
        vg.connect(pn); pn.connect(g);
        const lfo = c.createOscillator(); lfo.frequency.value = TREM[k];
        const lg = c.createGain(); lg.gain.value = 0.15; lfo.connect(lg); lg.connect(vg.gain); lfo.start();
        const oscs = [[0.99826, 0.5], [1.00173, 0.5], [2, 0.25]].map(([r, a]) => {
          const o = c.createOscillator(); o.type = 'sine'; o.frequency.value = 220;
          const og = c.createGain(); og.gain.value = a * 0.55; o.connect(og); og.connect(vg); o.start();
          this.fuentes.push(o); return { o, r };
        });
        this.fuentes.push(lfo);
        voces.push(oscs);
      }
      return { g, voces };
    }

    _asignar(capa, acorde, t) {
      acorde.forEach((n, k) => { const f = notaHz(n); capa.voces[k].forEach(({ o, r }) => o.frequency.setValueAtTime(f * r, t)); });
    }

    planificar() {
      const c = this.eng.ctx, L = this.m.segAcorde;
      if (this.m.gains.pad <= 0) return;
      if (this.sigInicio < c.currentTime - L) this.sigInicio = c.currentTime;
      const N = 64, ent = new Float32Array(N), sal = new Float32Array(N);
      for (let i = 0; i < N; i++) { const u = i / (N - 1); sal[i] = Math.pow(Math.cos(0.5 * Math.PI * u), 2); ent[i] = Math.pow(Math.sin(0.5 * Math.PI * u), 2); }
      while (this.sigInicio < c.currentTime + 100) {
        const ts = this.sigInicio, kk = this.k, A = this.capas[kk % 2], B = this.capas[(kk + 1) % 2];
        const tIni = Math.max(c.currentTime + 0.02, ts + 0.01);
        this._asignar(B, this.m.acordes[(kk + 1) % this.m.acordes.length], tIni);
        A.g.gain.setValueCurveAtTime(sal, tIni, L - 0.03);
        B.g.gain.setValueCurveAtTime(ent, tIni, L - 0.03);
        this.k++; this.sigInicio += L;
      }
    }

    aplicarMezcla() {
      const c = this.eng.ctx, t = c.currentTime, mz = this.eng.mezcla, g = this.m.gains, m = this.m;
      this.gLecho.gain.setTargetAtTime(g.lecho * mz.lecho, t, 0.1);
      this.gAire.gain.setTargetAtTime(g.aire * mz.aire, t, 0.1);
      this.gPad.gain.setTargetAtTime(g.pad * mz.pad, t, 0.1);
      const hz = this.eng.hzUsuario != null && m.hz > 0 ? this.eng.hzUsuario : m.hz;
      const prof = Math.min(0.9, m.depth * mz.prof);
      this.am.frequency.setTargetAtTime(hz > 0 ? hz : 0.0001, t, 0.1);
      this.amNodos.forEach(({ nodo, d, k }) => {
        const p = hz > 0 ? prof * k : 0, norm = 1 / (1 - p / 2);
        // env = (1 - p/2 + (p/2) * (-cos)) / (1 - p/2); osc sin ≈ modulación coseno sin importar la fase
        nodo.gain.setTargetAtTime((1 - p / 2) * norm, t, 0.1);
        d.gain.setTargetAtTime((p / 2) * norm, t, 0.1);
      });
    }

    detener(fade) {
      const c = this.eng.ctx, t = c.currentTime;
      this.out.gain.cancelScheduledValues(t);
      this.out.gain.setValueAtTime(this.out.gain.value, t);
      this.out.gain.linearRampToValueAtTime(0, t + fade);
      setTimeout(() => {
        this.fuentes.forEach((s) => { try { s.stop(); } catch (e) { /* ya parada */ } });
        try { this.out.disconnect(); } catch (e) { /* ya liberado */ }
      }, (fade + 0.5) * 1000);
    }
  }

  window.NFEngine = NFEngine;
})();
