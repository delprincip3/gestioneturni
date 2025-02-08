#!/usr/bin/env bash
# exit on error
set -o errexit

# Installa le dipendenze Python
pip install -r requirements.txt

# Installa le dipendenze npm e compila il CSS
npm install
npm run build

# Crea la directory src/style se non esiste
mkdir -p src/style

# Compila il CSS di nuovo per sicurezza
npx tailwindcss -i ./src/style/input.css -o ./src/style/output.css

# Esegui le migrazioni del database
flask db upgrade 