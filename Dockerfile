# ============================================================
#   KNM Listening Practice – Clean Separation Dockerfile
# ============================================================

FROM python:3.11-slim

# ---- 1️⃣  Install dependencies ----
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ---- 2️⃣  Copy scripts into the image ----
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python & Bash scripts into /app
COPY . /app/

# ---- 3️⃣  Prepare runtime data mount point ----
RUN mkdir -p /data
VOLUME ["/data"]

# ---- 4️⃣  Environment defaults ----
ENV PYTHONUNBUFFERED=1
ENV AZURE_SPEECH_KEY=""
ENV AZURE_SPEECH_REGION="westeurope"
ENV VOICE_MALE="nl-NL-MaartenNeural"
ENV VOICE_FEMALE="nl-NL-ColetteNeural"
ENV SPEECH_RATE="0%"

# ---- 5️⃣  Default working directory ----
WORKDIR /app

# ---- 6️⃣  Default command ----
CMD ["bash"]

COPY entrypoint.sh /app/entrypoint.sh
COPY normalize_segments_and_merge_final.sh /app/normalize_segments_and_merge_final.sh
RUN chmod +x /app/entrypoint.sh /app/normalize_segments_and_merge_final.sh

ENTRYPOINT ["/app/entrypoint.sh"]


