#!/bin/bash

echo "Starting Streamlit..."

pkill -f streamlit || true

streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.enableCORS false \
  --server.enableXsrfProtection false