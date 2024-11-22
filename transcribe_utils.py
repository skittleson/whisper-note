"""Transcribe utils built on prexisting solutions"""

import logging
from threading import Thread
import os
import io
import wave
from queue import Queue
import sounddevice
import speech_recognition as sr
from faster_whisper import WhisperModel

logging.getLogger(sounddevice.__name__).setLevel(logging.CRITICAL)


class RecognizerLive:
    """Transcribe incoming audio chunks to text"""

    def __init__(self) -> None:
        # device = "gpu" if torch.cuda.is_available() else "gpu"
        # print(device)
        self._model = WhisperModel("small.en", device="cpu", compute_type="int8")
        self._recognizer = sr.Recognizer()
        self._audio_queue = Queue()
        self._text_queue = Queue()
        self.callback_phrase = None

    def _record_audio_disk(self, audio: sr.AudioData, output_file: str):
        """Creates and/or appends audio chunks to disk"""

        if os.path.exists(output_file):
            data = []
            w = wave.open(output_file, "rb")
            data.append([w.getparams(), w.readframes(w.getnframes())])
            w.close()

            ww = wave.open(io.BytesIO(audio.get_wav_data()), "rb")
            data.append([ww.getparams(), ww.readframes(ww.getnframes())])
            ww.close()

            output = wave.open(output_file, "wb")
            output.setparams(data[0][0])
            output.writeframes(data[0][1])
            output.writeframes(data[1][1])
            output.close()

        else:
            with open(output_file, "wb") as f:
                f.write(audio.get_wav_data())
        

    def transcribe(self, audio_file):
        """Transcribe audio like file"""

        segments, _ = self._model.transcribe(
            audio_file,
            beam_size=5,
            word_timestamps=False,
            vad_filter=True,
        )
        segments = list(segments)
        content = ("".join(segment.text for segment in segments)).strip()
        return content

    def _recognize_worker(self):
        while True:
            audio : sr.AudioData = self._audio_queue.get()
            if audio is None:
                break  # stop processing if the main thread is done

            # received audio data, now we'll recognize it
            try:
                audio_bytes = io.BytesIO(audio.get_wav_data())
                content = self.transcribe(audio_bytes)
                if len(content) < 1:
                    continue
                self._text_queue.put(content)
                if self.callback_phrase is not None:
                    self.callback_phrase(content)
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
                    # repeatedly listen for phrases then put the resulting audio on the audio job queue
                    self._audio_queue.put(
                        self._recognizer.listen(source, phrase_time_limit=None)
                    )
            except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
                pass

        self._audio_queue.put(None)
        recognize_thread.join()  # wait for the recognize_thread to actually stop
        final_content = ""
        while self._text_queue.empty() is not True:
            final_content = final_content + " " + self._text_queue.get()
        return final_content

    def run(self):
        """run instance"""

        return self._audio_thread_listen()
