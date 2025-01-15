import os
from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image

# Folder containing images and output path
images_folder = r"D:\Coding\Python\VisioGen\Images"
output_video_path = r"D:\Coding\Python\VisioGen\aiimages_video.mp4"

# Duration for zoom-in effect and crossfade transition
zoom_in_duration = 2  # seconds
crossfade_duration = 1  # seconds

# Collect all image files
image_files = [os.path.join(images_folder, img) for img in os.listdir(images_folder) if img.endswith(('.png', '.jpg', '.jpeg'))]

# Create clips with zoom-in effect and crossfade transition
clips = []
for image_path in image_files:
    # Open and resize image with Pillow for zoom-in effect
    with Image.open(image_path) as img:
        img_zoomed_in = img.resize((int(img.width * 1.2), int(img.height * 1.2)), Image.LANCZOS)
        img_zoomed_in.save("zoom_in_temp.png")

    # Create image clip with zoom-in effect
    zoom_in_clip = ImageClip("zoom_in_temp.png", duration=zoom_in_duration)
    zoom_in_clip = zoom_in_clip.fadein(crossfade_duration)  # Apply fadein effect for transition
    clips.append(zoom_in_clip)

# Concatenate all image clips
final_video = concatenate_videoclips(clips, method="compose")

# Write the final video to a file
final_video.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-preset", "ultrafast"])

print(f"Video saved at: {output_video_path}")
