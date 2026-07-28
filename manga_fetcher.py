import os
import sys
import requests
import json
from PIL import Image
from io import BytesIO

# Input args
manga_id = sys.argv[1]
chapter_id = sys.argv[2]
chapter_num = sys.argv[3]
chapter_title = sys.argv[4]

WP_URL = os.environ.get('WP_URL', 'https://weebhq.com')
WP_USERNAME = os.environ.get('WP_USERNAME', 'admin') # Needs to be set in GH Secrets
WP_APP_PASSWORD = os.environ.get('WP_APP_PASSWORD')

def main():
    print(f"Fetching Chapter {chapter_num} (ID: {chapter_id}) for Manga {manga_id}")
    
    # 1. Fetch images from MangaDex
    res = requests.get(f"https://api.mangadex.org/at-home/server/{chapter_id}")
    data = res.json()
    base_url = data['baseUrl']
    hash_val = data['chapter']['hash']
    filenames = data['chapter']['data']
    
    attachment_ids = []
    
    for i, file in enumerate(filenames):
        img_url = f"{base_url}/data/{hash_val}/{file}"
        print(f"Downloading {i+1}/{len(filenames)}...")
        
        # Download
        img_res = requests.get(img_url)
        img = Image.open(BytesIO(img_res.content))
        
        # Convert to WebP
        webp_io = BytesIO()
        img.save(webp_io, format="WEBP", quality=85)
        webp_io.seek(0)
        
        # Upload to WordPress
        wp_media_url = f"{WP_URL}/wp-json/wp/v2/media"
        headers = {
            'Content-Disposition': f'attachment; filename="manga_{manga_id}_ch{chapter_num}_{i+1}.webp"',
            'Content-Type': 'image/webp'
        }
        
        auth = (WP_USERNAME, WP_APP_PASSWORD)
        upload_res = requests.post(wp_media_url, headers=headers, data=webp_io, auth=auth)
        
        if upload_res.status_code == 201:
            attachment_ids.append(upload_res.json()['id'])
            print(f"Uploaded successfully. ID: {upload_res.json()['id']}")
        else:
            print(f"Upload failed: {upload_res.text}")
            
    # 2. Create Chapter Post
    if attachment_ids:
        print("Creating Chapter Post...")
        create_url = f"{WP_URL}/wp-json/weebhq/v1/manga-chapter"
        payload = {
            "manga_id": manga_id,
            "chapter_num": chapter_num,
            "title": chapter_title,
            "mangadex_chapter_id": chapter_id,
            "attachment_ids": attachment_ids
        }
        
        create_res = requests.post(create_url, json=payload, auth=auth)
        print(create_res.text)
        print("Done!")

if __name__ == "__main__":
    main()