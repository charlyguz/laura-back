from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
import requests
import os
from elevenlabs import Voice, VoiceDesign, Gender, Age, Accent
from elevenlabs import set_api_key, generate, save
from io import BytesIO
import base64

whisper_api_key = os.environ['WHISPER_API_KEY']
gpt_api_key = os.environ['GPT_API_KEY']
elevenlabs_api_key = os.environ['ELEVENLABS_API_KEY']
set_api_key(elevenlabs_api_key) 
openai.api_key = gpt_api_key
app = Flask(__name__)
CORS(app)

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    audio_file = request.files['audio']
    native_language = request.form['native_language']
    target_language = request.form['target_language']
    
    # Utiliza GPT para generar una respuesta en el idioma nativo y en el idioma objetivo
    response_text = get_response("", native_language, target_language)
    
    # Utiliza ElevenLabs para convertir el texto de respuesta a voz en ambos idiomas
    file_path = text_to_speech(response_text)
    with open(file_path,'rb') as wav_file:
        wav_data = wav_file.read()
    # Codificar en base64
    wav_base64 = base64.b64encode(wav_data)

    target_audio_base64 = wav_base64.decode()
    
    # Guarda el audio blob como .mp3
    wav_filename = f"./audio_file.mp3"
    audio_file.save(wav_filename)
    # Utiliza Whisper para convertir el audio a texto
    transcript = whisper(wav_filename)
    # Envía el audio como una respuesta de archivo
    response_data = {
        'text_response': response_text,
        'audio_response': target_audio_base64,
        'transcript': transcript
    }
    
    return jsonify(response_data)

def whisper(wav_filename):
    openai.api_key = whisper_api_key
    audio = open(wav_filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio)
    
    return transcript['text']

def text_to_speech(texto):
    # Utiliza la API de ElevenLabs para convertir el texto en voz
    audio = generate(
    text=texto,
    voice="Rachel",
    model='eleven_multilingual_v1'
        )
    save(audio, "11L_file.mp3")
    route = "11L_file.mp3"
    
    return route

def get_response(text, native_language, target_language):
    # Aquí iría el código para enviar una solicitud a la API de GPT-4
    # y generar una respuesta en el idioma nativo y en el idioma objetivo
    # Por ejemplo:
    if text == "":
        prompt = f"Tu eres Laura. Laura como profesora de lenguas, le enseña a su alumno a hablar {target_language} y le repetite todo en {native_language} para que aprenda como se escucha la misma frase en los 2 idiomas. Laura es muy abierta y siempre le pregunta a su alumno de que tema quiere hablar hoy. Tienes que simular ser Laura para dar clases de idiomas. Solo puedes dar un parrafo de texto a la vez"
    else:
        prompt = text 
    
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        temperature=0.5
    )

    
    response_text = response["choices"][0]["text"]
    print (response_text)
    return response_text

if __name__ == '__main__':
    app.run(debug=True)
