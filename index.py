"""Whisper app for taking notes through dictation via the cli."""

import sys
import logging
import readline
import sounddevice
import speech_recognition as sr
import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment
from rich.console import Console
import pyperclip
logging.getLogger(sounddevice.__name__).setLevel(logging.CRITICAL)
MODEL_SIZE = "tiny.en"

console = Console()
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

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

def main_audio() -> str:
    """Take a note down using my voice"""

    console.print('Start taking your note.')
    r = sr.Recognizer()
    running = True
    running_pharses = []
    while running:
        try:
            with sr.Microphone(sample_rate=16000) as source:
                audio = r.listen(source, timeout=45)
            if audio is None:
                continue
            segments, _ = model.transcribe(audio_to_file_object(audio),
                                        beam_size=5,
                                        word_timestamps=False,
                                        vad_filter=True)
            segments = list(segments)
            content = (''.join(segment.text for segment in segments)).strip()
            if len(content) < 1:
                continue
            readline.set_startup_hook(lambda: readline.insert_text(content))
            user_content = console.input()
            running_pharses.append(user_content)
            console.clear()
        except KeyboardInterrupt:
            running = False
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            console.print(".")

    # alter combined strings
    console.clear()
    note = ' '.join(phrase for phrase in running_pharses)
    readline.set_startup_hook(lambda: readline.insert_text(note))
    note_content = console.input()

    # save it to the clipboard and leave
    console.clear()
    pyperclip.copy(note_content)
    console.print('saved')
    sys.exit(0)

if __name__ == '__main__':
    main_audio()
