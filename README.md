# Inburgering Listening Practice - Automated Video Pipeline

An automated end-to-end pipeline designed to generate Dutch **KNM (Kennis van de Nederlandse Maatschappij)** listening practice videos. This tool transforms a simple text file containing scripts and multiple-choice questions into a fully merged, normalized, and high-quality MP4 video.

## Key Features

* **TTS Integration:** Uses Azure Cognitive Services (Neural Voices) to generate high-quality Dutch audio.
* **Dynamic Image Generation:** Automatically creates visual question slides for each MCQ.
* **Audio Normalization:** Ensures consistent volume levels across all segments using ffmpeg.
* **Dockerized Workflow:** Fully containerized to handle complex dependencies like ffmpeg and opencv effortlessly.
* **Automated Stitching:** Seamlessly merges intros, audio scripts, and question segments into a final practice video.



## Project Structure

### Python Scripts
* **generate_audio_segments_multi_voice.py:** Handles Azure TTS synthesis with multi-voice support.
* **generate_question_images.py:** Converts text questions into visual slides.
* **generate_video_segments_and_merge.py:** Stitches audio and images into video clips.

### Orchestration and Shell
* **entrypoint.sh:** The master orchestrator that runs the 5-stage pipeline.
* **normalize_segments_and_merge_final.sh:** Post-processing for audio consistency and final rendering.

## Prerequisites

* Docker installed and configured.
* An Azure Speech Services account with an API Key and Region.

## Setup and Installation

### 1. Clone the repository
```bash
git clone [https://github.com/rajeshclt3/Inburgering-listening-mcq-video.git](https://github.com/rajeshclt3/Inburgering-listening-mcq-video.git)
cd Inburgering-listening-mcq-video

git clone https://github.com/rajeshclt3/Inburgering-listening-mcq-video.git
cd Inburgering-listening-mcq-video
Configure Environment Variables: Create a .env file in the root directory (do not commit this file!):

Plaintext

AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=westeurope
Prepare Input Data: Place your script and questions in an input.txt file inside your project folder using the required ### AUDIO_SCRIPT_X ### format.

Usage
You can run the entire pipeline using Docker. This ensures all dependencies (Python, FFMPEG, etc.) are correctly configured.

Build the Image
Bash

docker build -t knm-video-gen .
Run the Pipeline
Bash

docker run -it --env-file .env -v $(pwd):/data knm-video-gen
The final output will be generated in /data/final_video/final_video.mp4.

Security & Best Practices
Secrets Management: API keys are managed via .env files and are never hardcoded in the source or committed to version control.