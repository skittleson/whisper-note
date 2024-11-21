"""Transcribe utils built on prexisting solutions"""

import logging
from threading import Thread
from queue import Queue
import sounddevice
import speech_recognition as sr
import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment
logging.getLogger(sounddevice.__name__).setLevel(logging.CRITICAL)

class TranscribeLive:
    """Transcribe incoming audio chunks to text"""

    def __init__(self) -> None:
        self._model = WhisperModel("small.en", device="cpu", compute_type="int8")
        self._recognizer = sr.Recognizer()
        self._audio_queue = Queue()
        self._text_queue = Queue()

    def _audio_to_file_object(self, audio: sr.AudioData):
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

    def _recognize_worker(self):
        while True:
            audio = self._audio_queue.get()
            if audio is None:
                break  # stop processing if the main thread is done

            # received audio data, now we'll recognize it
            try:
                segments, _ = self._model.transcribe(self._audio_to_file_object(audio),
                            beam_size=5,
                            word_timestamps=False,
                            vad_filter=True)
                segments = list(segments)
                content = (''.join(segment.text for segment in segments)).strip()
                if len(content) < 1:
                    continue
                self._text_queue.put(content)
                # console.print(content)
            except sr.UnknownValueError:
                print("could not understand audio")
            self._audio_queue.task_done()  # mark the audio processing job as completed in the queue

    def _audio_thread_listen(self):
        # start a new thread to recognize audio, while this thread focuses on listening
        recognize_thread = Thread(target=self._recognize_worker)
        recognize_thread.daemon = True
        recognize_thread.start()
        with sr.Microphone() as source:
            try:
                while True:
                    # repeatedly listen for phrases and put the resulting audio on the audio processing job queue
                    self._audio_queue.put(self._recognizer.listen(source, phrase_time_limit=None))
            except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
                pass

        self._audio_queue.put(None)
        recognize_thread.join()  # wait for the recognize_thread to actually stop
        final_content = ''
        while self._text_queue.empty() is not True:
            final_content = final_content + ' ' + self._text_queue.get()
        return final_content
    
    def run(self):
        """test"""

        print('placeholder')