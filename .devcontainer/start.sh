#!/bin/bash

echo "Starting Streamlit..."

pkill -f streamlit || true

cd /workspaces/WIMS-Converter

streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.enableCORS false \
  --server.enableXsrfProtection false