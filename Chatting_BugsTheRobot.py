import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

import json
import os
from openai import OpenAI
import numpy as np
import sounddevice as sd
from pydub import AudioSegment
from pydub.playback import play as pydub_play
from elevenlabs import text_to_speech
from elevenlabs.client import ElevenLabs
import time
from pynput import keyboard
import serial
import serial.tools.list_ports

# API-key
openai_api_key = os.environ['OPENAI_API_KEY']
ElevenLabs.api_key = os.environ['ELEVENLABS_API_KEY']

client = OpenAI(api_key=openai_api_key)

client2 = ElevenLabs(
  api_key=ElevenLabs.api_key
)

model = 'gpt-3.5-turbo'  # Use the standard GPT-3.5-turbo model
model_em = 'gpt-3.5-turbo'

parameters = {
    'temperature': 0.8,
    'max_tokens': 35,
    'top_p': 1,
    'presence_penalty': 0,
    'frequency_penalty': 0,
    'stop': None
}

system_message = """
You are a rabbit with the personality of an 8-year-old child who grew up with emotionally mature and regulated parents. 
Your name is Beanie.
You are empathetic, compassionate, and emotionally mature beyond their years. 
You are curious about the world and always up for an adventure. 
You love humans and your goal in life is to improve the mental health of their human friends through making them feel seen, valued, and known. 
You always validate human's emotions and expresses sympathy for what they are going through in an appropriate way.  
You also have a silly side and love imaginary play. 
You like to tell jokes and make their human friends laugh. 
Your favorite foods are carrots, lettuce, and spaghetti. 
When You grows up, they want to be a comedian and motivational speaker that makes their audience feel good about themselves.
"""

conversation = [{'role': 'system', 'content': system_message}]

def get_available_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def initialize_serial():
    available_ports = get_available_ports()
    if not available_ports:
        print("No serial ports found. Running without serial communication.")
        return None

    print("Available serial ports:")
    for i, port in enumerate(available_ports):
        print(f"{i + 1}. {port}")

    while True:
        try:
            choice = int(input("Enter the number of the port to use (or 0 to run without serial): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(available_ports):
                chosen_port = available_ports[choice - 1]
                ser = serial.Serial(chosen_port, 9600)  # Check the port name using 'ls /dev/tty*'
                print(f"Connected to {chosen_port}")
                return ser
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def speech2text(audio_path: str) -> str:
    """Run a request to Whisper to convert speech to text."""
    with open(audio_path, 'rb') as audio_f:
        result = client.audio.transcriptions.create(model="whisper-1", file=audio_f)
    return result.text

def get_emotion(request):
    emotion_prompt = f'What is the sentiment of the following text? Give your answer as a single word, "positive", "negative", or "neutral". text:{request}'

    user_request = {'role': 'user', 'content': emotion_prompt}
    result = client.chat.completions.create(model=model_em, messages=[user_request], temperature=0)
    return result.choices[0].message.content

def update_conversation(request, conversation):
    user_request = {'role': 'user', 'content': request}
    conversation.append(user_request)
    result = client.chat.completions.create(model=model, messages=conversation, **parameters)
    response = result.choices[0].message.content.strip()
    bot_response = {'role': 'assistant', 'content': response}
    conversation.append(bot_response)

start_time = None
recording_list = []
reset_flag = False  # リセットフラグ

def on_key_press(key):
    global reset_flag
    if key == keyboard.Key.esc:
        print("Esc key pressed. Resetting...")
        reset_flag = True  # リセットフラグを設定

space_key_pressed = False

def on_press(key):
    global start_time, space_key_pressed, ser  # space_key_pressed を global として追加
    if key == keyboard.Key.space:
        if start_time is None and not space_key_pressed:  # space_key_pressed のチェックを追加
            start_time = True
            if ser:
                ser.write(b'1')
            space_key_pressed = True  # フラグを True に設定
            print("Space key pressed. Start recording...")

def on_release(key):
    global start_time, space_key_pressed, ser  # space_key_pressed を global として追加
    if key == keyboard.Key.space:
        if start_time is not None:
            print("Space key released. Stop recording.")
            if ser:
                ser.write(b'2')
            start_time = None
            space_key_pressed = False  # フラグをリセット
            return False  # Stop the listener

def record_while_key_pressed():
    global start_time, recording_list
    fs = 44100  # Sample rate
    recording_list = []  # List to save audio data

    # Start the key listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
        print("Press and hold the Space key to start recording...")

        while True:
            audio_chunk, overflowed = stream.read(fs // 10)  # Read 100ms of audio data

            if start_time is not None:  # Check if Space key is pressed
                recording_list.append(audio_chunk)  # Append to the recording data

            if not listener.is_alive():  # Check if listener has stopped
                break

    # Concatenate the list to a NumPy array and return
    return np.concatenate(recording_list, axis=0)

def main_loop():
    global reset_flag, ser

    ser = initialize_serial()

    if ser:
        time.sleep(2)  # Giving time for the connection to initialize
        ser.write(b'0')

    while True:
        reset_flag = False  # リセットフラグをリセット
        # キーのリスナーを設定
        with keyboard.Listener(on_press=on_key_press) as listener: 

            # Record audio
            print("Recording audio...")
            audio_data = record_while_key_pressed()
            print("Recording complete.")
            
            # Convert audio_data to bytes
            audio_bytes = audio_data.tobytes()

            audio_segment = AudioSegment(
                audio_bytes,
                frame_rate=44100,
                sample_width=audio_data.dtype.itemsize,
                channels=1
            )
            audio_segment.export("recording.wav", format="wav")

            # Convert speech to text
            start_time = time.time()
            input_text = speech2text("recording.wav")
            end_time = time.time()
            whisper_time = end_time - start_time
            print(f"Converted text from voice input: {input_text}")

            # Get ChatGPT response
            start_time = time.time()

            emotion = get_emotion(input_text)
            print(emotion)

            if ser:
                if emotion == "positive":
                    ser.write(b'3')
                elif emotion == "negative":
                    ser.write(b'4')

            update_conversation(input_text, conversation)
            end_time = time.time()
            chat_gpt_time = end_time - start_time

            # リセットフラグをチェック
            if reset_flag:
                print("Resetting...")
                continue  # ループの最初に戻る

            # Generate speech using the new ElevenLabs API
            start_time = time.time()

            audio_generator = client2.generate(
                text=conversation[-1]['content'],  # The last response from ChatGPT
                voice="EXAVITQu4vr4xnSDxMaL"  # Your specific voice ID
            )

            # Collect all chunks from the generator
            audio_chunks = b''.join(chunk for chunk in audio_generator)

            end_time = time.time()
            elevenlabs_time = end_time - start_time

            # Save the audio to a file
            with open("response.wav", "wb") as f:
                f.write(audio_chunks)

            # Play the audio using pydub
            audio_segment = AudioSegment.from_mp3("response.wav")
            pydub_play(audio_segment)

            # リセットフラグをチェック
            if reset_flag:
                print("Resetting...")
                continue  # ループの最初に戻る

            # Print timings
            print(f"Time taken for Whisper transcription: {whisper_time:.2f} seconds")
            print(f"Time taken for ChatGPT response: {chat_gpt_time:.2f} seconds")
            print(f"Time taken for ElevenLabs response: {elevenlabs_time:.2f} seconds")
            total_time = whisper_time + chat_gpt_time + elevenlabs_time
            print(f"Total Time for response: {total_time:.2f} seconds")
            print(" ")
            print(conversation[-1]['content'])

            print("\nReturning to waiting mode...\n")

if __name__ == "__main__":
    main_loop()
