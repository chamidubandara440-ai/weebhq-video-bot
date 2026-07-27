import sys
import os
import urllib.request
import asyncio
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip

def main():
    if len(sys.argv) < 5:
        print("Missing arguments")
        return
        
    title = sys.argv[1]
    summary = sys.argv[2]
    image_url = sys.argv[3]
    permalink = sys.argv[4]
    
    print(f"Generating video for: {title}")
    
    # 1. Download Image
    image_path = "cover.jpg"
    urllib.request.urlretrieve(image_url, image_path)
    print("Downloaded image.")
    
    # 2. Generate Voice (Edge TTS)
    text = f"Anime News! {title}. {summary}"
    voice = "en-US-ChristopherNeural"
    audio_path = "voice.mp3"
    
    async def generate_audio():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(audio_path)
        
    asyncio.run(generate_audio())
    print("Generated TTS audio.")
    
    # 3. Create Video with MoviePy
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    # Base Image Clip (9:16 aspect ratio)
    clip = ImageClip(image_path).set_duration(duration)
    
    # Crop to 9:16 (1080x1920)
    w, h = clip.size
    target_ratio = 9/16
    current_ratio = w/h
    if current_ratio > target_ratio:
        new_w = h * target_ratio
        x_center = w/2
        clip = clip.crop(x1=x_center-new_w/2, y1=0, x2=x_center+new_w/2, y2=h)
    else:
        new_h = w / target_ratio
        y_center = h/2
        clip = clip.crop(x1=0, y1=y_center-new_h/2, x2=w, y2=y_center+new_h/2)
        
    clip = clip.resize(width=1080, height=1920)
    
    # Set audio
    clip = clip.set_audio(audio)
    
    # Render
    output_path = "output.mp4"
    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print("Video rendered successfully!")

if __name__ == "__main__":
    main()