import os
import json
import random
import requests
import re

def get_reddit_wallpapers():
    url = "https://www.reddit.com/r/Animewallpaper/new.json?limit=50"
    headers = {"User-Agent": "python:weebhq.pinterest.bot:v1.0 (by /u/weebhq)"}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to fetch from Reddit API. Status: {res.status_code}")
        # Fallback to safebooru if Reddit blocks us
        return get_safebooru_wallpapers()
    
    posts = res.json().get('data', {}).get('children', [])
    wallpapers = []
    
    for p in posts:
        data = p.get('data', {})
        title = data.get('title', 'Anime Wallpaper')
        post_id = data.get('id', '')
        url = data.get('url', '')
        
        if url.endswith(('.jpg', '.png', '.jpeg')):
            wallpapers.append({
                'id': post_id,
                'title': title,
                'url': url
            })
            
    if not wallpapers:
        return get_safebooru_wallpapers()
        
    return wallpapers

def get_safebooru_wallpapers():
    print("Fetching from Safebooru as fallback...")
    # Pick a random page to ensure we always get fresh images that aren't in history
    page = random.randint(1, 50)
    url = f"https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&limit=100&pid={page}&tags=highres"
    res = requests.get(url)
    if res.status_code != 200:
        print("Safebooru fetch failed.")
        return []
        
    posts = res.json()
    wallpapers = []
    for p in posts:
        post_id = str(p.get('id', ''))
        width = int(p.get('width', 0))
        height = int(p.get('height', 0))
        
        # Pinterest prefers vertical images (2:3 aspect ratio).
        if height <= width:
            continue
            
        # Safebooru image url format: https://safebooru.org/images/directory/image.jpg
        img_url = f"https://safebooru.org/images/{p.get('directory')}/{p.get('image')}"
        
        # Create a nice title from tags
        tags = p.get('tags', '').split()
        character = "Anime"
        for t in tags:
            if "girl" in t or "boy" in t:
                continue
            if len(t) > 3 and not t.isnumeric():
                character = t.replace('_', ' ').title()
                break
                
        title = f"{character} - Aesthetic Anime Wallpaper"
        
        wallpapers.append({
            'id': "safebooru_" + post_id,
            'title': title,
            'url': img_url
        })
        
    # Shuffle so we pick a random one from this page
    random.shuffle(wallpapers)
    return wallpapers

def load_history():
    if os.path.exists("pinterest_history.txt"):
        with open("pinterest_history.txt", "r") as f:
            return set(f.read().splitlines())
    return set()

def save_history(post_id):
    with open("pinterest_history.txt", "a") as f:
        f.write(f"{post_id}\n")

def pin_to_pinterest(image_url, title, token, board_id):
    url = "https://api-sandbox.pinterest.com/v5/pins"
    
    description = "#bestanimewallpaper #animewallpapers #liveanimewallpapers #freeanimewallpapers #animelivewallpaperspc #animelivewallpaperswallpaperengine #animewallpaper #animelivewallpapersforwallpaperengine #animegirlslivewallpapers4k #4kanimewallpaper #hdanimewallpaper #topanimewallpaper #liveanimewallpaper #animelivewallpaper #cuteanimewallpaper #animewallpaperlive #freeanimewallpaper #anime4kwallpaper #anime3dwallpaper #animewallpaperforpc #animephonewallpaper #anime4klivewallpaper"
    
    payload = {
        "board_id": board_id,
        "title": title[:100],  # Max 100 chars
        "description": description[:500],
        "link": "https://weebhq.com",
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code in [200, 201]:
        print("Successfully pinned to Pinterest!")
        return True
    else:
        print("Failed to pin:", res.text)
        return False

def main():
    token = os.environ.get("PINTEREST_ACCESS_TOKEN")
    board_id = os.environ.get("PINTEREST_BOARD_ID")
    
    if not token or not board_id:
        print("Missing Pinterest secrets. Exiting.")
        return
        
    print("Fetching wallpapers from Reddit via RSS Proxy...")
    wallpapers = get_reddit_wallpapers()
    
    if not wallpapers:
        print("No wallpapers found.")
        return
        
    history = load_history()
    
    # Find a new wallpaper
    selected = None
    for wp in wallpapers:
        if wp['id'] not in history:
            selected = wp
            break
            
    if not selected:
        print("All fetched wallpapers have already been posted.")
        return
        
    print(f"Selected Wallpaper: {selected['title']}")
    
    success = pin_to_pinterest(selected['url'], selected['title'], token, board_id)
    
    if success:
        save_history(selected['id'])
        print(f"Added {selected['id']} to history.")

if __name__ == "__main__":
    main()
