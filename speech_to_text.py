import requests
import speech_recognition as sr
import time
import re

API_URL = "http://127.0.0.1:8000/api/"
TOKEN = "ed76b6555bcb6d50f9646cdc0ceff41920f4e0f2"

headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
}


def singularizar_palabra(palabra):
    if palabra.endswith('es'):
        palabra = palabra[:-2]
    elif palabra.endswith('s'):
        palabra = palabra[:-1]
    return palabra

def fetch_products_from_backend():
    response = requests.get(f"{API_URL}products/", headers=headers)
    response.raise_for_status()
    productos = response.json()

    productos_formateados = []
    for product in productos:
        productos_formateados.append({
            "id": product["id"],
            "name": product["name"].lower()
        })

    return productos_formateados

def extraer_cantidad(texto):

    match = re.search(r'\d+', texto)
    if match:
        return int(match.group())


    palabras_a_numeros = {
        "uno": 1, "una": 1,
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
    }
    texto = texto.lower()
    for palabra, numero in palabras_a_numeros.items():
        if palabra in texto:
            return numero

    return None

def detectar_productos_en_texto(texto, productos_backend):
    palabras = texto.lower().split()
    productos_detectados = []

    for producto in productos_backend:
        nombre_producto = producto['name'].lower()


        if any(palabra in nombre_producto for palabra in palabras):
            cantidad = extraer_cantidad(texto) or 1
            productos_detectados.append({
                "product": producto['id'],
                "quantity": cantidad,
            })

    return productos_detectados

def crear_orden_en_backend(detected_items):
    data = {
        "items": detected_items
    }
    response = requests.post(f"{API_URL}orders/", headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def escuchar_y_reconocer():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎙️ Hablá ahora, estoy escuchando!")
        audio = r.listen(source)

    try:
        texto = r.recognize_google(audio, language="es-ES")
        print(f"📝 Texto detectado: {texto}")
        return texto
    except sr.UnknownValueError:
        print("😢 No pude entender el audio.")
        return ""
    except sr.RequestError:
        print("🚫 Error en el servicio de reconocimiento de voz.")
        return ""

if __name__ == "__main__":
    products = fetch_products_from_backend()
    spoken_text = escuchar_y_reconocer()

    if spoken_text:
        detected_items = detectar_productos_en_texto(spoken_text, products)

        if detected_items:
            print(f"✅ Productos detectados: {detected_items}")
            crear_orden_en_backend(detected_items)
            print("✅ Pedido creado exitosamente!")
        else:
            print("😢 No se detectaron productos en el pedido.")
