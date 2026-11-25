# -*- coding: utf-8 -*-
"""
Genera una pista a medida (MP3 o WAV).

Ejemplos:
  python generar_pista.py --modo beta --minutos 90 --salida mi_foco.mp3
  python generar_pista.py --modo alfa --pomodoro 40 8 --ciclos 3 --salida lectura_40-8.mp3
  python generar_pista.py --modo ruido --minutos 120 --wav --salida ruido.wav
Modos: beta, gamma, alfa, theta, ruido
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neurofoco_dsp as dsp  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", required=True, choices=list(dsp.MODOS))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--minutos", type=float, help="sesion continua")
    g.add_argument("--pomodoro", nargs=2, type=float, metavar=("TRABAJO", "DESCANSO"))
    ap.add_argument("--ciclos", type=int, default=1)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--wav", action="store_true")
    ap.add_argument("--kbps", type=int, default=128)
    ap.add_argument("--semilla", type=int, default=1)
    a = ap.parse_args()

    plan = (dsp.plan_continuo(a.modo, a.minutos, a.semilla) if a.minutos
            else dsp.plan_pomodoro(a.modo, a.pomodoro[0], a.pomodoro[1], a.ciclos, a.semilla))
    s = dsp.SumideroWAV(a.salida) if a.wav or a.salida.lower().endswith(".wav") else dsp.SumideroMP3(a.salida, a.kbps)

    def prog(p):
        sys.stdout.write(f"\r  {p*100:5.1f} %")
        sys.stdout.flush()

    dsp.renderizar(plan, s, progreso=prog)
    print(f"\nListo: {a.salida}  ({s.segundos/60:.1f} min, pico {s.pico_dbfs:.1f} dBFS, RMS {s.rms_dbfs:.1f} dBFS)")


if __name__ == "__main__":
    main()
