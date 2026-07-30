import os
import json
import random
import requests
import re

def get_reddit_wallpapers():
    url = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fwww.reddit.com%2Fr%2FAnimewallpaper%2Fnew.rss"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Failed to fetch from RSS proxy. Status: {res.status_code}")
        return []
    
    posts = res.json().get('items', [])
    wallpapers = []
    
    for p in posts:
        title = p.get('title', 'Anime Wallpaper')
        post_id = p.get('guid', '')
        content = p.get('content', '')
        
        # Extract the high-res image link from the HTML content
        # It looks like: <a href="https://i.redd.it/xyz.png">[link]</a>
        match = re.search(r'<a href="(https://i\.redd\.it/[^"]+)">\[link\]</a>', content)
        if match:
            image_url = match.group(1)
            wallpapers.append({
                'id': post_id,
                'title': title,
                'url': image_url
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
    url = "https://api-sandbox.pinterest.com/v5/pins"
    
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
