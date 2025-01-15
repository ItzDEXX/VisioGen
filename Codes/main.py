import whisper
import os
import shutil
import cv2
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import numpy as np

FONT_SCALE = 2
FONT_THICKNESS = 2

class VideoTranscriber:
    def __init__(self, model_path, video_path):
        self.model = whisper.load_model(model_path)
        self.video_path = video_path
        self.audio_path = ''
        self.text_array = []
        self.fps = 0

    def transcribe_video(self):
        print('Transcribing video...')

        # Get the provided text from the environment variable
        transcribe_text = os.environ.get('RECEIVED_TEXT', '')  
        if not transcribe_text:
            raise ValueError("No text provided for captions.")

        # Perform transcription with word timestamps
        result = self.model.transcribe(self.audio_path, word_timestamps=True)

        # Prepare video capture for timing
        cap = cv2.VideoCapture(self.video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)

        # Split provided text into words
        provided_words = transcribe_text.split(" ")
        audio_words = [word for segment in result['segments'] for word in segment['words']]

        if len(provided_words) != len(audio_words):
            print("Warning: Provided text has a different word count than the transcribed audio.")

        for i, audio_word in enumerate(audio_words):
            if i < len(provided_words):
                word = provided_words[i]
            else:
                word = ''  # Fallback in case we have more audio words than provided text

            start_time = audio_word['start']
            end_time = audio_word['end']

            # Adjust timing based on pauses after punctuation
            if word in {',', '.', '!', '?'}:  # Check if the current word is a punctuation mark
                if word == ',':
                    end_time += 0.2  # 200 ms pause after a comma
                elif word in {'.', '!', '?'}:
                    end_time += 0.4  # 400 ms pause after a full stop

                # If the next word exists, adjust its start time
                if i + 1 < len(audio_words):
                    next_word_start_time = audio_words[i + 1]['start']
                    if next_word_start_time < end_time:
                        next_word_start_time = end_time  # Delay the next word to start after the punctuation pause
                    audio_words[i + 1]['start'] = next_word_start_time

            # Calculate frame range for each word
            start_frame = int(start_time * self.fps)
            end_frame = int(end_time * self.fps)

            # Append word and its adjusted frame range
            self.text_array.append([word, start_frame, end_frame])

        cap.release()
        print('Transcription complete.')


    def extract_audio(self):
        print('Extracting audio...')
        audio_path = os.path.join(os.path.dirname(self.video_path), "audio.mp3")
        video = VideoFileClip(self.video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        self.audio_path = audio_path
        print('Audio extracted.')

    def extract_frames(self, output_folder, font):
        print('Extracting frames...')
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        N_frames = 0

        with tqdm(total=total_frames, desc="Extracting Frames") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_image)

                for text_info in self.text_array:
                    if text_info[1] <= N_frames <= text_info[2]:
                        text = text_info[0]
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_size = (text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1])
                        text_x = int((width - text_size[0]) / 2)
                        text_y = height - 200

                        outline_thickness = 4
                        for x_offset in [-outline_thickness, 0, outline_thickness]:
                            for y_offset in [-outline_thickness, 0, outline_thickness]:
                                draw.text((text_x + x_offset, text_y + y_offset), text, font=font, fill=(0, 0, 0))

                        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
                        break

                frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                cv2.imwrite(os.path.join(output_folder, f"{N_frames:05d}.jpg"), frame)

                N_frames += 1
                pbar.update(1)

        cap.release()
        print(f'{N_frames} frames extracted.')

    def create_video(self, output_video_path, font):
        print('Creating video...')
        image_folder = os.path.join(os.path.dirname(self.video_path), "frames")
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        self.extract_frames(image_folder, font)

        images = sorted([img for img in os.listdir(image_folder) if img.endswith(".jpg")],
                        key=lambda x: int(x.split(".")[0]))

        clip = ImageSequenceClip([os.path.join(image_folder, image) for image in images], fps=self.fps)
        audio = AudioFileClip(self.audio_path)
        clip = clip.set_audio(audio)
        clip.write_videofile(output_video_path)

        shutil.rmtree(image_folder)
        os.remove(self.audio_path)
        print(f'Video saved at {output_video_path}')


def choose_font():
    font = os.environ.get('SELECTED_FONT', 'Arvo-Bold')
    font_path = ""

    # Adjust paths to the VisioGen directory
    if font == 'naname-goma':
        font_path = "/home/ubuntu/VisioGen/gomarice_naname_goma.ttf"
    elif font == 'Handscript':
        font_path = "/home/ubuntu/VisioGen/Handscript.ttf"
    elif font == 'Shikaku-serif':
        font_path = "/home/ubuntu/VisioGen/gomarice_shikaku_serif.ttf"
    elif font == 'Arvo-Bold':
        font_path = "/home/ubuntu/VisioGen/Arvo-Bold.ttf"
    else:
        print("Invalid font provided. Defaulting to Arvo-Bold.")
        font_path = "/home/ubuntu/VisioGen/Arvo-Bold.ttf"

    font_size = 60
    return ImageFont.truetype(font_path, font_size)


# Example usage
model_path = "base"
video_path = "/home/ubuntu/VisioGen/random_subclip_with_audio.mp4"
output_video_path = "/home/ubuntu/VisioGen/random_subclip_with_audio(captioned).mp4"

transcriber = VideoTranscriber(model_path, video_path)
font = choose_font()
transcriber.extract_audio()
transcriber.transcribe_video()
transcriber.create_video(output_video_path, font)
