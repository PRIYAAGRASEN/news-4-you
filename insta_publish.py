# insta_publish.py

import os
import requests
import time

INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
GRAPH_API = "https://graph.facebook.com/v19.0"


def create_image_container(image_url, caption=None):
    payload = {
        "image_url": image_url,
        "is_carousel_item": True,
        "access_token": ACCESS_TOKEN
    }
    if caption:
        payload["caption"] = caption

    r = requests.post(
        f"{GRAPH_API}/{INSTAGRAM_USER_ID}/media",
        data=payload
    )
    data = r.json()
    print("INSTAGRAM RESPONSE:", data)
    return data.get("id")


def wait_until_ready(creation_id, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(
            f"{GRAPH_API}/{creation_id}",
            params={
                "fields": "status_code",
                "access_token": ACCESS_TOKEN
            }
        )
        res = r.json()
        status = res.get("status_code")
        if status == "FINISHED":
            return True
        elif status== "ERROR":
            print(f" Container {creation_id} failed: {res.get('error_description')}")
            return False
        
        print(f"{creation_id} still {status}... waiting 10s")
        time.sleep(10)
    return False


def create_carousel_container(children_ids, caption):
    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }

    r = requests.post(
        f"{GRAPH_API}/{INSTAGRAM_USER_ID}/media",
        data=payload
    )
    data = r.json()
    print("INSTAGRAM RESPONSE:", data)
    return data.get("id")


def publish_container(creation_id, retries=3):
    for i in range(retries):
        r = requests.post(
            f"{GRAPH_API}/{INSTAGRAM_USER_ID}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": ACCESS_TOKEN
            }
        )

        if r.ok:
            return r.json()

        print(f"⚠️ Publish attempt {i+1} failed:", r.text)
        # If it's a "Media not ready" error, wait longer
        # If it's a "Rate limit" error, wait MUCH longer
        wait_time = (i + 1) * 40 
        print(f"💤 Sleeping {wait_time}s before retrying...")
        time.sleep(wait_time)

    return None



def post_carousel(image_urls, caption):
    child_ids = []

    # 1️⃣ create child containers
    for url in image_urls:
        cid = create_image_container(url)
        if not cid:
            raise Exception("Failed to create image container")
        child_ids.append(cid)

    # 2️⃣ wait until all are ready
    for cid in child_ids:
        ok = wait_until_ready(cid)
        if not ok:
            print("⚠️ Child container not ready, continuing anyway")

    # 3️⃣ create carousel container
    carousel_id = create_carousel_container(child_ids, caption)
    if not carousel_id:
        raise Exception("Failed to create carousel container")

    # 4. NEW: Wait for the CAROUSEL itself to be ready
    # This is likely why you got the 9007 error!
    print("⏳ Waiting for carousel to finalize...")
    if not wait_until_ready(carousel_id):
        print("❌ Carousel container failed to finalize.")
        return False
    # 4️⃣ publish (SAFE)
   
    result = publish_container(carousel_id)

    if not result:
        return False

    return True
