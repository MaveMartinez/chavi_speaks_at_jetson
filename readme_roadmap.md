# XAVI — Async Voice Assistant

Async voice assistant that pipelines speech-to-text (Vosk), a local LLM (Ollama), and text-to-speech (Piper) with a producer-consumer audio queue — delivering low-latency responses by streaming TTS playback while the model is still generating.

---

## Requirements

- Python 3.10+
- Windows 10/11 (tested) or Linux/Jetson (partial support in code)
- Microphone and speakers
- ~2 GB RAM free for the LLM

---

## Setup Roadmap

### 1. Clone the repository
```
git clone https://github.com/MaveMartinez/Chavi_speaks.git
cd Chavi_speaks
```

### 2. Create and activate virtual environment
```
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python dependencies
```
pip install -r requirements.txt
```

### 4. Install Ollama
Download and run the installer from: https://ollama.com/download

Then pull the LLM model:
```
ollama pull llama3.2:3b
```

### 5. Install Piper (TTS)
Download `piper_windows_amd64.zip` from:
https://github.com/rhasspy/piper/releases

Extract the zip and place the entire `piper/` folder inside the project root:
```
Chavi_speaks/
  piper/
    piper.exe
    onnxruntime.dll
    espeak-ng-data/
    ...
```

### 6. Download the voice model
Download these two files from the rhasspy/piper-voices repository:
- `es_ES-davefx-medium.onnx`
- `es_ES-davefx-medium.onnx.json`

Place both files in the project root (same folder as `main.py`).

Direct link: https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_ES/davefx/medium

### 7. Download the Vosk speech recognition model
Download `vosk-model-small-es-0.42.zip` from:
https://alphacephei.com/vosk/models

Extract and place the folder in the project root:
```
Chavi_speaks/
  vosk-model-small-es-0.42/
```

### 8. (Optional) ESP32 serial connection
If using the ESP32 for LED eye animations, connect it via USB and update the COM port in `serial_out.py`:
```python
PUERTO = 'COM3'  # Change to your port
```
If no ESP32 is connected, the program runs normally without it.

---

## Run

Start Ollama in a separate terminal:
```
ollama serve
```

Then run the assistant:
```
python main.py
```

---

## Project structure

```
Chavi_speaks/
  main.py                        # Main async loop: STT → LLM → TTS
  escucha_activa_stt.py          # Vosk speech-to-text
  llamas.py                      # Ollama LLM client (streaming)
  serial_out.py                  # ESP32 serial communication
  check_ollama_endpoint.py       # Diagnostic: verify Ollama is running
  test_audio.py                  # Diagnostic: verify Piper + ffplay
  es_ES-davefx-medium.onnx.json  # Piper voice config
  requirements.txt
  .gitignore
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Piper no encontrado` | Check that `piper/piper.exe` exists inside the project folder |
| `Content-Length: 0 bytes` | Piper DLLs missing — re-extract the full zip, not just piper.exe |
| `Ollama no disponible` | Run `ollama serve` in a separate terminal before starting |
| `Vosk NameError` | The vosk model folder is missing or misnamed — must be `vosk-model-small-es-0.42` |
| `COM3 not found` | ESP32 not connected — safe to ignore if not using serial |
