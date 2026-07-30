import os
import json
import random
import requests
from urllib.parse import urlparse

def get_reddit_wallpapers():
    url = "https://www.reddit.com/r/Animewallpaper/new.json?limit=50"
    headers = {"User-Agent": "WeebHQ-Wallpaper-Bot/1.0"}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("Failed to fetch from Reddit.")
        return []
    
    posts = res.json().get('data', {}).get('children', [])
    wallpapers = []
    
    for p in posts:
        data = p.get('data', {})
        url = data.get('url', '')
        title = data.get('title', 'Anime Wallpaper')
        post_id = data.get('id', '')
        
        # Only accept direct image links
        if url.endswith(('.jpg', '.jpeg', '.png')):
            wallpapers.append({
                'id': post_id,
                'title': title,
                'url': url
            })
            
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
    url = "https://api.pinterest.com/v5/pins"
    
    # Clean up title for description
    description = f"{title}\n\nFind more awesome Anime content and news at WeebHQ!\n#anime #animewallpaper #weebhq #manga #otaku"
    
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
        
    print("Fetching wallpapers from Reddit...")
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
