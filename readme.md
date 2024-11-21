# Whisper Note

Near realtime text transcription with Whisper note taking app with editing. 

## ToDos

- [ ] Keep cli running but pause capture of audio. This keeps the models in memory
- [ ] Presenting all the captures of text in a list mode could be useful.
- [ ] ollama for cleaning up text.

## Virtual env

create a virtual `python -m venv .venv`

then activate it `source .venv/bin/activate`

update all packates `pip install -r requirements.txt`

## Portable
`pyinstaller index.py -n wnote`