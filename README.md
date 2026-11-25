# NeuroFoco Studio

Sonido de estudio **sintetizado en tu propio equipo**: sin internet, sin suscripciones, sin telemetría.
Sustituye al antiguo borrador *RubBio-Sounds* (que se conserva intacto como archivo histórico en `Proyectos raros a medias`).

## Qué incluye

| Pieza | Dónde | Para qué |
| :--- | :--- | :--- |
| **App web offline** (Web Audio API) | `app/index.html` (doble clic en `Iniciar_NeuroFoco.bat`) | Síntesis en tiempo real, Pomodoro con campanas, mezcla, diario de valoraciones, biblioteca y dossier científico |
| **Biblioteca renderizada** | `audio/*.mp3`, `audio/muestras_wav/*.wav` | Sesiones de 60 min, Pomodoros 50/10 y 25/5 por modo, pausa de 20 min, demo de campanas |
| **Motor DSP en Python** | `motor/neurofoco_dsp.py` | Misma síntesis, por bloques (streaming), para generar archivos |
| **Generador a medida** | `motor/generar_pista.py` | Cualquier duración / Pomodoro / modo, MP3 o WAV |
| **Verificador objetivo** | `motor/verificar.py` → `docs/informe_verificacion.md` | FFT de la modulación, pendientes espectrales, niveles, clics, decodificación de los MP3 |
| **Dossier científico** | `docs/dossier_cientifico.md` y pestaña *Ciencia* | Qué respalda cada frecuencia (y qué no) |

## Los cinco modos

| Modo | Pulso (AM) | Pensado para | Respaldo (resumen) |
| :--- | :---: | :--- | :--- |
| 🎯 Foco profundo | 16 Hz (beta) | Estudio técnico, supuestos, redactar | ★★★☆☆ prometedor |
| ⚡ Repaso activo | 40 Hz (gamma) | Tarjetas / test, ≤ 25 min | ★☆☆☆☆ preliminar |
| 📖 Lectura y redacción | 10 Hz (alfa) | Leer manuales, subrayar | ★☆☆☆☆ débil |
| 🌙 Descanso activo | 6 Hz (theta) | Pausas del Pomodoro | ★☆☆☆☆ muy débil |
| 🌧️ Enmascaramiento puro | sin pulso | Fatiga sensorial, ruido ambiente | ★★★☆☆ bueno para enmascarar |

Las estrellas son un resumen divulgativo propio. Ver `docs/dossier_cientifico.md` (con matices y conflictos de interés).

## Cómo suena (diseño)

* **Lecho** de ruido marrón filtrado (grave y cálido) + **aire** de ruido rosa en banda 180-5200 Hz.
* **Pad** de cuatro voces con acordes que se funden lentamente (cada 56-80 s) y vibrato mínimo; acordes distintos por modo.
* **Modulación de amplitud** de coseno elevado a la frecuencia del modo, con nivel medio constante (no «sube y baja» el volumen global).
* **Campanas** tipo cuenco: parciales inarmónicos con batido suave. Trabajo = dos golpes ascendentes; descanso = un golpe grave y largo.
* Nivel de programa −21 dBFS RMS, picos < −5 dBFS, sin recortes. Fundidos cruzados de 3 s entre trabajo y descanso.

## Uso rápido

```text
Iniciar_NeuroFoco.bat                      # abre la app
Renderizar_Biblioteca.bat                  # regenera todos los audios y los verifica
python motor\generar_pista.py --modo beta --pomodoro 40 8 --ciclos 3 --salida mi_pista.mp3
python motor\generar_pista.py --modo alfa --minutos 90 --wav --salida lectura.wav
python motor\verificar.py                  # informe en docs\informe_verificacion.md
```

Dependencias (solo para renderizar): `numpy`, `scipy`, `lameenc`; para verificar MP3: `miniaudio`. La app web no necesita nada.

## Integración con el AOA

El panel de Tutor Integral tiene un botón **🎛️ NeuroFoco Studio** en la cabecera que abre `http://127.0.0.1:8780/neurofoco/app/index.html`. El servidor solo expone `app/` y `audio/` (con soporte de rangos HTTP para poder avanzar dentro de los MP3). Prueba: `Tutor Integral/tests/test_neurofoco_route.py`.

## Límites honestos

* Los audios **no sustituyen** a hábitos de estudio, sueño ni pausas, y su efecto sobre el rendimiento no está probado para esta síntesis concreta.
* La pestaña *Tu propia evidencia* de la app guarda tus valoraciones 1-5 por modo: es la mejor forma de comprobar qué te funciona.
* Volumen moderado. Si tienes epilepsia, acúfenos o hiperacusia, consulta antes de usar sonidos pulsados.

© Rubén García Fuentes. Acceso libre para estudio y práctica personal. Enlace original compartible. Prohibida la redistribución no autorizada.
