import slack

def test_slack_message():
    TOKEN = 'xoxb-2569679174866-6651760390341-nXgxbFm3vJVs2eSq30Se0pZF'  # Reemplaza con tu token real
    CHANNEL_ID = 'C054TP80E5V'  # Reemplaza con el ID del canal obtenido
    client = slack.WebClient(token=TOKEN)

    try:
        response = client.chat_postMessage(
            channel=CHANNEL_ID,  # Usa el ID del canal
            text="🚀 Hola desde la prueba de Slack. Este es un mensaje de prueba para confirmar la integración."
        )
        if response["ok"]:
            print("✅ Mensaje enviado correctamente.")
        else:
            print("❌ Error en el envío del mensaje:", response)
    except Exception as e:
        print(f"⚠️ Error al enviar mensaje: {e}")

# Llama a la función para probar
test_slack_message()
