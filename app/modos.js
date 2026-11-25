/* NeuroFoco Studio - definicion de modos (espejo de motor/neurofoco_dsp.py) */
window.NF_MODOS = {
  beta: {
    id: 'beta', nombre: 'Foco profundo', icono: '🎯', hz: 16, banda: 'Beta', depth: 0.42,
    gains: { lecho: 1.0, aire: 0.50, pad: 0.42 }, padCut: 2200, segAcorde: 64,
    acordes: [['D3','A3','E4','F#4'], ['B2','F#3','D4','E4'], ['G2','D3','A3','B3'], ['A2','E3','B3','C#4']],
    color: '#38bdf8', estrellas: 3,
    resumen: 'Modulación rápida de amplitud a 16 Hz sobre ruido cálido y pad suave.',
    uso: 'Estudio técnico, problemas, supuestos prácticos, redacción exigente. Bloques de 25-50 min.',
    evidencia: 'Prometedora (1 grupo, con conflicto de interés): Woods et al., 2024.'
  },
  gamma: {
    id: 'gamma', nombre: 'Repaso activo', icono: '⚡', hz: 40, banda: 'Gamma', depth: 0.30,
    gains: { lecho: 0.9, aire: 0.50, pad: 0.35 }, padCut: 2800, segAcorde: 56,
    acordes: [['C3','G3','D4','E4'], ['F3','C4','E4','G4'], ['A2','E3','B3','D4'], ['G2','D3','F#3','A3']],
    color: '#facc15', estrellas: 1,
    resumen: 'Modulación sutil a 40 Hz con timbre más brillante y ligero.',
    uso: 'Repaso rápido de tarjetas y test, en bloques cortos (≤ 25 min). Úsalo como textura estimulante, no como promesa.',
    evidencia: 'Preliminar: robusta como respuesta cerebral (ASSR), sin prueba de mejora de memoria en estudiantes sanos.'
  },
  alfa: {
    id: 'alfa', nombre: 'Lectura y redacción', icono: '📖', hz: 10, banda: 'Alfa', depth: 0.35,
    gains: { lecho: 1.0, aire: 0.35, pad: 0.50 }, padCut: 1700, segAcorde: 72,
    acordes: [['A2','E3','C4','G4'], ['F2','C3','A3','E4'], ['C3','G3','D4','E4'], ['D3','A3','C4','F4']],
    color: '#34d399', estrellas: 1,
    resumen: 'Pulso lento y envolvente a 10 Hz, grave y cálido, sin brillo molesto.',
    uso: 'Lectura de manuales, subrayado, redacción tranquila, repaso pasivo.',
    evidencia: 'Débil: el alfa se asocia a calma atenta, pero el arrastre auditivo no está demostrado.'
  },
  theta: {
    id: 'theta', nombre: 'Descanso activo', icono: '🌙', hz: 6, banda: 'Theta', depth: 0.50,
    gains: { lecho: 1.0, aire: 0.25, pad: 0.45 }, padCut: 1400, segAcorde: 80,
    acordes: [['F2','C3','A3','E4'], ['Bb2','F3','D4','A4'], ['C3','G3','E4','D5']],
    color: '#a78bfa', estrellas: 1,
    resumen: 'Oleaje lento a 6 Hz, muy grave y envolvente. Pensado para las pausas.',
    uso: 'Pausas del Pomodoro, desconexión visual, respirar. Lo que descansa es la pausa; el sonido solo acompaña.',
    evidencia: 'Muy débil como herramienta de descanso; se usa por contraste y comodidad.'
  },
  ruido: {
    id: 'ruido', nombre: 'Enmascaramiento puro', icono: '🌧️', hz: 0, banda: 'Sin modulación', depth: 0,
    gains: { lecho: 1.0, aire: 0.80, pad: 0.0 }, padCut: 1500, segAcorde: 64,
    acordes: [['D3','A3','E4','F#4']],
    color: '#94a3b8', estrellas: 3,
    resumen: 'Ruido marrón (grave) + rosa (aire), constante. Sin pulso.',
    uso: 'Días de fatiga sensorial, oficinas, vecinos, habla de fondo. Solo tapa ruidos: no estimula.',
    evidencia: 'Buena para enmascarar habla y sonidos intermitentes; a volumen alto empeora.'
  }
};
