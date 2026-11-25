/* NeuroFoco Studio - interfaz: Pomodoro, mezcla y diario */
(function () {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const MODOS = window.NF_MODOS;
  const eng = new window.NFEngine();
  const LS = 'neurofoco.v1';
  const CIRC = 553; // 2·π·88

  // ---------------------------------------------------------------- estado
  const cfg = Object.assign({ modo: 'beta', trabajo: 25, descanso: 5, ciclos: 4, preset: '25,5', vol: 60,
    lecho: 100, aire: 100, pad: 100, prof: 100, camp: 100, tema: 'oscuro' }, JSON.parse(localStorage.getItem(LS + '.cfg') || '{}'));
  const S = { estado: 'idle', fase: 'trabajo', ciclo: 1, finFase: 0, durFase: 0, restante: 0, libre: false,
    t0Libre: 0, ultimoTick: 0, segTrabajo: 0, pendienteValorar: null };
  const guardarCfg = () => localStorage.setItem(LS + '.cfg', JSON.stringify(cfg));

  // ---------------------------------------------------------------- tema claro/oscuro
  function aplicarTema() {
    const claro = cfg.tema === 'claro';
    document.body.classList.toggle('claro', claro);
    const bt = $('#btn-tema');
    if (bt) bt.textContent = claro ? '🌙 Oscuro' : '☀️ Claro';
  }
  const btnTema = $('#btn-tema');
  if (btnTema) btnTema.addEventListener('click', () => { cfg.tema = cfg.tema === 'claro' ? 'oscuro' : 'claro'; guardarCfg(); aplicarTema(); });
  aplicarTema();

  // ---------------------------------------------------------------- pestañas
  $$('.tab').forEach((b) => b.addEventListener('click', () => {
    $$('.tab').forEach((x) => x.classList.toggle('active', x === b));
    $$('.panel').forEach((p) => p.classList.toggle('active', p.id === 'tab-' + b.dataset.tab));
  }));

  // ---------------------------------------------------------------- modos
  function pintarModos() {
    const g = $('#grid-modos'); g.innerHTML = '';
    Object.values(MODOS).forEach((m) => {
      const b = document.createElement('button');
      b.className = 'modo' + (m.id === cfg.modo ? ' sel' : ''); b.style.setProperty('--c', m.color); b.dataset.id = m.id;
      b.innerHTML = `<span class="st" title="Respaldo científico (resumen divulgativo)">${'★'.repeat(m.estrellas)}${'☆'.repeat(5 - m.estrellas)}</span>
        <div class="ic">${m.icono}</div><h3>${m.nombre}</h3>
        <div class="hz">${m.hz ? m.banda + ' · ' + m.hz + ' Hz' : m.banda}</div><p>${m.resumen}</p>
        <p><em>${m.uso}</em></p>`;
      b.addEventListener('click', () => elegirModo(m.id));
      g.appendChild(b);
    });
  }
  function elegirModo(id) {
    cfg.modo = id; guardarCfg(); pintarModos(); colorFase();
    if (S.estado === 'run' && S.fase === 'trabajo') { eng.hzUsuario = hzUsr(); eng.reproducir(id, 3); aplicarMezclaUI(); }
  }
  function colorFase() {
    const c = S.fase === 'descanso' ? MODOS.theta.color : MODOS[cfg.modo].color;
    $('#card-timer').style.setProperty('--c', c);
  }

  // ---------------------------------------------------------------- presets
  function aplicarPreset(p) {
    cfg.preset = p;
    if (p === 'libre') { S.libre = true; } else {
      S.libre = false; const [w, d] = p.split(',').map(Number); cfg.trabajo = w; cfg.descanso = d;
      $('#in-trabajo').value = w; $('#in-descanso').value = d;
    }
    $$('#presets .chip').forEach((c) => c.classList.toggle('sel', c.dataset.p === p));
    $('#in-trabajo').disabled = $('#in-descanso').disabled = $('#in-ciclos').disabled = (p === 'libre');
    guardarCfg(); if (S.estado === 'idle') mostrarInactivo();
  }
  $$('#presets .chip').forEach((c) => c.addEventListener('click', () => { if (S.estado === 'idle') aplicarPreset(c.dataset.p); }));
  ['#in-trabajo', '#in-descanso'].forEach((s) => $(s).addEventListener('change', () => {
    if (S.estado !== 'idle') return;
    cfg.trabajo = Math.max(1, Math.min(180, +$('#in-trabajo').value || 25));
    cfg.descanso = Math.max(1, Math.min(60, +$('#in-descanso').value || 5));
    $('#in-trabajo').value = cfg.trabajo; $('#in-descanso').value = cfg.descanso;
    $$('#presets .chip').forEach((c) => c.classList.remove('sel')); cfg.preset = 'custom'; guardarCfg(); mostrarInactivo();
  }));
  $('#in-ciclos').addEventListener('change', () => { cfg.ciclos = +$('#in-ciclos').value; guardarCfg(); mostrarInactivo(); });

  // ---------------------------------------------------------------- temporizador
  const fmt = (s) => { s = Math.max(0, Math.round(s)); const m = Math.floor(s / 60); return String(m).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); };
  function mostrarInactivo() {
    $('#fase-lbl').textContent = 'Listo';
    $('#tiempo').textContent = S.libre ? '00:00' : fmt(cfg.trabajo * 60);
    $('#ciclo-lbl').textContent = S.libre ? 'Sesión continua' : 'Ciclo 1 de ' + (cfg.ciclos || '∞');
    $('#anillo-prog').style.strokeDashoffset = CIRC; document.title = 'NeuroFoco Studio · Sonido de estudio';
  }
  function botones() {
    const run = S.estado !== 'idle';
    $('#btn-start').textContent = S.estado === 'run' ? '⏸ Pausa' : (S.estado === 'pausa' ? '▶ Reanudar' : '▶ Empezar');
    $('#btn-pausa').disabled = $('#btn-skip').disabled = $('#btn-stop').disabled = !run;
    $('#btn-pausa').textContent = S.estado === 'pausa' ? '▶ Reanudar' : '⏸ Pausa';
    $('#btn-skip').disabled = !run || S.libre;
  }
  function iniciarFase(fase, conCampana) {
    S.fase = fase; colorFase();
    S.durFase = (fase === 'trabajo' ? cfg.trabajo : cfg.descanso) * 60 * 1000;
    S.finFase = Date.now() + S.durFase;
    if (conCampana) eng.campana(fase === 'trabajo' ? 'trabajo' : 'descanso');
    eng.hzUsuario = fase === 'trabajo' ? hzUsr() : null;
    eng.reproducir(fase === 'trabajo' ? cfg.modo : 'theta', conCampana ? 4 : 2.5);
    aplicarMezclaUI();
    $('#fase-lbl').textContent = fase === 'trabajo' ? 'Trabajo' : 'Descanso';
  }
  function empezar() {
    eng.iniciar(); eng.setVolumen(cfg.vol / 100); $('#aviso-audio').hidden = true;
    S.estado = 'run'; S.ciclo = 1; S.segTrabajo = 0; S.ultimoTick = Date.now(); $('#valoracion').hidden = true;
    if (S.libre) {
      S.fase = 'trabajo'; S.t0Libre = Date.now(); colorFase(); eng.campana('inicio');
      eng.hzUsuario = hzUsr(); eng.reproducir(cfg.modo, 4); aplicarMezclaUI(); $('#fase-lbl').textContent = 'Continua';
    } else iniciarFase('trabajo', true);
    botones();
  }
  function pausar() {
    if (S.estado === 'run') { S.estado = 'pausa'; S.restante = S.libre ? Date.now() - S.t0Libre : S.finFase - Date.now(); eng.pausar(); $('#fase-lbl').textContent = 'En pausa'; }
    else if (S.estado === 'pausa') {
      S.estado = 'run'; S.ultimoTick = Date.now();
      if (S.libre) S.t0Libre = Date.now() - S.restante; else S.finFase = Date.now() + S.restante;
      eng.reanudar(); $('#fase-lbl').textContent = S.libre ? 'Continua' : (S.fase === 'trabajo' ? 'Trabajo' : 'Descanso');
    }
    botones();
  }
  function terminar(completa) {
    const minTrab = Math.round(S.segTrabajo / 60);
    if (S.estado !== 'idle') { registrarFoco(S.segTrabajo); eng.parar(2.5); if (completa) eng.campana('trabajo'); }
    S.estado = 'idle'; S.segTrabajo = 0; botones(); mostrarInactivo(); colorFase(); pintarStats();
    if (minTrab >= 5 && !(S.pendienteValorar)) pedirValoracion(cfg.modo);
  }
  function siguienteFase() {
    if (S.fase === 'trabajo') {
      if (cfg.ciclos && S.ciclo >= cfg.ciclos) { $('#fase-lbl').textContent = '¡Completado!'; pedirValoracion(cfg.modo); terminar(true); return; }
      pedirValoracion(cfg.modo); iniciarFase('descanso', true);
    } else { S.ciclo++; iniciarFase('trabajo', true); }
  }
  function tick() {
    const ahora = Date.now();
    if (S.estado === 'run') {
      const dt = (ahora - S.ultimoTick) / 1000; S.ultimoTick = ahora;
      if (S.fase === 'trabajo') S.segTrabajo += dt;
      if (S.libre) {
        const el = (ahora - S.t0Libre) / 1000; $('#tiempo').textContent = fmt(el);
        $('#ciclo-lbl').textContent = 'Tiempo transcurrido'; $('#anillo-prog').style.strokeDashoffset = CIRC * (1 - (el % 3600) / 3600);
        document.title = fmt(el) + ' · NeuroFoco';
      } else {
        const rem = (S.finFase - ahora) / 1000;
        $('#tiempo').textContent = fmt(rem); $('#ciclo-lbl').textContent = 'Ciclo ' + S.ciclo + ' de ' + (cfg.ciclos || '∞');
        $('#anillo-prog').style.strokeDashoffset = CIRC * (1 - Math.max(0, Math.min(1, 1 - rem * 1000 / S.durFase)));
        document.title = fmt(rem) + ' · ' + (S.fase === 'trabajo' ? 'Trabajo' : 'Descanso');
        if (rem <= 0) siguienteFase();
      }
    }
  }
  setInterval(tick, 250);

  $('#btn-start').addEventListener('click', () => { if (S.estado === 'idle') empezar(); else pausar(); });
  $('#btn-pausa').addEventListener('click', pausar);
  $('#btn-skip').addEventListener('click', () => { if (S.estado !== 'idle' && !S.libre) { S.finFase = Date.now(); siguienteFase(); } });
  $('#btn-stop').addEventListener('click', () => terminar(false));
  document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !/INPUT|SELECT|TEXTAREA|BUTTON|SUMMARY/.test(document.activeElement.tagName)) {
      e.preventDefault(); if (S.estado === 'idle') empezar(); else pausar();
    }
  });

  // ---------------------------------------------------------------- mezcla
  function hzUsr() { return $('#chk-hz').checked ? +$('#r-hz').value : null; }
  function aplicarMezclaUI() {
    eng.mezcla = { lecho: cfg.lecho / 100, aire: cfg.aire / 100, pad: cfg.pad / 100, prof: cfg.prof / 100, campanas: cfg.camp / 100 };
    eng.hzUsuario = S.fase === 'trabajo' ? hzUsr() : null;
    if (eng.escena) eng.escena.aplicarMezcla();
  }
  [['vol', 'r-vol', 'o-vol'], ['lecho', 'r-lecho', 'o-lecho'], ['aire', 'r-aire', 'o-aire'], ['pad', 'r-pad', 'o-pad'],
    ['prof', 'r-prof', 'o-prof'], ['camp', 'r-camp', 'o-camp']].forEach(([k, r, o]) => {
    const el = $('#' + r); el.value = cfg[k]; $('#' + o).textContent = cfg[k];
    el.addEventListener('input', () => {
      cfg[k] = +el.value; $('#' + o).textContent = el.value; guardarCfg();
      if (k === 'vol') eng.setVolumen(cfg.vol / 100); else aplicarMezclaUI();
    });
  });
  $('#chk-hz').addEventListener('change', () => { $('#r-hz').disabled = !$('#chk-hz').checked; aplicarMezclaUI(); });
  $('#r-hz').addEventListener('input', () => { $('#o-hz').textContent = $('#r-hz').value; aplicarMezclaUI(); });
  [['#btn-camp-trabajo', 'trabajo'], ['#btn-camp-descanso', 'descanso']].forEach(([sel, tipo]) => {
    const el = $(sel);
    if (el) el.addEventListener('click', () => { eng.iniciar(); eng.setVolumen(cfg.vol / 100); aplicarMezclaUI(); eng.campana(tipo); });
  });

  // ---------------------------------------------------------------- visualizador (sin parpadeos: nada se sincroniza con la AM)
  const cv = $('#viz'), cx = cv.getContext('2d'), datos = new Uint8Array(1024);
  function dibujar(t) {
    const w = cv.width, h = cv.height; cx.clearRect(0, 0, w, h);
    const color = getComputedStyle($('#card-timer')).getPropertyValue('--c').trim() || '#38bdf8';
    if (eng.analyser && S.estado === 'run') eng.espectro(datos); else datos.fill(0);
    const barras = 72, ancho = w / barras;
    for (let i = 0; i < barras; i++) {
      const idx = Math.floor(Math.pow(i / barras, 2) * 520) + 2;
      const v = datos[idx] / 255, alto = Math.max(2, v * (h - 12));
      cx.fillStyle = color; cx.globalAlpha = 0.25 + 0.75 * v;
      cx.fillRect(i * ancho + 2, h - alto - 4, ancho - 4, alto);
    }
    cx.globalAlpha = 1;
    requestAnimationFrame(dibujar);
  }
  requestAnimationFrame(dibujar);

  // ---------------------------------------------------------------- diario / estadísticas (solo localStorage)
  const hoy = () => new Date().toISOString().slice(0, 10);
  const leer = () => JSON.parse(localStorage.getItem(LS + '.diario') || '{"min":{},"bloques":{},"val":[]}');
  const escribir = (d) => localStorage.setItem(LS + '.diario', JSON.stringify(d));
  function registrarFoco(seg) {
    if (seg < 30) return; const d = leer(); d.min[hoy()] = (d.min[hoy()] || 0) + seg / 60;
    d.bloques[hoy()] = (d.bloques[hoy()] || 0) + (seg >= 300 ? 1 : 0); escribir(d);
  }
  function pedirValoracion(modo) { S.pendienteValorar = modo; $('#valoracion').hidden = false; }
  $$('#valoracion button').forEach((b) => b.addEventListener('click', () => {
    const d = leer(); d.val.push({ fecha: new Date().toISOString(), modo: S.pendienteValorar || cfg.modo, nota: +b.dataset.v,
      trabajo: cfg.trabajo, descanso: cfg.descanso });
    escribir(d); S.pendienteValorar = null; $('#valoracion').hidden = true; pintarStats();
  }));
  function pintarStats() {
    const d = leer();
    $('#st-hoy').textContent = Math.round(d.min[hoy()] || 0); $('#st-sesiones').textContent = d.bloques[hoy()] || 0;
    const agg = {}; d.val.forEach((v) => { (agg[v.modo] = agg[v.modo] || []).push(v.nota); });
    let mejor = null, mm = 0; Object.entries(agg).forEach(([m, a]) => { const x = a.reduce((p, c) => p + c, 0) / a.length; if (a.length >= 3 && x > mm) { mm = x; mejor = m; } });
    $('#st-mejor').textContent = mejor ? MODOS[mejor].nombre.split(' ')[0] + ' (' + mm.toFixed(1) + ')' : '—';
    const t = $('#tabla-diario');
    if (!d.val.length) { t.innerHTML = '<div class="vacio">Aún no hay valoraciones. Al terminar un bloque aparecerá una pregunta de 1 a 5.</div>'; return; }
    t.innerHTML = '<table class="tabla"><thead><tr><th>Modo</th><th>Bloques valorados</th><th>Media (1-5)</th></tr></thead><tbody>' +
      Object.entries(agg).sort((a, b) => b[1].length - a[1].length).map(([m, a]) => `<tr><td>${MODOS[m].icono} ${MODOS[m].nombre}</td><td>${a.length}</td><td>${(a.reduce((p, c) => p + c, 0) / a.length).toFixed(2)}</td></tr>`).join('') + '</tbody></table>';
  }
  $('#btn-csv').addEventListener('click', () => {
    const d = leer(); const csv = 'fecha,modo,nota,trabajo_min,descanso_min\n' + d.val.map((v) => [v.fecha, v.modo, v.nota, v.trabajo, v.descanso].join(',')).join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'neurofoco_diario.csv'; a.click();
  });
  $('#btn-borrar').addEventListener('click', () => { if (confirm('¿Borrar todo el diario de valoraciones?')) { localStorage.removeItem(LS + '.diario'); pintarStats(); } });

  // ---------------------------------------------------------------- init
  pintarModos(); aplicarPreset(cfg.preset === 'custom' ? '25,5' : cfg.preset);
  if (cfg.preset === 'custom') { $('#in-trabajo').value = cfg.trabajo; $('#in-descanso').value = cfg.descanso; }
  $('#in-ciclos').value = String(cfg.ciclos); colorFase(); botones(); mostrarInactivo(); pintarStats();
  window.NF_DEBUG = { eng, S, cfg };
})();
