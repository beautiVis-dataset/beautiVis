import csv
import glob
import os
import re
import time
import requests

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
                print(f"Attempt {attempt + 1}/{max_retries}: Received 429 error for {reddit_url}. Waiting for {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                status = response.status_code if response is not None else "No Response"
                print(f"Attempt {attempt + 1}/{max_retries}: Could not retrieve post {reddit_url} (status: {status}). Sleeping for 15 seconds...")
                time.sleep(15)
        else:
            break
    else:
        print(f"Failed to retrieve post after {max_retries} tries: {reddit_url}")
        return None

    try:
        data = response.json()
    except Exception as e:
        print(f"Error parsing JSON for {reddit_url}: {e}")
        return None

    try:
        post_data = data[0]['data']['children'][0]['data']
    except Exception as e:
        print(f"Error extracting post data from JSON for {reddit_url}: {e}")
        return None

    author = post_data.get("author")
    is_robot_indexable = post_data.get("is_robot_indexable", True)
    if not author or author == "[deleted]":
        print(f"The post is deleted: {reddit_url}")
        return None
    if not is_robot_indexable:
        print(f"The post is removed: {reddit_url}")
        return None

    if "preview" in post_data:
        images = post_data["preview"].get("images", [])
        if images:
            image_url = images[0]["source"]["url"].replace("&amp;", "&")
            return image_url

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
            print(f"Image saved to {save_path}")
        else:
            print(f"Failed to download image {image_url} (HTTP {response.status_code})")
    except Exception as e:
        print(f"Error downloading image {image_url}: {e}")

def process_csv_file(csv_path):
    basename = os.path.basename(csv_path)
    match = re.match(r"(\d{4}-\d{2})-nonvisualizations\.csv", basename)
    if not match:
        print(f"Filename {basename} does not match expected pattern. Skipping.")
        return
    year_month = match.group(1)

    output_dir = os.path.join("nonvis_images", year_month)
    os.makedirs(output_dir, exist_ok=True)

    with open(csv_path, "r", newline='', encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            reddit_url = row.get("full_permalink")
            title = row.get("title", "no title")
            if reddit_url:
                print(f"\nProcessing: {title}")
                image_url = get_image_url_from_json(reddit_url)
                print(f"Extracted image URL for '{title}': {image_url}")
                if image_url:
                    filename = row.get("image_file")
                    if not filename:
                        filename = "default_image.jpg"
                    else:
                        if not os.path.splitext(filename)[1]:
                            filename += ".jpg"
                    save_path = os.path.join(output_dir, filename)
                    download_image(image_url, save_path)
                else:
                    print(f"No image URL found for post: {reddit_url}")
                time.sleep(5)
            else:
                print("No full_permalink found in row.")

def main():
    csv_files = glob.glob(os.path.join("nonvis_csv", "*-nonvisualizations.csv"))
    if not csv_files:
        print("No CSV files found in the nonvis_csv folder.")
        return

    for csv_file in csv_files:
        print(f"\nProcessing CSV file: {csv_file}...")
        process_csv_file(csv_file)

if __name__ == "__main__":
    main()
