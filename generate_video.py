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
    
    clip = ImageClip(image_path).set_duration(duration)
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
    clip = clip.set_audio(audio)
    
    output_path = "output.mp4"
    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print("Video rendered successfully!")
    
    # 4. Upload to TikTok
    session_id = os.environ.get("TIKTOK_SESSION_ID")
    if session_id:
        print("Starting TikTok Upload...")
        from tiktok_uploader.upload import upload_video
        
        # Create a simple netscape cookies file for tiktok-uploader
        with open("cookies.txt", "w") as f:
            f.write(f".tiktok.com\tTRUE\t/\tFALSE\t2147483647\tsessionid\t{session_id}\n")
            
        description = f"{title} #anime #animenews #manga #weebhq"
        
        try:
            upload_video('output.mp4', description=description, cookies='cookies.txt')
            print("Successfully uploaded to TikTok!")
        except Exception as e:
            print(f"TikTok upload failed: {e}")
    else:
        print("No TIKTOK_SESSION_ID found. Skipping upload.")

if __name__ == "__main__":
    main()