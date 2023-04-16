'''
Function introduction:
1. Microphone will receive the wake word GPT(def get_wake_word(phrase))
2. Use the one of the models of ChatGPT to response the answers(def synthesize_speech(input, output))
3. Use the Microphone to play the response as a speech(def play)
'''
import os
import openai
import pydub
import asyncio
import speech_recognition as sr
from pydub import playback
from google.cloud import texttospeech

openai.api_key = "your api key"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "your application address"

r = sr.Recognizer()
WAKE_WORD = "gpt"

# Define a function to get the wake word


def get_wake_word(phrase):
    if WAKE_WORD in phrase.lower():
        return WAKE_WORD
    else:
        return None

# Define a function to synthesize the speech


def synthesize_speech(text, output_filename):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice,
                 "audio_config": audio_config}
    )
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)

# Define a function to play the audio


def play_audio(file):
    sound = pydub.AudioSegment.from_file(file, format="mp3")
    playback.play(sound)

# Define the main function


async def main():
    while True:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            print("Waiting for a wake word 'ok gpt'")
            while True:
                audio = r.listen(source)
                try:
                    with open("aud.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    audio_file = open("aud.wav", "rb")
                    transcript = openai.Audio.transcribe(
                        "whisper-1", audio_file)
                    phrase = transcript["text"]
                    print(f"You said: {phrase}")

                    wake_word = get_wake_word(phrase)
                    if wake_word is not None:
                        break
                    else:
                        print("Not a wake word, try again.")

                except Exception as e:
                    print("Error transcribing audio: {0}".format(e))
                    continue

            print("Speak a prompt...")
            synthesize_speech("How can I help you?", "res.mp3")
            play_audio("res.mp3")
            audio = r.listen(source)

            try:
                with open("aud_prompt.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                audio_prompt_file = open("aud_prompt.wav", "rb")
                transcript = openai.Audio.transcribe(
                    "whisper-1", audio_prompt_file)
                user_input = transcript["text"]
                print(f"You said: {user_input}")
            except Exception as e:
                print("Error transcribing audio: {0}".format(e))
                continue

            if wake_word == WAKE_WORD:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.5,
                    max_tokens=500,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    n=1,
                    stop=["\nUser:"],
                )

                bot_response = response["choices"][0]["message"]["content"]

        print("Bot's response: ", bot_response)
        synthesize_speech(bot_response, "res.mp3")
        play_audio("res.mp3")

if __name__ == "__main__":
    asyncio.run(main())
