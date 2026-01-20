import os
import re
import time
import azure.cognitiveservices.speech as speechsdk

# =============================
# CONFIGURATION
# =============================

INPUT_FILE = "input.txt"
OUTPUT_DIR = "output_audio"
VOICE_NAME = "nl-NL-ColetteNeural"  # Dutch female voice
SPEECH_RATE = "0%"  # can adjust to "-10%" if you want slower voice
TARGET_SCRIPT_DURATION = 60  # seconds

# =============================
# AZURE SETUP
# =============================

def get_speech_synthesizer():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_SPEECH_REGION")

    if not speech_key or not service_region:
        raise EnvironmentError("Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables.")

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_synthesis_voice_name = VOICE_NAME
    return speech_config


def synthesize_text_to_file(text, output_path, speech_config):
    """Generate audio file from text using Azure TTS."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

    # Apply speech synthesis settings
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    text_ssml = f"""
    <speak version='1.0' xml:lang='nl-NL'>
        <voice name='{VOICE_NAME}'>
            <prosody rate='{SPEECH_RATE}'>{text}</prosody>
        </voice>
    </speak>
    """

    print(f"Generating audio: {output_path}")
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

    # Find all audio scripts
    audio_blocks = re.findall(r"### AUDIO_SCRIPT_(\d+) ###(.*?)### QUESTIONS_\1 ###", content, re.S)
    data = []

    for idx, (script_id, block) in enumerate(audio_blocks, 1):
        questions_block_match = re.search(rf"### QUESTIONS_{script_id} ###(.*?)(?=(### AUDIO_SCRIPT_|$))", content, re.S)
        questions_block = questions_block_match.group(1).strip() if questions_block_match else ""

        # Parse questions
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
    speech_config = get_speech_synthesizer()
    sections = parse_input_file(INPUT_FILE)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for section in sections:
        sid = section["script_id"]

        # === Audio Script ===
        script_path = os.path.join(OUTPUT_DIR, f"script_{sid:02d}.wav")
        synthesize_text_to_file(section["audio_text"], script_path, speech_config)

        # === Questions ===
        for q in section["questions"]:
            q_text = f"{q['q']} Optie A: {q['A']}. Optie B: {q['B']}. Optie C: {q['C']}."
            q_path = os.path.join(OUTPUT_DIR, f"script_{sid:02d}_q{q['id']:02d}.wav")
            synthesize_text_to_file(q_text, q_path, speech_config)

        print(f"Finished Script {sid}\n{'-'*50}")
        time.sleep(2)  # avoid hitting Azure API too quickly


if __name__ == "__main__":
    main()
