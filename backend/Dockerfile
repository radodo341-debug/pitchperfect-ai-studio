FROM python:3.11.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TDEED_DIR=/opt/T-DEED \
    PP_TRACKER_MODEL=/models/yolo-person.pt

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ffmpeg libglib2.0-0 libgl1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip==25.1.1 \
    && python -m pip install --index-url https://download.pytorch.org/whl/cpu \
       torch==2.3.1 torchvision==0.18.1 \
    && python -m pip install -r /app/requirements.txt

COPY patch_tdeed.py /app/patch_tdeed.py
RUN git clone --depth 1 https://github.com/arturxe2/T-DEED.git /opt/T-DEED \
    && mkdir -p /opt/T-DEED/checkpoints/SoccerNetBall/SoccerNetBall_challenge1 \
    && python /app/patch_tdeed.py

COPY main.py player_tracking.py /app/
COPY tests /app/tests
COPY start.sh /app/start.sh
RUN mkdir -p /models /data
WORKDIR /app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1
CMD ["sh", "/app/start.sh"]
