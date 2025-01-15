import os
from pathlib import Path
import subprocess
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from google.cloud import texttospeech
from google.oauth2 import service_account

app = Flask(__name__)
CORS(app)

# Base directory
BASE_DIR = Path("/home/ubuntu/VisioGen")

# File paths using Path for better cross-platform compatibility
PATHS = {
    'audio': BASE_DIR / "output.mp3",
    'editing_script': BASE_DIR / "editing.py",
    'main_script': BASE_DIR / "main.py",
    'output_video': BASE_DIR / "random_subclip_with_audio(captioned).mp4",
    'credentials': BASE_DIR / "ordinal-door-446822-p4-41977e7b9dc7.json",
    'venv_python': BASE_DIR / "venv/bin/python3"
}

def synthesize_text(text, voice_gender, speech_speed):
    try:
        credentials = service_account.Credentials.from_service_account_file(str(PATHS['credentials']))
        client = texttospeech.TextToSpeechClient(credentials=credentials)

        voice_name = 'en-US-Neural2-F' if voice_gender.lower() == 'female' else 'en-US-Neural2-D'
        
        voice = texttospeech.VoiceSelectionParams(
            language_code='en-US',
            name=voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speech_speed
        )

        synthesis_input = texttospeech.SynthesisInput(text=text)

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        PATHS['audio'].parent.mkdir(parents=True, exist_ok=True)
        with open(PATHS['audio'], "wb") as out:
            out.write(response.audio_content)
            print(f'Audio content written to file "{PATHS["audio"]}"')

    except Exception as e:
        print(f"Error synthesizing text with Google Cloud TTS: {e}")
        raise

def run_editing_script(timeout=300):
    try:
        for script in ['editing_script', 'main_script']:
            print(f'Running {script}...')
            result = subprocess.run(
                [str(PATHS['venv_python']), str(PATHS[script])],
                check=True,
                timeout=timeout,
                capture_output=True,
                text=True
            )
            print(f'Output from {script}:\n{result.stdout}')
            if result.stderr:
                print(f'Errors from {script}:\n{result.stderr}')

    except subprocess.TimeoutExpired as e:
        print(f'Script timed out after {timeout} seconds')
        raise
    except subprocess.CalledProcessError as e:
        print(f'Script failed with exit code {e.returncode}')
        print(f'Output:\n{e.output}')
        print(f'Error:\n{e.stderr}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        raise

def generate_large_file(file_path, chunk_size=8192):
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(chunk_size):
                yield chunk
    except Exception as e:
        print(f"Error generating file chunks: {e}")
        raise

def set_environment_variables(font, video_type, text):
    os.environ.update({
        'SELECTED_FONT': font,
        'VIDEO_TYPE': video_type,
        'RECEIVED_TEXT': text
    })

@app.route('/endpoint', methods=['POST', 'GET'])
def process_text():
    if request.method == 'POST':
        if not request.is_json:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400

        try:
            data = request.get_json()
            text = data.get('text', '')
            if not text:
                return jsonify({'status': 'error', 'message': 'Text for synthesis is required.'}), 400

            font = data.get('font', 'Arvo-Bold')
            video_type = data.get('videoType', 'Minecraft')
            voice_gender = data.get('voiceType', 'Male')
            speech_speed = float(data.get('speechSpeed', 1.0))

            print(f"Processing request - Text: {text}, Font: {font}, "
                  f"Video Type: {video_type}, Voice: {voice_gender}, Speed: {speech_speed}")

            synthesize_text(text, voice_gender, speech_speed)
            set_environment_variables(font, video_type, text)
            run_editing_script()

            if PATHS['output_video'].exists():
                return jsonify({
                    'status': 'success',
                    'video_url': f'https://{request.host}/endpoint/video'
                })
            return jsonify({'status': 'error', 'message': 'Video file not found'}), 404

        except Exception as e:
            print(f"Error processing request: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'error', 'message': 'Use POST to generate video.'}), 405

@app.route('/endpoint/video', methods=['GET'])
def send_video():
    if PATHS['output_video'].exists():
        return Response(
            stream_with_context(generate_large_file(PATHS['output_video'])),
            mimetype='video/mp4',
            headers={
                "Content-Disposition": 'attachment; filename="output.mp4"',
                "Cache-Control": "no-cache",
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )
    return jsonify({'status': 'error', 'message': 'Video file not found'}), 404

if __name__ == '__main__':
    # Ensure required directories exist
    for path in PATHS.values():
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    