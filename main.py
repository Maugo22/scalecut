#!/usr/bin/env python3
"""
ScaleCut — entry point.

Usage:
    python main.py              # wizard paso a paso
    python main.py quick ...    # crear proyecto sin wizard
    python main.py templates    # listar plantillas
    python main.py version      # ver versión
"""
from scalecut.cli import main

if __name__ == "__main__":
    main()
