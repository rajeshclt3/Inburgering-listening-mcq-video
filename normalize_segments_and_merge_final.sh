#!/bin/bash
# ============================================================
#  KNM Listening Practice - Normalize (ordered) + Merge
#  - Preserves order from /data/segments/list.txt
#  - Adds *_answer.mp4 immediately after its base clip (once)
#  - Normalizes all audio/video to 44.1 kHz stereo AAC
#  - Outputs final video to /data/final_video/final_video.mp4
# ============================================================

set -euo pipefail

# ---- Paths (Docker mount) ----
PROJECT_DIR="/data"
SEGMENTS_DIR="${PROJECT_DIR}/segments"
NORMALIZED_DIR="${PROJECT_DIR}/segments_normalized"
FINAL_DIR="${PROJECT_DIR}/final_video"
LIST_FILE="${SEGMENTS_DIR}/list.txt"
FINAL_LIST="${NORMALIZED_DIR}/list.txt"
OUTPUT_FILE="${FINAL_DIR}/final_video.mp4"

mkdir -p "${NORMALIZED_DIR}" "${FINAL_DIR}"

if [ ! -f "${LIST_FILE}" ]; then
  echo "ERROR: ${LIST_FILE} not found. Run the Python segment builder first."
  exit 1
fi

echo " Step 1: Normalizing all segments (video + audio) in listed order..."
: > "${FINAL_LIST}"   # truncate/create

# Track already-added basenames to avoid duplicates
declare -A added_files

normalize_and_add() {
  local src="$1"
  [ ! -f "$src" ] && return

  local base
  base="$(basename "$src")"
  local out="${NORMALIZED_DIR}/${base}"

  # prevent duplicates by basename
  if [[ -n "${added_files[$base]:-}" ]]; then
    echo " Skipping duplicate: $base"
    return
  fi
  added_files["$base"]=1

  echo " Normalizing: $base"
  ffmpeg -y -i "$src" \
    -c:v libx264 -preset veryfast -crf 20 \
    -c:a aac -b:a 192k -ar 44100 -ac 2 \
    -movflags +faststart "$out" < /dev/null

  # Append absolute path to concat list
  echo "file '$(realpath "$out")'" >> "${FINAL_LIST}"
}

# --- Normalize in the same order as list.txt ---
while IFS= read -r line; do
  [[ -z "$line" || "$line" != file* ]] && continue
  # Extract path between single quotes
  file_path="$(printf '%s\n' "$line" | sed -E "s/file '([^']+)'/\1/")"

  # 1) Add the main clip
  normalize_and_add "$file_path"

  # 2) If a sibling *_answer.mp4 exists, add it right after
  answer_path="${file_path%.*}_answer.mp4"
  if [ -f "$answer_path" ]; then
    normalize_and_add "$answer_path"
  fi
done < "${LIST_FILE}"

# --- Safety pass: include any *_answer.mp4 in SEGMENTS_DIR not yet added ---
for extra in "${SEGMENTS_DIR}"/*_answer.mp4; do
  [ -f "$extra" ] || continue
  base_extra="$(basename "$extra")"
  if [[ -z "${added_files[$base_extra]:-}" ]]; then
    normalize_and_add "$extra"
  fi
done

echo " Normalization complete."
echo " Normalized list written to: ${FINAL_LIST}"
echo "------------------------------------------------------------"

echo " Step 2: Merging normalized clips..."
ffmpeg -y -f concat -safe 0 -i "${FINAL_LIST}" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a aac -b:a 192k -ar 44100 -ac 2 \
  -movflags +faststart "${OUTPUT_FILE}"

echo "------------------------------------------------------------"
if [ -f "${OUTPUT_FILE}" ]; then
  echo "Merge complete!"
  echo "Final video: ${OUTPUT_FILE}"
else
  echo " Merge failed — check FFmpeg logs above."
  exit 1
fi

