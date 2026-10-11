#!/usr/bin/env bash
# Regenera los notebooks de ejemplo desde build/ y los ejecuta para verificarlos.
set -e
cd "$(dirname "$0")"
python build/nb_l01.py
python build/nb_l05.py
python build/nb_l07.py
python build/nb_l10.py
python build/nb_l14.py
python build/nb_l21.py
echo
python ejecutar_notebooks.py
