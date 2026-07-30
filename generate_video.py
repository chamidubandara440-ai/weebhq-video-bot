import sys
import os
import urllib.request
import asyncio
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, vfx
from PIL import Image, ImageDraw, ImageFont
import textwrap

def generate_overlay(title, width=1080, height=1920):
    # Create a transparent overlay image
    overlay = Image.new("RGBA", (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    # Fonts
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_banner = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        font_main = ImageFont.load_default()
        font_banner = ImageFont.load_default()

    # Draw Banner
    banner_text = " WEEBHQ ANIME NEWS "
    # We don't have font.getbbox in older PIL sometimes, just hardcode approx size
    # Using generic textbbox if available
    try:
        bbox = draw.textbbox((0,0), banner_text, font=font_banner)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except:
        tw, th = 500, 50
        
    draw.rectangle([(width-tw)/2 - 20, 200, (width+tw)/2 + 20, 200 + th + 20], fill=(230,0,20,255))
    draw.text(((width-tw)/2, 210), banner_text, font=font_banner, fill="white")
    
    # Draw Title
    wrapped_title = textwrap.fill(title, width=25)
    lines = wrapped_title.split('\n')
    
    y = 350
    for line in lines:
        try:
            bbox = draw.textbbox((0,0), line, font=font_main)
            tw = bbox[2] - bbox[0]
        except:
            tw = 800
        
        # Draw shadow
        draw.text(((width-tw)/2 + 4, y + 4), line, font=font_main, fill="black")
        # Draw text
        draw.text(((width-tw)/2, y), line, font=font_main, fill="white")
        y += 80
        
    # Draw Footer
    footer = "Read more at weebhq.com"
    try:
        bbox = draw.textbbox((0,0), footer, font=font_banner)
        fw = bbox[2] - bbox[0]
    except:
        fw = 400
    draw.text(((width-fw)/2, height - 200), footer, font=font_banner, fill=(200,200,200,255))
    
    overlay.save("overlay.png")

def main():
    if len(sys.argv) < 5:
        print("Missing arguments")
        return
        
    title = sys.argv[1]
    summary = sys.argv[2]
    image_url = sys.argv[3]
    permalink = sys.argv[4]
    
    print(f"Generating advanced video for: {title}")
    
    # 1. Download Image
    image_path = "cover.jpg"
    urllib.request.urlretrieve(image_url, image_path)
    print("Downloaded image.")
    
    # 2. Generate Overlay
    generate_overlay(title)
    
    # 3. Generate Voice (Edge TTS)
    text = f"Anime News! {title}. {summary}"
    voice = "en-US-ChristopherNeural"
    audio_path = "voice.mp3"
    
    async def generate_audio():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(audio_path)
        
    asyncio.run(generate_audio())
    print("Generated TTS audio.")
    
    # 4. Create Video with MoviePy
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    # Base Image
    base_clip = ImageClip(image_path).set_duration(duration)
    w, h = base_clip.size
    
    # Crop to 9:16
    target_ratio = 9/16
    current_ratio = w/h
    if current_ratio > target_ratio:
        new_w = h * target_ratio
        x_center = w/2
        base_clip = base_clip.crop(x1=x_center-new_w/2, y1=0, x2=x_center+new_w/2, y2=h)
    else:
        new_h = w / target_ratio
        y_center = h/2
        base_clip = base_clip.crop(x1=0, y1=y_center-new_h/2, x2=w, y2=y_center+new_h/2)
        
    # Resize and apply simple zoom
    base_clip = base_clip.resize(width=1080, height=1920)
    # Slow zoom-in effect (5% zoom over duration)
    # resize lambda is very CPU intensive but works
    # A lightweight alternative is to scale it once and pan, but resize lambda is standard:
    zoom_clip = base_clip.resize(lambda t: 1 + 0.04 * (t/duration)).set_position('center')
    
    # We must crop it back to 1080x1920 after zoom because it gets larger
    def crop_center(get_frame, t):
        frame = get_frame(t)
        # return a cropped version
        return frame
    
    # A much safer zoom in moviepy without breaking resolution:
    zoom_clip = zoom_clip.crop(x_center=540, y_center=960, width=1080, height=1920)
    
    # Overlay Clip
    overlay_clip = ImageClip("overlay.png").set_duration(duration)
    
    # Composite
    final_clip = CompositeVideoClip([zoom_clip, overlay_clip])
    final_clip = final_clip.set_audio(audio)
    
    output_path = "output.mp4"
    final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print("Video rendered successfully!")
    
    # 5. Upload to TikTok
    session_id = os.environ.get("TIKTOK_SESSION_ID")
    if session_id:
        print("Starting TikTok Upload...")
        from tiktok_uploader.upload import upload_video
        
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

    # 6. Upload to Facebook Reels
    fb_token = os.environ.get("FB_PAGE_TOKEN")
    fb_page_id = os.environ.get("FB_PAGE_ID")
    
    if fb_token and fb_page_id:
        print("Starting Facebook Reels Upload...")
        import requests
        
        # Step 1: Initialize Upload
        init_url = f"https://graph.facebook.com/v19.0/{fb_page_id}/video_reels"
        init_data = {
            "upload_phase": "start",
            "access_token": fb_token
        }
        res = requests.post(init_url, data=init_data)
        if res.status_code == 200:
            res_json = res.json()
            video_id = res_json.get('video_id')
            upload_url = res_json.get('upload_url')
            
            if video_id and upload_url:
                print(f"FB Video ID: {video_id}. Uploading...")
                
                # Step 2: Upload Video Data
                headers = {
                    "Authorization": f"OAuth {fb_token}",
                    "file_offset": "0"
                }
                with open('output.mp4', 'rb') as f:
                    file_data = f.read()
                
                upload_res = requests.post(upload_url, headers=headers, data=file_data)
                if upload_res.status_code == 200:
                    print("Upload complete. Publishing...")
                    
                    # Step 3: Finish Upload & Publish
                    finish_data = {
                        "upload_phase": "finish",
                        "access_token": fb_token,
                        "video_id": video_id,
                        "video_state": "PUBLISHED",
                        "description": f"{title}\n\n#anime #animenews #weebhq #manga"
                    }
                    pub_res = requests.post(init_url, data=finish_data)
                    if pub_res.status_code == 200:
                        print("Successfully uploaded and published to Facebook Reels!")
                    else:
                        print("FB Publish failed:", pub_res.text)
                else:
                    print("FB Upload chunk failed:", upload_res.text)
            else:
                print("FB Init failed to return video_id/upload_url")
        else:
            print("FB Init failed:", res.text)
    else:
        print("No FB_PAGE_TOKEN or FB_PAGE_ID found. Skipping FB Reels upload.")

if __name__ == "__main__":
    main()
