import speech_recognition as sr
import os
from notion import post_notion

r = sr.Recognizer()

directory = os.fsencode("clips/atomichabits/")

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".flac") or filename.endswith(".py"):
        print(os.path.join(os.fsdecode(directory), filename))
        heading = filename.replace(".flac", "")

        audioclip = sr.AudioFile(f'clips/{filename}')
        with audioclip as source:
            audio = r.record(source)

        post_notion(heading, r.recognize_google(audio))

    else:
        continue
