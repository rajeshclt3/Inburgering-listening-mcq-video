import os
import argparse
from PIL import Image, ImageDraw, ImageFont
import azure.cognitiveservices.speech as speechsdk

# ========= CLI ARGUMENTS =========
parser = argparse.ArgumentParser(description="Generate intro image and audio for KNM video.")
parser.add_argument("--input", default="/data/intro.txt", help="Path to intro text file")
parser.add_argument("--output", default="/data/output_audio", help="Output directory for audio")
parser.add_argument("--scenes", default="/data/scenes", help="Path to scenes folder")
parser.add_argument("--voice", default="en-GB-SoniaNeural", help="Voice for TTS")
args = parser.parse_args()

# ========= PATHS =========
INTRO_FILE = args.input
AUDIO_OUT_DIR = args.output
IMAGE_OUT_DIR = "/data/output_images"
SCENE_IMG_PATH = os.path.join(args.scenes, "intro.png")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

os.makedirs(AUDIO_OUT_DIR, exist_ok=True)
os.makedirs(IMAGE_OUT_DIR, exist_ok=True)

# ========= AZURE SPEECH CONFIG =========
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "westeurope")

def log(msg): 
    print(f"[DEBUG] {msg}")

# ========= DRAW HELPERS =========
def draw_full_border(draw, canvas_size=(1100, 600)):
    draw.rectangle([(0, 0), (canvas_size[0]-1, canvas_size[1]-1)],
                   outline=(255,165,0), width=5)

# ========= IMAGE GENERATION =========
def generate_intro_image(intro_text, out_path, scene_path):
    log(f"Generating intro image: {out_path}")
    base = Image.new("RGB", (1100, 600), (255, 255, 255))
    draw = ImageDraw.Draw(base)
    font_title = ImageFont.truetype(FONT_PATH, 48)
    font_sub = ImageFont.truetype(FONT_PATH, 28)

    # Title
    draw.text((60, 20), "Listening Practice", fill=(0,0,0), font=font_title)
    draw.text((60, 80), "Welcome to this listening exercise", fill=(0,0,0), font=font_sub)

    # Scene image below heading
    if os.path.exists(scene_path):
        scene = Image.open(scene_path).convert("RGB")
        scene_width = 600
        ratio = scene_width / scene.width
        scene_height = int(scene.height * ratio)
        scene = scene.resize((scene_width, scene_height))
        x = (1100 - scene_width) // 2
        y = 140
        base.paste(scene, (x, y))
    else:
        draw.rectangle((100, 180, 700, 400), fill=(230,230,230))
        draw.text((120, 280), "Intro image missing", fill=(80,0,0), font=font_sub)

    draw_full_border(draw)
    base.save(out_path)
    log("Intro image created successfully!")

# ========= AUDIO GENERATION =========
def generate_intro_audio(text, out_path, voice):
    if not SPEECH_KEY or not SPEECH_REGION:
        raise EnvironmentError("Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION")

    log(f"Generating intro audio: {out_path}")
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = voice
    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text_async(text).get()
    log("Intro audio generated successfully!")

# ========= MAIN =========
if __name__ == "__main__":
    log("=== Intro Media Generator (Docker-Compatible) ===")

    if not os.path.exists(INTRO_FILE):
        raise FileNotFoundError(f"Intro file not found: {INTRO_FILE}")

    with open(INTRO_FILE, "r", encoding="utf-8") as f:
        intro_text = f.read().strip()

    intro_image_path = os.path.join(IMAGE_OUT_DIR, "intro.png")
    intro_audio_path = os.path.join(AUDIO_OUT_DIR, "intro.wav")

    generate_intro_image(intro_text, intro_image_path, SCENE_IMG_PATH)
    generate_intro_audio(intro_text, intro_audio_path, args.voice)

    log("All intro assets (image + audio) created successfully!")
