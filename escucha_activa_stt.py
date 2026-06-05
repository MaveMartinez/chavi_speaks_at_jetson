# escucha_activa_stt.py — JETSON ORIN NANO
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE   = 48000
BLOCK_SIZE    = 4096
VAD_THRESHOLD = 0.05
SILENCE_SECS  = 1.8
MAX_SECS      = 15

print("[STT] Cargando Whisper en CUDA...")
model = WhisperModel("small", device="cpu", compute_type="int8")

print("[STT] ✅ Modelo cargado")

def grabar_hasta_silencio():
    chunks         = []
    silence_frames = int(SAMPLE_RATE * SILENCE_SECS / BLOCK_SIZE)
    max_frames     = int(SAMPLE_RATE * MAX_SECS / BLOCK_SIZE)
    silent_count   = 0
    grabando       = False

    print("[STT] Escuchando...")
    with sd.InputStream(samplerate=48000, channels=1,
                    dtype="int16", blocksize=BLOCK_SIZE, device=27) as stream:
        for _ in range(max_frames):
            chunk, _ = stream.read(BLOCK_SIZE)
            chunk_float = chunk.astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(chunk_float ** 2)))
            print(f"[DEBUG] RMS: {rms:.5f}")
            if rms > VAD_THRESHOLD:
                grabando = True
                silent_count = 0
                chunks.append(chunk.copy())
            elif grabando:
                chunks.append(chunk.copy())
                silent_count += 1
                if silent_count >= silence_frames:
                    break

    if not chunks:
        return np.zeros(BLOCK_SIZE, dtype="float32")
    return np.concatenate(chunks, axis=0).flatten()

def escuchar() -> str:
    audio = grabar_hasta_silencio()
    audio_float = audio.astype(np.float32) / 32768.0
    
    # Resamplear de 48000 a 16000
# Resamplear de 48000 a 16000 sin scipy
    audio_16k = audio_float[::3]
    
    segments, _ = model.transcribe(audio_16k, language="es", vad_filter=True)
    texto = " ".join(s.text for s in segments).strip()
    print(f"[STT] Transcripción: '{texto}'")
    return texto
