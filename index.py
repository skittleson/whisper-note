"""Whisper app for taking notes through dictation via the cli."""

import sys
import logging
import readline
from queue import Queue
from threading import Thread
import sounddevice
import speech_recognition as sr
import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment
from rich.console import Console
import pyperclip

MODEL_SIZE = "small.en"
logging.getLogger(sounddevice.__name__).setLevel(logging.CRITICAL)
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
console = Console()
r = sr.Recognizer()
audio_queue = Queue()
text_queue = Queue()

@staticmethod
def audio_to_file_object(audio: sr.AudioData):
    """Converts audio stream into object for whisper"""

    audio_segment = AudioSegment(
        data=audio.get_raw_data(),
        sample_width=audio.sample_width,
        frame_rate=audio.sample_rate,
        channels=1)

    # convert to expected format
    if audio_segment.frame_rate != 16000: # 16 kHz
        audio_segment = audio_segment.set_frame_rate(16000)
    if audio_segment.sample_width != 2:   # int16
        audio_segment = audio_segment.set_sample_width(2)
    if audio_segment.channels != 1:       # mono
        audio_segment = audio_segment.set_channels(1)        
    arr = np.array(audio_segment.get_array_of_samples())
    arr = arr.astype(np.float32)/32768.0
    return arr

def recognize_worker():
    """background worker to process text in real time"""

    while True:
        audio = audio_queue.get()  # retrieve the next audio processing job from the main thread
        if audio is None:
            break  # stop processing if the main thread is done

        # received audio data, now we'll recognize it
        try:
            segments, _ = model.transcribe(audio_to_file_object(audio),
                        beam_size=5,
                        word_timestamps=False,
                        vad_filter=True)
            segments = list(segments)
            content = (''.join(segment.text for segment in segments)).strip()
            if len(content) < 1:
                continue
            text_queue.put(content)
            console.print(content)
        except sr.UnknownValueError:
            console.print("could not understand audio")
        audio_queue.task_done()  # mark the audio processing job as completed in the queue

def audio_thread_listen():
    """blocking listening thread"""
    
    # start a new thread to recognize audio, while this thread focuses on listening
    recognize_thread = Thread(target=recognize_worker)
    recognize_thread.daemon = True
    recognize_thread.start()
    with sr.Microphone() as source:
        try:
            while True:  # repeatedly listen for phrases and put the resulting audio on the audio processing job queue
                audio_queue.put(r.listen(source, phrase_time_limit=None))
                # press any key
        except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
            pass

    audio_queue.put(None)
    recognize_thread.join()  # wait for the recognize_thread to actually stop
    final_content = ''
    while text_queue.empty() is not True:
        final_content = final_content + ' ' + text_queue.get()
    return final_content

def console_user_experience():
    """Primary user experience for taking notes"""

    console.print('Keep speaking until CTRL+C happens then edit the sentence.')
    note = ''
    while True:
        user_content = audio_thread_listen()
        console.clear()
        try:
            console.print(note, style="dim")
            readline.set_startup_hook(lambda: readline.insert_text(user_content))
            note = note + ' ' + console.input()
            console.clear()
            console.print(note, style="dim")
        except KeyboardInterrupt:
            break
    pyperclip.copy(note)
    console.print('saved')

if __name__ == '__main__':
    console_user_experience()
    sys.exit(0)
