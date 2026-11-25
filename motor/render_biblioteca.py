# -*- coding: utf-8 -*-
"""
Renderiza la biblioteca completa de NeuroFoco Studio a MP3 (y muestras WAV).

Uso:
  python render_biblioteca.py                  # todo (unos 590 min de audio, ~25-40 min en 4 nucleos)
  python render_biblioteca.py --solo pomo25_beta sesion60_alfa
  python render_biblioteca.py --factor 0.05 --salida ..\\audio_prueba   # prueba rapida
Genera: audio/*.mp3, audio/muestras_wav/*.wav, audio/manifiesto.json y app/biblioteca.js
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neurofoco_dsp as dsp  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HZ = {"beta": 16, "gamma": 40, "alfa": 10, "theta": 6, "ruido": 0}
NOM = {"beta": "Foco profundo", "gamma": "Repaso activo", "alfa": "Lectura y redaccion",
       "theta": "Descanso activo", "ruido": "Enmascaramiento puro"}
USO = {
    "beta": "Estudio tecnico, problemas, supuestos practicos, redaccion exigente.",
    "gamma": "Repaso rapido de tarjetas y test. Bloques cortos; evidencia preliminar.",
    "alfa": "Lectura de manuales, subrayado, redaccion tranquila.",
    "theta": "Pausas del Pomodoro y desconexion suave.",
    "ruido": "Dias de fatiga sensorial o entornos ruidosos: solo enmascara, sin modulacion.",
}


def _catalogo():
    c = []
    for m in ("beta", "alfa", "ruido"):
        c.append(dict(id=f"sesion60_{m}", tipo="continua", modo=m, min=60,
                      titulo=f"Sesion continua 60 min - {NOM[m]}",
                      estructura="60 min sin pausas"))
    c.append(dict(id="sesion30_gamma", tipo="continua", modo="gamma", min=30,
                  titulo=f"Sesion continua 30 min - {NOM['gamma']}",
                  estructura="30 min sin pausas (gamma cansa: mejor en bloques cortos)"))
    for m in ("beta", "gamma", "alfa", "ruido"):
        c.append(dict(id=f"pomo50_{m}", tipo="pomodoro", modo=m, trabajo=50, descanso=10, ciclos=1,
                      titulo=f"Pomodoro 50/10 - {NOM[m]}",
                      estructura="50 min de trabajo + 10 min de descanso (theta)"))
    for m in ("beta", "gamma", "alfa", "ruido"):
        c.append(dict(id=f"pomo25_{m}", tipo="pomodoro", modo=m, trabajo=25, descanso=5, ciclos=1,
                      titulo=f"Pomodoro 25/5 - {NOM[m]}",
                      estructura="25 min de trabajo + 5 min de descanso (theta). Repite el archivo para mas ciclos"))
    c.append(dict(id="pausa20_theta", tipo="pausa", modo="theta", min=20,
                  titulo="Pausa larga 20 min - Descanso activo",
                  estructura="20 min de descanso suave"))
    c.append(dict(id="demo_campanas", tipo="demo", modo="beta", trabajo=0.4, descanso=0.3, ciclos=1,
                  titulo="Demo de transiciones y campanas (42 s)",
                  estructura="24 s de foco beta + 18 s de descanso theta, con las dos campanas"))
    return c


def _plan(it, factor):
    seed = zlib.crc32(it["id"].encode()) % 100000
    if it["tipo"] in ("continua", "pausa"):
        return dsp.plan_continuo(it["modo"], it["min"] * factor, seed)
    return dsp.plan_pomodoro(it["modo"], it["trabajo"] * factor, it["descanso"] * factor,
                             it.get("ciclos", 1), seed)


def _trabajo(args):
    it, salida, kbps, factor = args
    t0 = time.time()
    ruta = os.path.join(salida, it["id"] + ".mp3")
    s = dsp.SumideroMP3(ruta, kbps)
    dsp.renderizar(_plan(it, factor), s, fundido_cruce=3.0, fade_in=4.0, fade_out=5.0)
    rec = dict(it)
    rec.update(archivo=os.path.basename(ruta), kbps=kbps, bytes=os.path.getsize(ruta),
               segundos=round(s.segundos, 2), sha256=dsp.sha256_archivo(ruta),
               pico_dbfs=round(s.pico_dbfs, 2), rms_dbfs=round(s.rms_dbfs, 2),
               recortes=s.recortes, hz=HZ[it["modo"]], uso=USO[it["modo"]],
               nombre_modo=NOM[it["modo"]])
    return rec, time.time() - t0


def _muestra(args):
    modo, salida, factor = args
    ruta = os.path.join(salida, "muestras_wav", f"muestra_{modo}.wav")
    s = dsp.SumideroWAV(ruta)
    dsp.renderizar(dsp.plan_continuo(modo, 1.5 * max(factor, 0.2)), s, fade_in=3, fade_out=3)
    return dict(archivo=f"muestras_wav/muestra_{modo}.wav", modo=modo, segundos=round(s.segundos, 1),
                pico_dbfs=round(s.pico_dbfs, 2), rms_dbfs=round(s.rms_dbfs, 2),
                bytes=os.path.getsize(ruta), sha256=dsp.sha256_archivo(ruta))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", nargs="*")
    ap.add_argument("--salida", default=os.path.join(RAIZ, "audio"))
    ap.add_argument("--kbps", type=int, default=128)
    ap.add_argument("--factor", type=float, default=1.0, help="escala de duraciones (pruebas)")
    ap.add_argument("--workers", type=int, default=max(1, min(4, (os.cpu_count() or 2))))
    ap.add_argument("--sin-wav", action="store_true")
    a = ap.parse_args()

    os.makedirs(os.path.join(a.salida, "muestras_wav"), exist_ok=True)
    cat = [c for c in _catalogo() if not a.solo or c["id"] in a.solo]
    cat_total = {c["id"]: i for i, c in enumerate(_catalogo())}
    cat.sort(key=lambda c: -(c.get("min") or (c.get("trabajo", 0) + c.get("descanso", 0))))
    print(f"[NeuroFoco] {len(cat)} pistas, {a.workers} procesos, {a.kbps} kbps -> {a.salida}", flush=True)
    for m in dsp.MODOS:
        dsp.calibrar(m)

    resultados = []
    t0 = time.time()
    trabajos = [(c, a.salida, a.kbps, a.factor) for c in cat]
    with mp.Pool(a.workers) as pool:
        for rec, seg in pool.imap_unordered(_trabajo, trabajos):
            resultados.append(rec)
            print(f"  OK {rec['archivo']:<28} {rec['segundos']/60:5.1f} min  "
                  f"{rec['bytes']/1e6:6.1f} MB  pico {rec['pico_dbfs']:6.2f}  rms {rec['rms_dbfs']:6.2f}  ({seg:4.0f} s)",
                  flush=True)
        muestras = []
        if not a.sin_wav and not a.solo:
            for r in pool.imap_unordered(_muestra, [(m, a.salida, a.factor) for m in dsp.MODOS]):
                muestras.append(r)
                print(f"  OK {r['archivo']}", flush=True)

    resultados.sort(key=lambda r: cat_total[r["id"]])
    if a.solo:  # fusionar con el manifiesto previo
        previo = os.path.join(a.salida, "manifiesto.json")
        if os.path.exists(previo):
            ant = json.load(open(previo, encoding="utf-8"))
            ids = {r["id"] for r in resultados}
            resultados = sorted([r for r in ant.get("pistas", []) if r["id"] not in ids] + resultados,
                                key=lambda r: cat_total.get(r["id"], 99))
            muestras = ant.get("muestras", [])
    man = dict(generado=time.strftime("%Y-%m-%d %H:%M:%S"), fs=dsp.FS, kbps=a.kbps,
               pistas=resultados, muestras=muestras)
    with open(os.path.join(a.salida, "manifiesto.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
    if os.path.abspath(a.salida) == os.path.join(RAIZ, "audio"):
        with open(os.path.join(RAIZ, "app", "biblioteca.js"), "w", encoding="utf-8") as f:
            f.write("// Generado por motor/render_biblioteca.py - no editar a mano\n")
            f.write("window.NF_BIBLIOTECA = " + json.dumps(resultados, ensure_ascii=False, indent=1) + ";\n")
            f.write("window.NF_MUESTRAS = " + json.dumps(muestras, ensure_ascii=False, indent=1) + ";\n")
    print(f"[NeuroFoco] Terminado en {(time.time()-t0)/60:.1f} min. Total {sum(r['segundos'] for r in resultados)/60:.0f} min de audio.")


if __name__ == "__main__":
    mp.freeze_support()
    main()
