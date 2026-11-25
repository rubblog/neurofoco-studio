# -*- coding: utf-8 -*-
"""
NeuroFoco Studio - Motor DSP offline.

Sintetiza paisajes sonoros de estudio sin ninguna muestra externa:
  * Lecho de ruido marron (grave, calido) + capa de ruido rosa filtrada ("aire").
  * Pad armonico ambiental que evoluciona despacio (acordes con fundido continuo).
  * Modulacion de amplitud (AM) de coseno elevado a la frecuencia del modo
    (beta 16 Hz, gamma 40 Hz, alfa 10 Hz, theta 6 Hz) o sin modulacion.
  * Campanas tipo cuenco tibetano para las transiciones de Pomodoro.

Todo se genera por bloques (streaming), de modo que una sesion de 60 min
no necesita mas de unas decenas de MB de RAM.
Autor del proyecto: Ruben Garcia Fuentes. Sin dependencias de red.
"""
from __future__ import annotations

import functools
import hashlib
import math
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

import numpy as np
from scipy import signal

FS = 44100                 # Hz
CHUNK = FS * 10            # 10 s por bloque
OBJETIVO_RMS_DBFS = -21.0  # nivel medio de programa (comodo, sin saturar)

# ---------------------------------------------------------------------------
# Notas
# ---------------------------------------------------------------------------
_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def nota_hz(nombre: str) -> float:
    letra, resto, alt = nombre[0], nombre[1:], 0
    if resto.startswith("#"):
        alt, resto = 1, resto[1:]
    elif resto.startswith("b"):
        alt, resto = -1, resto[1:]
    midi = 12 * (int(resto) + 1) + _BASE[letra] + alt
    return 440.0 * 2 ** ((midi - 69) / 12)


# ---------------------------------------------------------------------------
# Definicion de modos (espejo de app/modos.js)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Modo:
    id: str
    nombre: str
    hz: float            # 0 = sin modulacion
    profundidad: float   # profundidad AM (0..1) en pad y aire
    g_lecho: float
    g_aire: float
    g_pad: float
    corte_pad: float
    acordes: tuple
    seg_acorde: float = 64.0


MODOS = {
    "beta": Modo("beta", "Foco profundo (beta 16 Hz)", 16.0, 0.42, 1.0, 0.50, 0.42, 2200,
                 (("D3", "A3", "E4", "F#4"), ("B2", "F#3", "D4", "E4"),
                  ("G2", "D3", "A3", "B3"), ("A2", "E3", "B3", "C#4"))),
    "gamma": Modo("gamma", "Repaso activo (gamma 40 Hz)", 40.0, 0.30, 0.9, 0.50, 0.35, 2800,
                  (("C3", "G3", "D4", "E4"), ("F3", "C4", "E4", "G4"),
                   ("A2", "E3", "B3", "D4"), ("G2", "D3", "F#3", "A3")), 56.0),
    "alfa": Modo("alfa", "Lectura y redaccion (alfa 10 Hz)", 10.0, 0.35, 1.0, 0.35, 0.50, 1700,
                 (("A2", "E3", "C4", "G4"), ("F2", "C3", "A3", "E4"),
                  ("C3", "G3", "D4", "E4"), ("D3", "A3", "C4", "F4")), 72.0),
    "theta": Modo("theta", "Descanso activo (theta 6 Hz)", 6.0, 0.50, 1.0, 0.25, 0.45, 1400,
                  (("F2", "C3", "A3", "E4"), ("Bb2", "F3", "D4", "A4"),
                   ("C3", "G3", "E4", "D5")), 80.0),
    "ruido": Modo("ruido", "Enmascaramiento puro (sin modulacion)", 0.0, 0.0, 1.0, 0.80, 0.0, 1500,
                  (("D3", "A3", "E4", "F#4"),), 64.0),
}

# ---------------------------------------------------------------------------
# Escena: generador continuo de un modo
# ---------------------------------------------------------------------------
_PINK_B = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
_PINK_A = [1.0, -2.494956002, 2.017265875, -0.522189400]
_BROWN_A = [1.0, -0.998]
_TREMOLO_HZ = (0.037, 0.052, 0.061, 0.043)
_PADRAW = 0.94   # compensa la RMS teorica de 4 voces incoherentes


def _env_am(t: np.ndarray, hz: float, prof: float) -> np.ndarray:
    """Coseno elevado en [1-prof, 1], normalizado a media 1 (nivel constante)."""
    if hz <= 0 or prof <= 0:
        return np.ones_like(t)
    env = 1.0 - prof * 0.5 * (1.0 - np.cos(2.0 * np.pi * hz * t))
    return env / (1.0 - prof * 0.5)


class Escena:
    """Genera un modo de forma continua, bloque a bloque (estado de filtros persistente)."""

    def __init__(self, modo: str, seed: int = 1, ganancia: Optional[float] = None):
        self.m = MODOS[modo]
        self.rng = np.random.default_rng(seed)
        self.pos = 0
        self.sos_lecho = signal.butter(2, 900, "low", fs=FS, output="sos")
        self.sos_aire = signal.butter(2, [180, 5200], "band", fs=FS, output="sos")
        self.sos_pad = signal.butter(2, self.m.corte_pad, "low", fs=FS, output="sos")
        self.zi_brown = np.zeros((2, 1))
        self.zi_pink = np.zeros((2, 3))
        self.zi_lecho = np.zeros((self.sos_lecho.shape[0], 2, 2))
        self.zi_aire = np.zeros((self.sos_aire.shape[0], 2, 2))
        self.zi_pad = np.zeros((self.sos_pad.shape[0], 2, 2))
        sc = _escalas_capas()
        self.esc_lecho, self.esc_aire = sc["lecho"], sc["aire"]
        self.fases_vox = self.rng.uniform(0, 2 * np.pi, size=(4, 3))
        self.ganancia = ganancia if ganancia is not None else calibrar(modo)

    # -- capas -------------------------------------------------------------
    def _lecho(self, n: int) -> np.ndarray:
        w = self.rng.standard_normal((2, n))
        y, self.zi_brown = signal.lfilter([1.0], _BROWN_A, w, axis=-1, zi=self.zi_brown)
        y, self.zi_lecho = signal.sosfilt(self.sos_lecho, y, axis=-1, zi=self.zi_lecho)
        return y * self.esc_lecho

    def _aire(self, n: int) -> np.ndarray:
        w = self.rng.standard_normal((2, n))
        y, self.zi_pink = signal.lfilter(_PINK_B, _PINK_A, w, axis=-1, zi=self.zi_pink)
        y, self.zi_aire = signal.sosfilt(self.sos_aire, y, axis=-1, zi=self.zi_aire)
        return y * self.esc_aire

    def _pad(self, t: np.ndarray) -> np.ndarray:
        m = self.m
        if m.g_pad <= 0:
            return np.zeros((2, t.size))
        L = m.seg_acorde
        out = np.zeros((2, t.size))
        c0 = int(math.floor(t[0] / L))
        c1 = int(math.floor(t[-1] / L)) + 1
        for c in range(c0, c1 + 1):
            ini = (c - 1) * L
            w = np.sin(np.pi * np.clip((t - ini) / (2 * L), 0.0, 1.0)) ** 2
            if not np.any(w > 1e-6):
                continue
            notas = m.acordes[c % len(m.acordes)]
            capa = np.zeros((2, t.size))
            for k, nom in enumerate(notas):
                f = nota_hz(nom)
                ph = self.fases_vox[k]
                s1 = np.sin(2 * np.pi * f * 0.99826 * t + ph[0])      # -3 cent
                s2 = np.sin(2 * np.pi * f * 1.00173 * t + ph[1])      # +3 cent
                s3 = 0.25 * np.sin(2 * np.pi * 2 * f * t + ph[2])
                trem = 1.0 + 0.15 * np.sin(2 * np.pi * _TREMOLO_HZ[k] * t + ph[0])
                pan = (-0.6, -0.2, 0.2, 0.6)[k]
                gl, gr = math.sqrt((1 - pan) / 2), math.sqrt((1 + pan) / 2)
                a = 0.5 * s1 + 0.5 * s3
                b = 0.5 * s2 + 0.5 * s3
                capa[0] += gl * (0.65 * a + 0.35 * b) * trem
                capa[1] += gr * (0.35 * a + 0.65 * b) * trem
            out += capa * w
        y, self.zi_pad = signal.sosfilt(self.sos_pad, out * _PADRAW, axis=-1, zi=self.zi_pad)
        return y

    # -- bloque ------------------------------------------------------------
    def bloque(self, n: int) -> np.ndarray:
        t = (self.pos + np.arange(n, dtype=np.float64)) / FS
        m = self.m
        lecho = self._lecho(n) * _env_am(t, m.hz, m.profundidad * 0.4)
        aire = self._aire(n)
        pad = self._pad(t)
        env = _env_am(t, m.hz, m.profundidad)
        y = lecho * m.g_lecho + (aire * m.g_aire + pad * m.g_pad) * env
        self.pos += n
        return (y * self.ganancia).astype(np.float32)


@functools.lru_cache(maxsize=1)
def _escalas_capas() -> dict:
    """Escala de cada ruido filtrado a RMS unidad (medida tras descartar transitorio)."""
    rng = np.random.default_rng(777)
    n = FS * 8
    w = rng.standard_normal(n)
    brown = signal.lfilter([1.0], _BROWN_A, w)
    brown = signal.sosfilt(signal.butter(2, 900, "low", fs=FS, output="sos"), brown)
    pink = signal.lfilter(_PINK_B, _PINK_A, rng.standard_normal(n))
    pink = signal.sosfilt(signal.butter(2, [180, 5200], "band", fs=FS, output="sos"), pink)
    ini = FS * 2
    return {"lecho": 1.0 / np.sqrt(np.mean(brown[ini:] ** 2)),
            "aire": 1.0 / np.sqrt(np.mean(pink[ini:] ** 2))}


@functools.lru_cache(maxsize=None)
def calibrar(modo: str) -> float:
    """Ganancia que lleva el modo a OBJETIVO_RMS_DBFS (y garantiza pico <= -3 dBFS)."""
    esc = Escena(modo, seed=4242, ganancia=1.0)
    x = np.concatenate([esc.bloque(FS * 10) for _ in range(4)], axis=1)[:, FS * 2:]
    rms = float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))
    g = 10 ** (OBJETIVO_RMS_DBFS / 20) / rms
    pico = float(np.max(np.abs(x))) * g
    if pico > 0.70:
        g *= 0.70 / pico
    return g


# ---------------------------------------------------------------------------
# Campanas (cuenco tibetano sintetico)
# ---------------------------------------------------------------------------
_PARCIALES = (1.0, 2.76, 5.40, 8.93)
_AMPS = (1.0, 0.45, 0.20, 0.08)
_TAUS = (3.2, 2.0, 1.1, 0.6)


def campana(tipo: str, pico: float = 0.25) -> np.ndarray:
    """Devuelve (2, n) float32. tipo: 'trabajo' (dos golpes ascendentes),
    'descanso' (un golpe grave y largo), 'inicio' (un golpe suave)."""
    if tipo == "trabajo":
        golpes = [(0.0, 392.00, 1.0), (1.15, 587.33, 0.85)]
        dur = 10.0
    elif tipo == "descanso":
        golpes = [(0.0, 261.63, 1.0), (0.02, 130.81, 0.45)]
        dur = 12.0
    else:
        golpes = [(0.0, 392.00, 1.0)]
        dur = 9.0
    n = int(dur * FS)
    t = np.arange(n) / FS
    out = np.zeros((2, n))
    for ini, f0, amp in golpes:
        i0 = int(ini * FS)
        tt = t[: n - i0]
        att = np.clip(tt / 0.03, 0, 1)
        att = 0.5 - 0.5 * np.cos(np.pi * att)
        for p, a, tau in zip(_PARCIALES, _AMPS, _TAUS):
            f = f0 * p
            if f > 9000:
                continue
            dec = np.exp(-tt / tau)
            for lado, det in ((0, 0.6), (1, -0.6)):
                s = np.sin(2 * np.pi * (f + det) * tt) * a * dec * att * amp
                out[lado, i0:] += 0.65 * s
                out[1 - lado, i0:] += 0.35 * s
    out *= pico / np.max(np.abs(out))
    return out.astype(np.float32)


# ---------------------------------------------------------------------------
# Segmentos y sesiones
# ---------------------------------------------------------------------------
@dataclass
class Segmento:
    modo: str
    segundos: float
    campana: Optional[str] = None     # tipo de campana al inicio del segmento
    etiqueta: str = ""
    seed: int = 1


def _flujo_segmento(seg: Segmento, n_total: int, t_campana: float) -> Iterator[np.ndarray]:
    esc = Escena(seg.modo, seed=seg.seed)
    cam = campana(seg.campana) if seg.campana else None
    c0 = int(t_campana * FS)
    emitido = 0
    while emitido < n_total:
        n = min(CHUNK, n_total - emitido)
        b = esc.bloque(n)
        if cam is not None and emitido < c0 + cam.shape[1] and emitido + n > c0:
            a = max(c0, emitido)
            z = min(c0 + cam.shape[1], emitido + n)
            b[:, a - emitido:z - emitido] += cam[:, a - c0:z - c0]
        yield b
        emitido += n


class Sumidero:
    """Base: acumula estadisticas (pico, RMS, recortes) y delega en write_pcm."""

    def __init__(self):
        self.n = 0
        self.suma_cuad = 0.0
        self.pico = 0.0
        self.recortes = 0
        self._rng = np.random.default_rng(99)

    def escribir(self, x: np.ndarray) -> None:
        x64 = x.astype(np.float64)
        self.suma_cuad += float(np.sum(x64 * x64))
        self.pico = max(self.pico, float(np.max(np.abs(x64))))
        self.recortes += int(np.sum(np.abs(x64) >= 0.999))
        self.n += x.shape[1]
        d = (self._rng.random(x.shape) - self._rng.random(x.shape))
        pcm = np.clip(x64 * 32767.0 + d, -32768, 32767).astype(np.int16)
        self.write_pcm(np.ascontiguousarray(pcm.T))

    def write_pcm(self, pcm: np.ndarray) -> None:  # pcm (n,2) int16
        raise NotImplementedError

    def cerrar(self) -> None:
        pass

    @property
    def segundos(self) -> float:
        return self.n / FS

    @property
    def rms_dbfs(self) -> float:
        rms = math.sqrt(self.suma_cuad / max(1, self.n * 2))
        return 20 * math.log10(max(rms, 1e-12))

    @property
    def pico_dbfs(self) -> float:
        return 20 * math.log10(max(self.pico, 1e-12))


class SumideroMP3(Sumidero):
    def __init__(self, ruta: str, kbps: int = 128):
        super().__init__()
        import lameenc
        self.f = open(ruta, "wb")
        self.enc = lameenc.Encoder()
        self.enc.set_bit_rate(kbps)
        self.enc.set_in_sample_rate(FS)
        self.enc.set_channels(2)
        self.enc.set_quality(2)

    def write_pcm(self, pcm):
        self.f.write(self.enc.encode(pcm.tobytes()))

    def cerrar(self):
        self.f.write(self.enc.flush())
        self.f.close()


class SumideroWAV(Sumidero):
    def __init__(self, ruta: str):
        super().__init__()
        import wave
        self.w = wave.open(ruta, "wb")
        self.w.setnchannels(2)
        self.w.setsampwidth(2)
        self.w.setframerate(FS)

    def write_pcm(self, pcm):
        self.w.writeframes(pcm.tobytes())

    def cerrar(self):
        self.w.close()


class SumideroMemoria(Sumidero):
    def __init__(self):
        super().__init__()
        self.partes: List[np.ndarray] = []

    def escribir(self, x):
        super().escribir(x)
        self.partes.append(x.copy())

    def write_pcm(self, pcm):
        pass

    def audio(self) -> np.ndarray:
        return np.concatenate(self.partes, axis=1)


def renderizar(segmentos: List[Segmento], sumidero: Sumidero, fundido_cruce: float = 3.0,
               fade_in: float = 4.0, fade_out: float = 5.0, progreso=None) -> None:
    """Concatena segmentos con fundido cruzado de potencia constante.

    La duracion total es exactamente la suma de las duraciones nominales.
    """
    X = int(fundido_cruce * FS)
    n_seg = len(segmentos)
    total = int(sum(s.segundos for s in segmentos) * FS)
    fi, fo = int(fade_in * FS), int(fade_out * FS)
    u = np.linspace(0.0, 1.0, X, dtype=np.float64)
    w_sale = np.cos(0.5 * np.pi * u).astype(np.float32)
    w_entra = np.sin(0.5 * np.pi * u).astype(np.float32)
    estado = {"pos": 0}

    def emitir(arr: np.ndarray) -> None:
        n = arr.shape[1]
        p = estado["pos"]
        if p < fi:
            k = min(n, fi - p)
            rampa = 0.5 - 0.5 * np.cos(np.pi * (p + np.arange(k)) / fi)
            arr[:, :k] *= rampa.astype(np.float32)
        ini_fo = total - fo
        if p + n > ini_fo and fo > 0:
            idx = np.arange(n) + p
            m = idx >= ini_fo
            rampa = np.ones(n)
            rampa[m] = 0.5 + 0.5 * np.cos(np.pi * (idx[m] - ini_fo) / fo)
            arr *= rampa.astype(np.float32)
        sumidero.escribir(arr)
        estado["pos"] += n
        if progreso:
            progreso(estado["pos"] / total)

    vacio = np.zeros((2, 0), dtype=np.float32)
    cola = None
    for i, seg in enumerate(segmentos):
        ultimo = i == n_seg - 1
        n_seg_total = int(seg.segundos * FS) + (0 if ultimo else X)
        t_camp = 1.0 if i == 0 else fundido_cruce / 2
        buf = vacio
        cabeza_hecha = cola is None
        for b in _flujo_segmento(seg, n_seg_total, t_camp):
            buf = np.concatenate([buf, b], axis=1)
            if not cabeza_hecha:
                if buf.shape[1] < X:
                    continue
                cabeza, buf = buf[:, :X], buf[:, X:]
                emitir(cola * w_sale + cabeza * w_entra)
                cabeza_hecha = True
            if ultimo:
                if buf.shape[1]:
                    emitir(buf)
                buf = vacio
            elif buf.shape[1] > X:
                emitir(buf[:, :-X])
                buf = buf[:, -X:]
        cola = None if ultimo else buf
    sumidero.cerrar()


def plan_continuo(modo: str, minutos: float, seed: int = 1) -> List[Segmento]:
    return [Segmento(modo, minutos * 60, "inicio", f"Sesion continua {modo}", seed)]


def plan_pomodoro(modo: str, trabajo_min: float, descanso_min: float,
                  ciclos: int = 1, seed: int = 1) -> List[Segmento]:
    segs: List[Segmento] = []
    for c in range(ciclos):
        segs.append(Segmento(modo, trabajo_min * 60, "trabajo", f"Trabajo {c + 1}", seed + 10 * c))
        segs.append(Segmento("theta", descanso_min * 60, "descanso", f"Descanso {c + 1}", seed + 10 * c + 5))
    return segs


def sha256_archivo(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()
