# main.py
# Loop principal asíncrono para Jetson: voz → Ollama → TTS NATIVO (aplay)

import os
import shutil
import sys
import asyncio
from escucha_activa_stt import escuchar
from llamas import conversar_xavi, verificar_ollama

cola_audio = asyncio.Queue()

def verificar_dependencias_audio():
    """Verifica que Piper esté disponible en el PATH global de Linux."""
    piper_bin = shutil.which("piper") or "piper"
    aplay_bin = shutil.which("aplay") or "aplay"
    
    print(f"[AUDIO] ✅ Entorno listo para Linux (Piper + aplay)")
    return True

async def reproducir_audio(texto: str):
    # Limpieza estándar de caracteres especiales
    texto_limpio = (
        texto.replace('"', '')
        .replace("'", "")
        .replace('\n', ' ')
        .replace('¿', '')
        .replace('?', '')
        .replace('¡', '')
        .replace('!', '')
        .replace('á', 'a')
        .replace('é', 'e')
        .replace('í', 'i')
        .replace('ó', 'o')
        .replace('ú', 'u')
        .replace('ñ', 'n')
    )
    
    modelo_onnx = os.path.join(os.getcwd(), "es_ES-davefx-medium.onnx")
    
    # Configuración nativa para Linux
    piper_bin = os.path.join(os.getcwd(), "piper", "piper")
    args_piper = [piper_bin, "--model", modelo_onnx, "--length-scale", "1.3", "--output_raw"]

    # Redirigimos el RAW directamente al sistema ALSA usando aplay a la tasa de muestreo del modelo
    args_aplay = ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw"]
    
    try:
        p_piper = await asyncio.create_subprocess_exec(
            *args_piper,
            stdin  = asyncio.subprocess.PIPE,
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE
        )
        stdout_piper, stderr_piper = await p_piper.communicate(
            input=texto_limpio.encode('utf-8') + b'\n'
        )

        bytes_calculados = len(stdout_piper)
        print(f"[PIPER] Frase procesada: '{texto_limpio}' | {bytes_calculados} bytes.")

        if stdout_piper and bytes_calculados > 0:
            p_aplay = await asyncio.create_subprocess_exec(
                *args_aplay,
                stdin  = asyncio.subprocess.PIPE,
                stdout = asyncio.subprocess.DEVNULL,
                stderr = asyncio.subprocess.DEVNULL
            )
            await p_aplay.communicate(input=stdout_piper)
        else:
            print("[⚠️ ADVERTENCIA] Buffer de audio vacío.")
    except Exception as e:
        print(f"[AUDIO] Error en la tubería asíncrona: {e}")

async def worker_audio():
    while True:
        texto = await cola_audio.get()
        if texto is None:
            cola_audio.task_done()
            break
        await reproducir_audio(texto)
        cola_audio.task_done()

async def procesar_conversacion():
    if not verificar_dependencias_audio():
        return
    
    tarea_worker = asyncio.create_task(worker_audio())

    try:
        while True:
            print("\n[MAIN] Esperando a que hables...")
            texto = await asyncio.to_thread(escuchar)

            if not texto or texto.strip() == "":
                continue

            print(f"[MAIN] Tú: {texto}")
            print("[MAIN] XAVI: ", end="", flush=True)
            
            oracion_actual = ""
            
            async for token in conversar_xavi(texto):
                print(token, end="", flush=True)
                oracion_actual += token
                
                if any(puntuacion in token for puntuacion in ['.', '!', '?']):
                    if oracion_actual.strip():
                        await cola_audio.put(oracion_actual.strip())
                        oracion_actual = ""
                
                await asyncio.sleep(0.01)
            
            if oracion_actual.strip():
                await cola_audio.put(oracion_actual.strip())

            await cola_audio.join()

    finally:
        await cola_audio.put(None)
        await tarea_worker

async def main_async():
    # Bypass temporal del puerto serial del ESP32 para priorizar solo conversación fluida por IA
    print("[SERIAL] Modo Simulación activo (Bypass).")

    if not await verificar_ollama():
        print("[MAIN] ❌ Ollama no está disponible en localhost:11434.")
        return

    print("=" * 55)
    print("  XAVI — Modo Conversacional Linux Nativo (Jetson Orin)")
    print("  Habla claro al micrófono USB. Ctrl+C para salir.")
    print("=" * 55)

    try:
        await procesar_conversacion()
    except KeyboardInterrupt:
        print("\n[MAIN] Detenido por el usuario.")

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass
