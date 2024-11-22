"""Whisper app for taking notes through dictation via the cli."""

import sys
import readline
from rich.console import Console
from rich.prompt import Confirm
import pyperclip
from transcribe_utils import RecognizerLive


console = Console()
r = RecognizerLive()
r.callback_phrase = console.print


def console_warm_session():
    """Keep models warmed up"""

    console_user_experience()
    if Confirm.ask("Start new session?"):
        console_warm_session()
    sys.exit(0)


def console_user_experience():
    """Primary user experience for taking notes"""

    console.clear()
    note = ""
    while True:
        console.print("Speak until CTRL+C.")
        user_content = r.run()
        console.clear()
        try:
            console.print(note, style="dim")
            console.print("ENTER to accept. CTRL+C to exit.")
            readline.set_startup_hook(lambda: readline.insert_text(user_content))
            note = note + " " + console.input()
            console.clear()
            console.print(note, style="dim")
        except KeyboardInterrupt:
            break
    pyperclip.copy(note)
    console.print("saved to clipboard!")


if __name__ == "__main__":
    console_warm_session()
