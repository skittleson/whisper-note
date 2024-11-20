VENV_DIR = .venv
PYTHON = python
ACTIVATE = source $(VENV_DIR)/bin/activate
INSTALL_DEPS = pip install -r requirements.txt

create-venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)

activate-venv:
	@echo "Activating virtual environment..."
	@$(ACTIVATE)

install-deps: create-venv
	@echo "Installing dependencies..."
	sudo apt install -y portaudio19-dev xclip
	$(INSTALL_DEPS)

# Default target
all: check-venv

check-venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Installing dependencies..."; \
		$(MAKE) install-deps; \
	else \
		echo "Virtual environment found. Skipping dependency installation."; \
	fi
	@echo "Setup complete. Virtual environment is ready."
