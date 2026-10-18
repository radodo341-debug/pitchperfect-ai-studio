FROM python:3.11.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TDEED_DIR=/opt/T-DEED \
    TDEED_CHECKPOINT_PATH=/models/SoccerNetBall_challenge1/checkpoint_best.pt \
    PP_TRACKER_MODEL=/models/yolo-person.pt

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ffmpeg libglib2.0-0 libgl1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip==25.1.1 \
    && python -m pip install --index-url https://download.pytorch.org/whl/cpu \
       torch==2.3.1 torchvision==0.18.1 \
    && python -m pip install -r /app/requirements.txt

# Pin upstream T-DEED to a reviewed immutable commit instead of cloning a moving branch.
ARG TDEED_COMMIT=d953b4de8a2ad941c565e1683c5b07255cbe644e
RUN git init /opt/T-DEED \
    && git -C /opt/T-DEED remote add origin https://github.com/arturxe2/T-DEED.git \
    && git -C /opt/T-DEED fetch --depth 1 origin "${TDEED_COMMIT}" \
    && git -C /opt/T-DEED checkout --detach FETCH_HEAD \
    && mkdir -p /models/SoccerNetBall_challenge1 \
    && python -c "import subprocess; print('Pinned T-DEED revision:', subprocess.check_output(['git','-C','/opt/T-DEED','rev-parse','HEAD'], text=True).strip())" \
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
