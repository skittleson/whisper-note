"""Whisper app for taking notes through dictation via the cli."""

import sys
import readline
from rich.console import Console
import pyperclip
from transcribe_utils import RecognizerLive


def console_user_experience():
    """Primary user experience for taking notes"""

    console = Console()
    console.clear()
    r = RecognizerLive()
    r.callback_phrase = console.print
    note = ""
    while True:
        console.print("Keep speaking until CTRL+C happens.")
        user_content = r.run()
        console.clear()
        try:
            console.print(note, style="dim")
            console.print("Edit until CTRL+C happens.")
            readline.set_startup_hook(lambda: readline.insert_text(user_content))
            note = note + " " + console.input()
            console.clear()
            console.print(note, style="dim")
        except KeyboardInterrupt:
            break
    pyperclip.copy(note)
    console.print("saved to clipboard")


if __name__ == "__main__":
    console_user_experience()
    sys.exit(0)
