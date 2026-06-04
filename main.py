#!/usr/bin/env python3
"""
ScaleCut — entry point.

Usage:
    python main.py              # wizard paso a paso
    python main.py quick ...    # crear proyecto sin wizard
    python main.py templates    # listar plantillas
    python main.py version      # ver versión

If you see 'ModuleNotFoundError', activate the virtual environment first:
    source .venv/bin/activate
Or use the launcher script that handles it automatically:
    bash run.sh
"""

import sys

try:
    from scalecut.cli import main
except ModuleNotFoundError as e:
    print(f"\n  Error: dependencia faltante — {e}")
    print("  El venv no está activado o las dependencias no están instaladas.")
    print("\n  Opciones:")
    print("    1. Usa el launcher:    bash run.sh")
    print("    2. Activa el venv:     source .venv/bin/activate")
    print("       Y luego:            python main.py\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
