from escucha_activa_stt import escuchar

print("Habla algo. Ctrl+C para salir.")

while True:
    try:
        texto = escuchar()
        if texto:
            print(f"✅ TRANSCRIPCIÓN: {texto}\n")
        else:
            print("[!] No se detectó voz\n")
    except KeyboardInterrupt:
        print("\nDetenido.")
        break
