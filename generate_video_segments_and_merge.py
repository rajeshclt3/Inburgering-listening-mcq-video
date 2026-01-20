import os
import re
import subprocess
from glob import glob

# ========= CONFIGURATION =========
import argparse
parser = argparse.ArgumentParser(description="Generate video segments and merge them for KNM pipeline.")
parser.add_argument("--data", default="/data", help="Base project folder containing audio/images.")
args = parser.parse_args()

BASE = args.data
AUDIO_DIR = os.path.join(BASE, "output_audio")
IMAGE_DIR = os.path.join(BASE, "output_images")
SOUNDS_DIR = os.path.join(BASE, "sounds")
SEGMENTS_DIR = os.path.join(BASE, "segments")
FINAL_DIR = os.path.join(BASE, "final_video")

os.makedirs(SEGMENTS_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

ANSWER_SOUND = os.path.join(SOUNDS_DIR, "answer.mp3")
SILENT_FALLBACK = os.path.join(SOUNDS_DIR, "silent.wav")

# ========= HELPERS =========
def log(msg):
    print(f"[DEBUG] {msg}")

def run_ffmpeg(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        log(f"FFmpeg Error:\n{result.stderr.decode(errors='ignore')}")
    return result.returncode == 0

def create_video_segment(image_path, audio_path, output_path):
    """Combine one image + one audio into a short mp4 segment."""
    log(f"Creating segment: {output_path}")
    cmd = (
        f'ffmpeg -y -loop 1 -i "{image_path}" -i "{audio_path}" '
        f'-c:v libx264 -tune stillimage -pix_fmt yuv420p '
        f'-shortest -vf "scale=1280:720" "{output_path}"'
    )
    run_ffmpeg(cmd)
    return output_path

# ========= MATCHING LOGIC =========
def match_images_and_audios():
    """Find matching image/audio pairs and define segment order."""
    pairs = []

    #  Intro section
    intro_img = os.path.join(IMAGE_DIR, "intro.png")
    intro_aud = os.path.join(AUDIO_DIR, "intro.wav")
    if os.path.exists(intro_img) and os.path.exists(intro_aud):
        pairs.append((intro_img, intro_aud, os.path.join(SEGMENTS_DIR, "00_intro.mp4")))
    else:
        log("Intro image or audio missing, skipping intro section.")

    # Other segments
    image_files = sorted(glob(os.path.join(IMAGE_DIR, "*.png")))
    log(f"[DEBUG] Found {len(image_files)} images, {len(os.listdir(AUDIO_DIR))} audios.")

    for img in image_files:
        name = os.path.basename(img)
        base = os.path.splitext(name)[0]
        audio_path = None

        # Case 1: main narration (script_XX)
        if re.match(r"script_\d{2}$", base):
            audio_path = os.path.join(AUDIO_DIR, f"{base}.wav")

        # Case 2: question slides (script_XX_qYY)
        elif re.match(r"script_\d{2}_q\d{2}$", base):
            audio_path = os.path.join(AUDIO_DIR, f"{base}.wav")

        # Case 3: scene narration (legacy _audio)
        elif "_audio" in base:
            audio_path = os.path.join(AUDIO_DIR, f"{base}.wav")

        # Case 4: answer slides → use global sound or silent fallback
        elif "answer" in base:
            answer_audio = ANSWER_SOUND
            if os.path.exists(answer_audio):
                log(f"[DEBUG] Using global answer sound for {img}")
                audio_path = answer_audio
            else:
                log(f"Global answer sound missing for {img}, generating silent fallback...")
                os.makedirs(SOUNDS_DIR, exist_ok=True)
                if not os.path.exists(SILENT_FALLBACK):
                    subprocess.run(
                        f'ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 1 "{SILENT_FALLBACK}" -y',
                        shell=True,
                        check=True
                    )
                audio_path = SILENT_FALLBACK

        # Skip unrecognized filenames
        else:
            continue

        if audio_path and os.path.exists(audio_path):
            seg_out = os.path.join(SEGMENTS_DIR, f"{base}.mp4")
            pairs.append((img, audio_path, seg_out))
        else:
            log(f"Missing audio for {img} → expected {audio_path}")

    return pairs

# ========= CONCATENATION =========
def concatenate_segments(segment_list, final_output):
    """Join all segments into one final video."""
    if not segment_list:
        log(" No video segments to concatenate.")
        return

    log("Concatenating all segments...")
    concat_file = os.path.join(SEGMENTS_DIR, "list.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for seg in segment_list:
            f.write(f"file '{os.path.abspath(seg)}'\n")

    cmd = (
        f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
        f'-c copy "{final_output}"'
    )
    run_ffmpeg(cmd)
    log(f"Final video created: {final_output}")

# ========= MAIN =========
if __name__ == "__main__":
    log("=== KNM Video Segment Generator & Merger (Final Docker Version) ===")

    pairs = match_images_and_audios()
    if not pairs:
        log("No valid image/audio pairs found. Check filenames.")
        exit(1)

    segment_paths = []
    for img, aud, outpath in pairs:
        try:
            segment_paths.append(create_video_segment(img, aud, outpath))
        except Exception as e:
            log(f"Error creating segment {outpath}: {e}")

    final_path = os.path.join(FINAL_DIR, "final_video_temp.mp4")
    concatenate_segments(segment_paths, final_path)

    log("All segments processed successfully! Proceed to normalization + final merge.")
