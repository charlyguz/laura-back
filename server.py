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

@app.route('/')
def home():
    return 'Backend server is running'

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    try:
        audio_file = request.files['audio']
        native_language = request.form['native_language']
        target_language = request.form['target_language']
        
        # Guarda el audio blob del usuario como .mp3
        wav_filename = f"./audio_file.mp3"
        audio_file.save(wav_filename)
        # Utiliza Whisper para convertir el audio a texto
        transcript = whisper(wav_filename)
    
        # Utiliza GPT para generar una respuesta en el idioma nativo y en el idioma objetivo
        response_text, feedback = start_dialog("", native_language, target_language, transcript)
        
        # Utiliza ElevenLabs para convertir el texto de respuesta a voz en ambos idiomas
        file_path = text_to_speech(response_text)
        with open(file_path,'rb') as wav_file:
            wav_data = wav_file.read()
        # Codificar en base64 para mandar el audio al front
        wav_base64 = base64.b64encode(wav_data)
    
        target_audio_base64 = wav_base64.decode()
        
    
        # Envía el audio como una respuesta de archivo
        response_data = {
            'text_response': response_text,
            'audio_response': target_audio_base64,
            'transcript': transcript,
            'feedback': feedback
        }
        
        return jsonify(response_data)
     except Exception as e:
        print(f"Error: {str(e)}")  
        return jsonify({'error': str(e)}), 500

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

'''
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
'''
def start_dialog(topic, native_language, target_language, user_text):
    conversation = {
        "system": [
            f"""Act as a language teacher. Your name is Laura and you are going to teach your student {target_language}. 
            Give your response in {target_language}. Be as friendly as possible. 
            Always start by greeting the user, telling him/her who you are, and then ask to develop 
            a conversation about {topic}, ask the first question."""
        ],
        "assistant": [],
        "user": [user_text]
    }

    while True:
        ai_says = get_response(conversation)
        print(f"Teacher: {ai_says}\n")
        print(f"Translation: {get_translated_text(ai_says, native_language)}\n")
        conversation["assistant"].append(ai_says)
        user_says = ""  # Set an empty string for user_says to avoid the need for user input
        _, feedback = check_grammar_pronunciation(user_text, native_language)
        print(f"\nFeedback: {feedback}\n")
        if user_says.lower() == "quit" or user_says.lower() == "bye":
            break
        conversation["user"].append(user_says)  # Append the empty string as a user response
        return ai_says, feedback  # Return the AI response without any user input

def get_response(conversation):
    messages = [{"role": "system", "content": conversation["system"][0]}]
    for role in ["assistant", "user"]:
        for message in conversation[role]:
            messages.append({"role": role, "content": message})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response['choices'][0]['message']['content']

def check_grammar_pronunciation(text, native_language):
    prompt = f"The following sentence may have errors, please correct it: '{text}'"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt
    )
    corrected_text = response.choices[0].text.strip()
    if corrected_text == text:
        feedback = "No errors detected."
    else:
        feedback = get_correction_feedback(text, corrected_text, native_language)
    return corrected_text, feedback

def get_correction_feedback(original, corrected, native_language):
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": f"""You are a teacher that gives feedback to language students, 
             youre given two sentences, the original sentece that the user said and the corrected sentence, give feedback on 
             the grammar mistakes of the student, corrections, ways he can say something better, etc. Do it as a natural 
             convesation. Bear in mind that this text was the output of a speech to text model, so dont mind the orthography."""},
            {"role": "user", "content": f"""can you give me feedback on these two sentences?, explain your response in {native_language}
             \nOriginal: '{original}'\nCorrected: '{corrected}"""}
        ]
    )
    feedback = response['choices'][0]['message']['content']
    return feedback

def get_translated_text(text, native_language):
    prompt = f"Translate the following text to {native_language}, Text:'{text}'"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )
    translated_text = response.choices[0].text.strip()
    return translated_text

if __name__ == '__main__':
    app.run()
