#!/bin/bash
# ============================================================
#  KNM Listening Practice – Automated Full Pipeline Entrypoint
#  Generates audio, images, segments
#   Normalizes & merges all clips automatically
#   Saves final video to /data/final_video/
# ============================================================

set -euo pipefail

echo "KNM Video Generation Pipeline Started"

# ----  Check input mount ----
if [ ! -d "/data" ]; then
  echo " ERROR: /data directory not mounted."
  echo "   Use: -v \$(pwd):/data"
  exit 1
fi

if [ ! -f "/data/input.txt" ]; then
  echo " ERROR: /data/input.txt not found."
  echo "   Place your input.txt inside your mounted project folder."
  exit 1
fi

# ----   Prepare directories ----
mkdir -p /data/output_audio /data/output_images /data/segments /data/final_video /data/scenes /data/sounds
echo " Output directories prepared."

# ----  Run generation stages ----
echo "  Step 1: Generating intro..."
python3 /app/generate_intro.py --input /data/input.txt --output /data/output_audio

echo " Step 2: Generating audio segments..."
python3 /app/generate_audio_segments_multi_voice.py --input /data/input.txt --output /data/output_audio

echo "  Step 3: Creating question images..."
python3 /app/generate_question_images.py --input /data/input.txt --output /data/output_images

echo "  Step 4: Creating video segments..."
python3 /app/generate_video_segments_and_merge.py --data /data

# ----  Normalize & merge final video ----
echo " Step 5: Normalizing and merging final video..."
bash /app/normalize_segments_and_merge_final.sh

# ----  Completion message ----
echo "------------------------------------------------------------"
echo " All stages completed successfully!"
echo " Final video available at: /data/final_video/final_video.mp4"
echo "------------------------------------------------------------"

