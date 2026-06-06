# CHAVI Speaks at Jetson Orin Nano

Asistente conversacional por voz que corre completamente en local sobre una **NVIDIA Jetson Orin Nano**.

Pipeline: Micrófono USB → STT (Whisper) → LLM (Ollama + Llama 3.2) → TTS (Piper) → Parlante

---

## Requisitos de Hardware

- NVIDIA Jetson Orin Nano (JetPack 5.x o 6.x)
- Micrófono USB (probado con Usb_Mic YC1006)
- Parlante con salida USB o jack 3.5mm
- Conexión a internet (solo para instalación)

---

## 1. Clonar el repositorio

```bash
git clone https://github.com/MaveMartinez/chavi_speaks_at_jetson.git
cd chavi_speaks_at_jetson
```

---

## 2. Instalar dependencias Python

```bash
pip install faster-whisper sounddevice numpy httpx pyserial
```

> **Nota:** scipy NO es compatible con NumPy 2.x en Jetson. No instalar.

---

## 3. Instalar Ollama y descargar el modelo LLM

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2:3b
```

Verificar que Ollama esté corriendo:
```bash
curl http://localhost:11434/api/tags
```

---

## 4. Configurar Piper TTS

Descargar el binario ARM64 y el modelo de voz español:

```bash
# Binario Piper para ARM64 (Jetson)
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz
tar -xzf piper_linux_aarch64.tar.gz

# Modelo de voz español
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json
```

Verificar que Piper funciona:
```bash
echo "Hola mundo" | ~/chavi_speaks_at_jetson/piper/piper \
  --model ~/chavi_speaks_at_jetson/es_ES-davefx-medium.onnx \
  --output_raw | aplay -r 22050 -f S16_LE -t raw
```

Deberías escuchar "Hola mundo" por el parlante.

---

## 5. Configurar el micrófono USB

Verificar que el micrófono es detectado:
```bash
arecord -l
```

Debe aparecer algo como:
```
card 0: UsbMic [Usb_Mic], device 0: USB Audio [USB Audio]
```

Fijar como dispositivo de entrada por defecto:
```bash
pulseaudio --kill && pulseaudio --start
pacmd set-default-source alsa_input.usb-YC1006_Usb_Mic-00.mono-fallback
```

Verificar el ID del dispositivo en sounddevice:
```bash
python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

Busca el número de `Usb_Mic` o `USB Audio` en la lista. Actualiza `device=` en `escucha_activa_stt.py`:

```python
with sd.InputStream(samplerate=48000, channels=1,
                    dtype="int16", blocksize=BLOCK_SIZE, device=24) as stream:
```

> El número de device puede variar entre reinicios. Si el micrófono no responde, repetir este paso.

---

## 6. Validar STT (transcripción de voz)

```bash
python3 validar_stt.py
```

Habla al micrófono. Debes ver en terminal:
```
✅ TRANSCRIPCIÓN: Hola
```

Si el RMS se queda en ~0.00040, el device ID es incorrecto — repetir paso 5.
Si el RMS sube pero no transcribe, verificar que `VAD_THRESHOLD = 0.05` en `escucha_activa_stt.py`.

---

## 7. Correr el sistema completo

```bash
python3 main.py
```

Flujo esperado:
```
[MAIN] Esperando a que hables...
[STT] Escuchando...
[STT] Transcripción: 'Hola'
[MAIN] Tú: Hola
[MAIN] XAVI: Hola! ¿En qué puedo ayudarte?
```

---

## Parámetros importantes en escucha_activa_stt.py

| Parámetro | Valor | Descripción |
|---|---|---|
| `SAMPLE_RATE` | 48000 | Hz soportado por el mic USB |
| `VAD_THRESHOLD` | 0.05 | Sensibilidad del micrófono |
| `SILENCE_SECS` | 1.8 | Segundos de silencio para cortar grabación |
| `device` | 24 | ID del micrófono USB (puede variar) |

---

## Solución de problemas frecuentes

**RMS siempre ~0.00040 (no detecta voz)**
```bash
pacmd set-default-source alsa_input.usb-YC1006_Usb_Mic-00.mono-fallback
```
Verificar device ID con `python3 -c "import sounddevice; print(sounddevice.query_devices())"` y actualizar en el código.

**Error: Invalid sample rate**
El micrófono solo acepta 44100 o 48000 Hz. Verificar que `SAMPLE_RATE = 48000`.

**Error: CTranslate2 not compiled with CUDA**
Usar CPU por ahora:
```python
model = WhisperModel("small", device="cpu", compute_type="int8")
```

**Ollama no disponible**
```bash
ollama serve &
```

**Piper no genera audio (0 bytes)**
Verificar ruta del binario y del modelo `.onnx` en `main.py`.

---

## Estructura del proyecto

```
chavi_speaks_at_jetson/
├── main.py                       # Loop principal
├── escucha_activa_stt.py         # STT con faster-whisper
├── llamas.py                     # LLM con Ollama
├── serial_out.py                 # Comunicación ESP32
├── validar_stt.py                # Script de prueba STT
├── piper/                        # Binario Piper ARM64 (descargar)
│   └── piper
├── es_ES-davefx-medium.onnx      # Modelo de voz español (descargar)
└── es_ES-davefx-medium.onnx.json
```

---

## Notas de migración desde laptop

- Vosk reemplazado por **faster-whisper** (CUDA/CPU)
- ffplay reemplazado por **aplay** (ALSA nativo)
- Modelo LLM cambiado a `llama3.2:3b` (versión fp16 cuando se active CUDA)
- Puerto serial cambiado a `/dev/ttyUSB0`
