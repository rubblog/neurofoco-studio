# Informe de verificacion automatica - NeuroFoco Studio

- Fecha: 2026-11-24 22:53:44
- Resultado: **79/79 comprobaciones superadas** (35 s)
- Script: `motor/verificar.py`

| Resultado | Comprobacion | Detalle |
| :---: | :--- | :--- |
| PASS | [beta] nivel RMS entre -23 y -19 dBFS | -21.07 dBFS |
| PASS | [beta] pico < -3 dBFS (sin recortes) | -6.87 dBFS |
| PASS | [beta] modulacion AM en 16 Hz | pico 16.00 Hz, prominencia x91 |
| PASS | [beta] estereo decorrelado (L/R no identicos) | corr 0.01 |
| PASS | [gamma] nivel RMS entre -23 y -19 dBFS | -21.07 dBFS |
| PASS | [gamma] pico < -3 dBFS (sin recortes) | -6.76 dBFS |
| PASS | [gamma] modulacion AM en 40 Hz | pico 40.00 Hz, prominencia x61 |
| PASS | [gamma] estereo decorrelado (L/R no identicos) | corr 0.01 |
| PASS | [alfa] nivel RMS entre -23 y -19 dBFS | -21.09 dBFS |
| PASS | [alfa] pico < -3 dBFS (sin recortes) | -7.25 dBFS |
| PASS | [alfa] modulacion AM en 10 Hz | pico 10.00 Hz, prominencia x63 |
| PASS | [alfa] estereo decorrelado (L/R no identicos) | corr 0.01 |
| PASS | [theta] nivel RMS entre -23 y -19 dBFS | -21.12 dBFS |
| PASS | [theta] pico < -3 dBFS (sin recortes) | -7.35 dBFS |
| PASS | [theta] modulacion AM en 6 Hz | pico 6.00 Hz, prominencia x87 |
| PASS | [theta] estereo decorrelado (L/R no identicos) | corr 0.01 |
| PASS | [ruido] nivel RMS entre -23 y -19 dBFS | -21.07 dBFS |
| PASS | [ruido] pico < -3 dBFS (sin recortes) | -7.10 dBFS |
| PASS | [ruido] sin modulacion dominante | prominencia x3.4 |
| PASS | [ruido] estereo decorrelado (L/R no identicos) | corr -0.00 |
| PASS | ruido rosa: pendiente ~ -3 dB/oct (400-3000 Hz) | -3.08 dB/oct |
| PASS | ruido marron: pendiente ~ -6 dB/oct (40-400 Hz) | -6.01 dB/oct |
| PASS | campana 'trabajo' pico <= 0.26 (suave) | 0.250 |
| PASS | campana 'trabajo' se extingue (energia final < 1% de la inicial) | 0.9737 % |
| PASS | campana 'descanso' pico <= 0.26 (suave) | 0.250 |
| PASS | campana 'descanso' se extingue (energia final < 1% de la inicial) | 0.1711 % |
| PASS | campana 'inicio' pico <= 0.26 (suave) | 0.250 |
| PASS | campana 'inicio' se extingue (energia final < 1% de la inicial) | 0.9913 % |
| PASS | duracion exacta = suma de segmentos (54 s) | 54.000 s |
| PASS | pico < -1 dBFS y sin recortes | -5.15 dBFS, 0 recortes |
| PASS | sin clics en la transicion de 24 s | max|dx| local/mediana = 1.30 |
| PASS | sin clics en la transicion de 36 s | max|dx| local/mediana = 0.74 |
| PASS | arranque con fundido (sin golpe inicial) |  |
| PASS | sesion60_beta.mp3: 3600.0 s ~ 3600.0 s, 44100 Hz |  |
| PASS | sesion60_beta.mp3: nivel RMS/pico del manifiesto | rms -21.06 pico -5.04 |
| PASS | sesion60_beta.mp3: AM 16 Hz sobrevive al MP3 | 16.00 Hz x81 |
| PASS | sesion60_alfa.mp3: 3600.0 s ~ 3600.0 s, 44100 Hz |  |
| PASS | sesion60_alfa.mp3: nivel RMS/pico del manifiesto | rms -21.07 pico -5.47 |
| PASS | sesion60_alfa.mp3: AM 10 Hz sobrevive al MP3 | 10.00 Hz x60 |
| PASS | sesion60_ruido.mp3: 3600.0 s ~ 3600.0 s, 44100 Hz |  |
| PASS | sesion60_ruido.mp3: nivel RMS/pico del manifiesto | rms -21.07 pico -5.76 |
| PASS | sesion60_ruido.mp3: sin modulacion dominante | x3.5 |
| PASS | sesion30_gamma.mp3: 1800.0 s ~ 1800.0 s, 44100 Hz |  |
| PASS | sesion30_gamma.mp3: nivel RMS/pico del manifiesto | rms -21.08 pico -5.73 |
| PASS | sesion30_gamma.mp3: AM 40 Hz sobrevive al MP3 | 40.00 Hz x54 |
| PASS | pomo50_beta.mp3: 3600.0 s ~ 3600.0 s, 44100 Hz |  |
| PASS | pomo50_beta.mp3: nivel RMS/pico del manifiesto | rms -21.07 pico -5.36 |
| PASS | pomo50_beta.mp3: AM 16 Hz sobrevive al MP3 | 16.00 Hz x83 |
| PASS | pomo50_gamma.mp3: 3600.0 s ~ 3600.0 s, 44100 Hz |  |
| PASS | pomo50_gamma.mp3: nivel RMS/pico del manifiesto | rms -21.08 pico -5.55 |
| PASS | pomo50_gamma.mp3: AM 40 Hz sobrevive al MP3 | 40.00 Hz x57 |
| PASS | pomo50_alfa.mp3: 3600.0 s ~ 3600.0 s, 44100 Hz |  |
| PASS | pomo50_alfa.mp3: nivel RMS/pico del manifiesto | rms -21.08 pico -5.94 |
| PASS | pomo50_alfa.mp3: AM 10 Hz sobrevive al MP3 | 10.00 Hz x61 |
| PASS | pomo50_ruido.mp3: 3600.0 s ~ 3600.0 s, 44100 Hz |  |
| PASS | pomo50_ruido.mp3: nivel RMS/pico del manifiesto | rms -21.07 pico -5.47 |
| PASS | pomo50_ruido.mp3: sin modulacion dominante | x3.6 |
| PASS | pomo25_beta.mp3: 1800.0 s ~ 1800.0 s, 44100 Hz |  |
| PASS | pomo25_beta.mp3: nivel RMS/pico del manifiesto | rms -21.07 pico -5.33 |
| PASS | pomo25_beta.mp3: AM 16 Hz sobrevive al MP3 | 16.00 Hz x83 |
| PASS | pomo25_gamma.mp3: 1800.0 s ~ 1800.0 s, 44100 Hz |  |
| PASS | pomo25_gamma.mp3: nivel RMS/pico del manifiesto | rms -21.07 pico -4.97 |
| PASS | pomo25_gamma.mp3: AM 40 Hz sobrevive al MP3 | 40.00 Hz x52 |
| PASS | pomo25_alfa.mp3: 1800.0 s ~ 1800.0 s, 44100 Hz |  |
| PASS | pomo25_alfa.mp3: nivel RMS/pico del manifiesto | rms -21.07 pico -5.51 |
| PASS | pomo25_alfa.mp3: AM 10 Hz sobrevive al MP3 | 10.00 Hz x61 |
| PASS | pomo25_ruido.mp3: 1800.0 s ~ 1800.0 s, 44100 Hz |  |
| PASS | pomo25_ruido.mp3: nivel RMS/pico del manifiesto | rms -21.06 pico -5.82 |
| PASS | pomo25_ruido.mp3: sin modulacion dominante | x3.4 |
| PASS | pausa20_theta.mp3: 1200.0 s ~ 1200.0 s, 44100 Hz |  |
| PASS | pausa20_theta.mp3: nivel RMS/pico del manifiesto | rms -21.09 pico -6.34 |
| PASS | pausa20_theta.mp3: AM 6 Hz sobrevive al MP3 | 6.00 Hz x78 |
| PASS | demo_campanas.mp3: 42.0 s ~ 42.0 s, 44100 Hz |  |
| PASS | demo_campanas.mp3: nivel RMS/pico del manifiesto | rms -21.38 pico -6.23 |
| PASS | muestras_wav/muestra_theta.wav: 90.0 s, 44.1 kHz 16-bit estero, SHA-256 | rms -21.26 pico -6.06 |
| PASS | muestras_wav/muestra_beta.wav: 90.0 s, 44.1 kHz 16-bit estero, SHA-256 | rms -21.23 pico -5.59 |
| PASS | muestras_wav/muestra_ruido.wav: 90.0 s, 44.1 kHz 16-bit estero, SHA-256 | rms -21.23 pico -6.05 |
| PASS | muestras_wav/muestra_gamma.wav: 90.0 s, 44.1 kHz 16-bit estero, SHA-256 | rms -21.23 pico -5.81 |
| PASS | muestras_wav/muestra_alfa.wav: 90.0 s, 44.1 kHz 16-bit estero, SHA-256 | rms -21.24 pico -6.77 |
