# -*- coding: utf-8 -*-
"""
Verificacion objetiva del audio de NeuroFoco Studio.

  python verificar.py            # sintesis + MP3 de audio/ (si existen)
  python verificar.py --rapido   # solo sintesis en memoria

Comprueba: frecuencia de modulacion (FFT de la envolvente), pendiente espectral
(rosa -3 dB/oct, marron -6 dB/oct), nivel RMS/pico, ausencia de recortes, duracion exacta,
continuidad del fundido cruzado, caida de las campanas y descodificacion real de los MP3.
Escribe docs/informe_verificacion.md. Codigo de salida != 0 si algo falla.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neurofoco_dsp as dsp  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FS = dsp.FS
RES = []


def check(nombre, ok, detalle=""):
    RES.append((nombre, bool(ok), detalle))
    print(("  PASS " if ok else "  FAIL ") + nombre + (f" -> {detalle}" if detalle else ""), flush=True)


def analisis_am(x_mono: np.ndarray):
    sos = signal.butter(4, [300, 4000], "band", fs=FS, output="sos")
    y = signal.sosfilt(sos, x_mono)
    env = np.abs(signal.hilbert(y))
    env = env - env.mean()
    esp = np.abs(np.fft.rfft(env * np.hanning(env.size)))
    fr = np.fft.rfftfreq(env.size, 1 / FS)
    m = (fr >= 2) & (fr <= 80)
    i = np.argmax(esp[m])
    return fr[m][i], esp[m][i] / np.median(esp[m])


def pendiente_db_oct(x, f1, f2):
    f, p = signal.welch(x, FS, nperseg=16384)
    m = (f >= f1) & (f <= f2)
    pend = np.polyfit(np.log2(f[m]), 10 * np.log10(p[m]), 1)[0]
    return pend


def fase_sintesis():
    print("== Sintesis por modo ==")
    for modo, m in dsp.MODOS.items():
        esc = dsp.Escena(modo, seed=2026)
        x = np.concatenate([esc.bloque(FS * 10) for _ in range(7)], axis=1)[:, FS * 2:]   # 60 s
        rms = 20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)))
        pico = 20 * np.log10(np.max(np.abs(x)))
        check(f"[{modo}] nivel RMS entre -23 y -19 dBFS", -23 <= rms <= -19, f"{rms:.2f} dBFS")
        check(f"[{modo}] pico < -3 dBFS (sin recortes)", pico < -3, f"{pico:.2f} dBFS")
        hz, prom = analisis_am(x[0].astype(np.float64))
        if m.hz > 0:
            check(f"[{modo}] modulacion AM en {m.hz:g} Hz", abs(hz - m.hz) < 0.25 and prom > 8,
                  f"pico {hz:.2f} Hz, prominencia x{prom:.0f}")
        else:
            check(f"[{modo}] sin modulacion dominante", prom < 6, f"prominencia x{prom:.1f}")
        check(f"[{modo}] estereo decorrelado (L/R no identicos)",
              abs(np.corrcoef(x[0], x[1])[0, 1]) < 0.9, f"corr {np.corrcoef(x[0], x[1])[0,1]:.2f}")
    esc = dsp.Escena("ruido", seed=5)
    aire = np.concatenate([esc._aire(FS * 10) for _ in range(4)], axis=1)[0]
    lecho = np.concatenate([esc._lecho(FS * 10) for _ in range(4)], axis=1)[0]
    pa, pb = pendiente_db_oct(aire, 400, 3000), pendiente_db_oct(lecho, 40, 400)
    check("ruido rosa: pendiente ~ -3 dB/oct (400-3000 Hz)", -4.2 <= pa <= -2.0, f"{pa:.2f} dB/oct")
    check("ruido marron: pendiente ~ -6 dB/oct (40-400 Hz)", -7.5 <= pb <= -4.5, f"{pb:.2f} dB/oct")


def fase_campanas():
    print("== Campanas ==")
    for tipo in ("trabajo", "descanso", "inicio"):
        c = dsp.campana(tipo)
        pico = float(np.max(np.abs(c)))
        e_ini = float(np.sum(c[:, : FS * 2] ** 2))
        e_fin = float(np.sum(c[:, -FS * 2:] ** 2))
        check(f"campana '{tipo}' pico <= 0.26 (suave)", pico <= 0.26, f"{pico:.3f}")
        check(f"campana '{tipo}' se extingue (energia final < 1% de la inicial)", e_fin < 0.01 * e_ini,
              f"{e_fin / e_ini * 100:.4f} %")


def fase_cruce():
    print("== Sesion Pomodoro corta (duracion y continuidad) ==")
    plan = [dsp.Segmento("beta", 24, "trabajo"), dsp.Segmento("theta", 12, "descanso"),
            dsp.Segmento("alfa", 18, "trabajo")]
    s = dsp.SumideroMemoria()
    dsp.renderizar(plan, s, fundido_cruce=3.0, fade_in=2.0, fade_out=2.0)
    x = s.audio()
    check("duracion exacta = suma de segmentos (54 s)", x.shape[1] == 54 * FS, f"{x.shape[1] / FS:.3f} s")
    check("pico < -1 dBFS y sin recortes", s.pico_dbfs < -1 and s.recortes == 0,
          f"{s.pico_dbfs:.2f} dBFS, {s.recortes} recortes")
    d = np.abs(np.diff(x[0].astype(np.float64)))
    glob = np.median([d[i:i + FS].max() for i in range(0, d.size - FS, FS)])
    for nombre, t in (("24 s", 24.0), ("36 s", 36.0)):
        i = int(t * FS)
        loc = d[i - FS // 2: i + FS // 2].max()
        check(f"sin clics en la transicion de {nombre}", loc < 2.0 * glob, f"max|dx| local/mediana = {loc / glob:.2f}")
    sil = x[0][: FS // 2]
    check("arranque con fundido (sin golpe inicial)", np.max(np.abs(sil)) < 0.1 * np.max(np.abs(x)), "")


def fase_mp3():
    man = os.path.join(RAIZ, "audio", "manifiesto.json")
    if not os.path.exists(man):
        print("== MP3: no hay manifiesto (omitido) ==")
        return
    import miniaudio
    d = json.load(open(man, encoding="utf-8"))
    print(f"== Descodificacion de {len(d['pistas'])} MP3 ==")
    for p in d["pistas"]:
        ruta = os.path.join(RAIZ, "audio", p["archivo"])
        if not os.path.exists(ruta):
            check(f"{p['archivo']} existe", False)
            continue
        info = miniaudio.mp3_get_file_info(ruta)
        esperado = p["segundos"]
        check(f"{p['archivo']}: {info.duration:.1f} s ~ {esperado:.1f} s, {info.sample_rate} Hz",
              abs(info.duration - esperado) < 0.5 and info.sample_rate == FS, "")
        check(f"{p['archivo']}: nivel RMS/pico del manifiesto", -23 <= p["rms_dbfs"] <= -19 and p["pico_dbfs"] < -1
              and p["recortes"] == 0, f"rms {p['rms_dbfs']} pico {p['pico_dbfs']}")
        # Descodificar 60 s (a partir de los 20 s) y medir la AM tras compresion MP3
        gen = miniaudio.stream_file(ruta, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=2,
                                    sample_rate=FS, frames_to_read=FS)
        bufs, n = [], 0
        for blk in gen:
            n += len(blk) // 2
            if FS * 20 <= n <= FS * 80:
                bufs.append(np.frombuffer(blk, dtype=np.int16).reshape(-1, 2)[:, 0].astype(np.float64) / 32768)
            if n > FS * 80:
                break
        modo = p["modo"]
        m = dsp.MODOS[modo]
        x = np.concatenate(bufs)
        if p["tipo"] == "pomodoro":
            pass
        hz, prom = analisis_am(x)
        if m.hz > 0 and p["tipo"] in ("continua", "pomodoro", "pausa"):
            check(f"{p['archivo']}: AM {m.hz:g} Hz sobrevive al MP3", abs(hz - m.hz) < 0.3 and prom > 8,
                  f"{hz:.2f} Hz x{prom:.0f}")
        elif m.hz == 0:
            check(f"{p['archivo']}: sin modulacion dominante", prom < 6, f"x{prom:.1f}")


def fase_wav():
    man = os.path.join(RAIZ, "audio", "manifiesto.json")
    if not os.path.exists(man):
        return
    import wave
    d = json.load(open(man, encoding="utf-8"))
    muestras = d.get("muestras", [])
    if not muestras:
        print("== WAV: sin muestras en manifiesto ==")
        return
    print(f"== Verificacion de {len(muestras)} muestras WAV ==")
    for m in muestras:
        ruta = os.path.join(RAIZ, "audio", m["archivo"])
        if not os.path.exists(ruta):
            check(f"{m['archivo']} existe", False)
            continue
        with wave.open(ruta, "rb") as w:
            dur = w.getnframes() / w.getframerate()
            ok_fmt = (w.getnchannels() == 2 and w.getsampwidth() == 2 and w.getframerate() == FS)
        sha_ok = dsp.sha256_archivo(ruta) == m["sha256"]
        check(f"{m['archivo']}: {dur:.1f} s, 44.1 kHz 16-bit estero, SHA-256",
              ok_fmt and abs(dur - m["segundos"]) < 0.5 and sha_ok,
              f"rms {m['rms_dbfs']} pico {m['pico_dbfs']}")


def escribir_informe(t):
    ok = sum(1 for r in RES if r[1])
    ruta = os.path.join(RAIZ, "docs", "informe_verificacion.md")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("# Informe de verificacion automatica - NeuroFoco Studio\n\n")
        f.write(f"- Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n- Resultado: **{ok}/{len(RES)} comprobaciones superadas**"
                f" ({t:.0f} s)\n- Script: `motor/verificar.py`\n\n| Resultado | Comprobacion | Detalle |\n| :---: | :--- | :--- |\n")
        for n, o, d in RES:
            f.write(f"| {'PASS' if o else '**FAIL**'} | {n} | {d} |\n")
    print(f"\n{ok}/{len(RES)} comprobaciones superadas. Informe: {ruta}")
    return ok == len(RES)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    fase_sintesis()
    fase_campanas()
    fase_cruce()
    if not a.rapido:
        fase_mp3()
        fase_wav()
    sys.exit(0 if escribir_informe(time.time() - t0) else 1)
