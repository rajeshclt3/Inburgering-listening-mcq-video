import os, argparse
import re
import time
import azure.cognitiveservices.speech as speechsdk

# =============================
# CONFIGURATION
# =============================
parser = argparse.ArgumentParser()
parser.add_argument("--input", default="/data/input.txt", help="Path to input file")
parser.add_argument("--output", default="/data/output_audio", help="Directory to save audio")
args = parser.parse_args()

INPUT_FILE = args.input
OUTPUT_DIR = args.output

VOICE_MALE = "nl-NL-MaartenNeural"    # Dutch male voice
VOICE_FEMALE = "nl-NL-ColetteNeural"  # Dutch female voice
SPEECH_RATE = "0%"                    # can adjust to "-10%" if slower needed
TARGET_SCRIPT_DURATION = 60           # seconds (optional target)

# =============================
# AZURE SETUP
# =============================

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

def get_speech_synthesizer(voice_name):
    """Returns a speech config for the given voice."""
    if not SPEECH_KEY or not SPEECH_REGION:
        raise EnvironmentError("Please set Azure Speech credentials.")

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = voice_name
    return speech_config


def synthesize_text_to_file(text, output_path, voice_name):
    """Generate audio file from text using Azure TTS with the selected voice."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    speech_config = get_speech_synthesizer(voice_name)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Build SSML string with rate and prosody
    text_ssml = f"""
    <speak version='1.0' xml:lang='nl-NL'>
        <voice name='{voice_name}'>
            <prosody rate='{SPEECH_RATE}'>{text}</prosody>
        </voice>
    </speak>
    """

    print(f"Generating with {voice_name}: {output_path}")
    result = synthesizer.speak_ssml_async(text_ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Audio saved: {output_path}")
    else:
        print(f"Error generating {output_path}: {result.reason}")


# =============================
# PARSER LOGIC
# =============================

def parse_input_file(filename):
    """Parses input.txt and returns a structured dictionary."""
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    audio_blocks = re.findall(r"### AUDIO_SCRIPT_(\d+) ###(.*?)### QUESTIONS_\1 ###", content, re.S)
    data = []

    for idx, (script_id, block) in enumerate(audio_blocks, 1):
        questions_block_match = re.search(rf"### QUESTIONS_{script_id} ###(.*?)(?=(### AUDIO_SCRIPT_|$))", content, re.S)
        questions_block = questions_block_match.group(1).strip() if questions_block_match else ""

        question_matches = re.findall(
            r"Q\d+:\s*(.*?)\nA\.\s*(.*?)\nB\.\s*(.*?)\nC\.\s*(.*?)\nANSWER:\s*([A-C])",
            questions_block, re.S
        )

        questions = []
        for i, q in enumerate(question_matches, 1):
            questions.append({
                "id": i,
                "q": q[0].strip(),
                "A": q[1].strip(),
                "B": q[2].strip(),
                "C": q[3].strip(),
                "answer": q[4].strip(),
            })

        data.append({
            "script_id": int(script_id),
            "audio_text": block.strip(),
            "questions": questions
        })
    return data


# =============================
# AUDIO GENERATION
# =============================

def main():
    sections = parse_input_file(INPUT_FILE)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for section in sections:
        sid = section["script_id"]

        # === Audio Script (Male Voice) ===
        script_path = os.path.join(OUTPUT_DIR, f"script_{sid:02d}.wav")
        synthesize_text_to_file(section["audio_text"], script_path, VOICE_MALE)

        # === Questions (Female Voice) ===
        for q in section["questions"]:
            q_text = f"{q['q']} Optie A: {q['A']}. Optie B: {q['B']}. Optie C: {q['C']}."
            q_path = os.path.join(OUTPUT_DIR, f"script_{sid:02d}_q{q['id']:02d}.wav")
            synthesize_text_to_file(q_text, q_path, VOICE_FEMALE)

        print(f"Finished Script {sid}\n{'-'*60}")
        time.sleep(2)  # small delay to avoid API rate limits


if __name__ == "__main__":
    main()
