#!/bin/bash
# Script de démarrage pour Render
uvicorn api.main:app --host 0.0.0.0 --port $PORT
