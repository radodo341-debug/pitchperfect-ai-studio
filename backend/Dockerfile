FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TDEED_DIR=/opt/T-DEED

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ffmpeg libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch keeps the image from pulling CUDA libraries.
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
    torch==2.3.1 torchvision==0.18.1

RUN pip install \
    fastapi==0.115.12 \
    "uvicorn[standard]==0.34.0" \
    python-multipart==0.0.20 \
    opencv-python-headless==4.10.0.84 \
    timm==1.0.3 \
    matplotlib==3.9.0 \
    SoccerNet \
    wandb==0.17.4

RUN git clone --depth 1 https://github.com/arturxe2/T-DEED.git /opt/T-DEED

COPY main.py /app/main.py
WORKDIR /app
EXPOSE 8000
CMD ["python", "main.py"]
