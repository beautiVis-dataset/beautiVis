import csv
import glob
import os
import re
import time
import requests
from pathlib import Path

def get_image_url_from_json(reddit_url):
    """
    Retrieve the Reddit post's JSON data by appending '/.json' to the URL.
    Implements retries with sleeping for error code 429 (and other errors).
    Returns the image URL (from the preview field if available, or the fallback URL)
    or None if extraction fails.
    """
    json_url = reddit_url.rstrip('/') + '/.json'
    headers = {"User-Agent": "Mozilla/5.0"}
    max_retries = 5
    response = None

    for attempt in range(max_retries):
        try:
            response = requests.get(json_url, headers=headers, timeout=10)
        except Exception as e:
            print(f"Error retrieving {json_url}: {e}")
            response = None

        if response is None or response.status_code != 200:
            if response is not None and response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 480))
                print(f"Attempt {attempt + 1}/{max_retries}: Received 429 error. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                status = response.status_code if response is not None else "No Response"
                print(f"Attempt {attempt + 1}/{max_retries}: Could not retrieve post (status: {status}). Sleeping 15 seconds...")
                time.sleep(15)
        else:
            break
    else:
        print(f"Failed to retrieve post after {max_retries} tries: {reddit_url}")
        return None

    try:
        data = response.json()
        post_data = data[0]['data']['children'][0]['data']
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None

    author = post_data.get("author")
    if not author or author == "[deleted]":
        print(f"Post deleted: {reddit_url}")
        return None
    if not post_data.get("is_robot_indexable", True):
        print(f"Post removed: {reddit_url}")
        return None

    if "preview" in post_data:
        images = post_data["preview"].get("images", [])
        if images:
            return images[0]["source"]["url"].replace("&amp;", "&")

    fallback_url = post_data.get("url", "")
    if fallback_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        return fallback_url

    return None

def download_image(image_url, save_path):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(image_url, headers=headers, stream=True, timeout=15)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
        print(f"Failed to download (HTTP {response.status_code})")
    except Exception as e:
        print(f"Download error: {e}")
    return False

def process_csv_file(csv_path, downloaded_csv_dir, downloaded_images_dir):
    basename = os.path.basename(csv_path)
    match = re.match(r"(\d{4}-\d{2})-combined\.csv", basename)
    if not match:
        print(f"Skipping non-combined file: {basename}")
        return

    year_month = match.group(1)
    output_csv = os.path.join(downloaded_csv_dir, f"{year_month}-downloaded.csv")
    image_dir = os.path.join(downloaded_images_dir, year_month)
    os.makedirs(image_dir, exist_ok=True)

    with open(csv_path, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            print(f"Empty CSV: {csv_path}")
            return

        fieldnames = reader.fieldnames
        rows = []
        success_count = 0

        for row in reader:
            reddit_url = row.get("full_permalink", "")
            title = row.get("title", "no title")[:100] 
            image_file = row.get("image_file", "")
            
            if not image_file:
                print(f"\nSkipping {title} - no image_file in CSV")
                continue

            image_path = os.path.join(image_dir, image_file)
            
            # Skip if image already exists
            if os.path.exists(image_path):
                print(f"\nImage exists: {image_file}")
                rows.append(row)
                success_count += 1
                continue

            if reddit_url:
                print(f"\nProcessing: {title}")
                image_url = get_image_url_from_json(reddit_url)

                if image_url:
                    if download_image(image_url, image_path):
                        print(f"Downloaded {image_file}")
                        rows.append(row)
                        success_count += 1
                    else:
                        print(f"Failed to download {image_file}")
                else:
                    print(f"No image URL found for {image_file}")
                
                time.sleep(5)
            else:
                print(f"\nSkipping {title} - no full_permalink")


    with open(output_csv, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created downloaded CSV: {output_csv} with {success_count} images")

def main():
    downloaded_csv_dir = "downloaded_csv"
    downloaded_images_dir = "downloaded_images"
    os.makedirs(downloaded_csv_dir, exist_ok=True)
    os.makedirs(downloaded_images_dir, exist_ok=True)

    csv_files = glob.glob(os.path.join("combined_csv", "*-combined.csv"))
    if not csv_files:
        print("No combined CSV files found")
        return

    for csv_file in csv_files:
        print(f"\nProcessing combined file: {csv_file}")
        process_csv_file(csv_file, downloaded_csv_dir, downloaded_images_dir)

if __name__ == "__main__":
    main()