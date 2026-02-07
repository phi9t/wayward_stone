FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.cache/huggingface \
    HUGGINGFACE_HUB_CACHE=/root/.cache/huggingface/hub

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    sox \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -U pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.6.0 torchaudio==2.6.0 \
    && pip install -r /app/requirements.txt
COPY qwen3_tts_audiobook.py /app/qwen3_tts_audiobook.py

ENTRYPOINT ["python", "/app/qwen3_tts_audiobook.py"]
