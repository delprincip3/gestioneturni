#!/usr/bin/env bash
# exit on error
set -o errexit

# Installa le dipendenze Python
pip install -r requirements.txt

# Installa le dipendenze npm e compila il CSS
npm install
npm run build

# Esegui le migrazioni del database
flask db upgrade 