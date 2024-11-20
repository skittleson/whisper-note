VENV_DIR = .venv
PYTHON = python
INSTALL_DEPS = pip install -r requirements.txt

default:
	@echo "must do something"

create-venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)

activate:
	@echo "Activating virtual environment..."
	. $(VENV_DIR)/bin/activate

install: create-venv
	@echo "Installing dependencies..."
	sudo apt install -y portaudio19-dev xclip ffmpeg
	$(INSTALL_DEPS)

portable: activate
	rm -rf build/
	rm -rf dist/
	pyinstaller index.py --onefile -n wnote
