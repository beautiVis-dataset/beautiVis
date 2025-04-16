from openai import OpenAI
import os
import base64
import time
import csv
import argparse
import json
import re


def load_api_key(key_number: int) -> str:
    key_file = f"key{key_number}.txt"
    try:
        with open(key_file, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: API key file '{key_file}' not found.")
        return ""

def load_prompt():
    with open("prompt.txt", "r", encoding="utf-8") as file:
        return file.read().strip()

def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def prepare_batch_input(folder_path, image_files, output_file, prompt):
    """Prepare batch input for a set of images from downloaded_images folder"""
    folder_name = os.path.basename(folder_path)
    year_month = folder_name
    
    csv_file = os.path.join("downloaded_csv", f"{year_month}-downloaded.csv")
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} not found. Skipping batch preparation.")
        return

    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    with open(output_file, "w") as f:
        for filename in image_files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                matching_row = next((row for row in rows if row.get("image_file") == filename), None)
                if not matching_row:
                    print(f"No matching CSV row found for {filename}. Skipping.")
                    continue

                title = matching_row.get("title", "")
                updated_prompt = prompt.format(title=title)

                image_path = os.path.join(folder_path, filename)
                base64_image = encode_image(image_path)
                if base64_image is None:
                    print(f"Skipping image {filename} due to encoding error.")
                    continue

                request = {
                    "custom_id": f"request-{filename}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4o",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": updated_prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            }
                        ],
                        "max_tokens": 300
                    }
                }
                f.write(json.dumps(request) + "\n")

def update_csv_row(image_filename, chart_type, high_level_categories, folder_path):
    """Update the CSV with classification results"""
    folder_name = os.path.basename(folder_path)
    year_month = folder_name
    
    csv_file = os.path.join("downloaded_csv", f"{year_month}-downloaded.csv")
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} not found. Skipping CSV update for {image_filename}")
        return

    vis_csv_folder = os.path.join("visornot", "vis_csv")
    nonvis_csv_folder = os.path.join("visornot", "nonvis_csv")
    os.makedirs(vis_csv_folder, exist_ok=True)
    os.makedirs(nonvis_csv_folder, exist_ok=True)

    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if "chart_type" not in fieldnames:
        fieldnames.append("chart_type")
    if "high_level_categories" not in fieldnames:
        fieldnames.append("high_level_categories")

    matching_row = next((row for row in rows if row.get("image_file") == image_filename), None)

    if matching_row:
        if chart_type and chart_type != "none":
            matching_row["chart_type"] = chart_type
            matching_row["high_level_categories"] = ", ".join(high_level_categories) if high_level_categories else "none"
            output_folder = vis_csv_folder
            output_suffix = "visualizations"
        else:
            matching_row["chart_type"] = "none"
            matching_row["high_level_categories"] = "none"
            output_folder = nonvis_csv_folder
            output_suffix = "nonvisualizations"

        output_csv = os.path.join(output_folder, f"{year_month}-{output_suffix}.csv")
        file_exists = os.path.exists(output_csv)

        with open(output_csv, mode="a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(matching_row)

        print(f"Updated CSV for {image_filename} in {output_csv}")
    else:
        print(f"No matching CSV row found for {image_filename} in {csv_file}")

def process_batch_results(output_file, folder_path):
    """Process the results from the batch API call"""
    with open(output_file, "r") as f:
        for line in f:
            result = json.loads(line)
            custom_id = result["custom_id"]
            response = result["response"]["body"]
            
            if "choices" not in response or not response["choices"]:
                print(f"Skipping {custom_id}: No valid response from API.")
                continue 

            response_content = response["choices"][0]["message"]["content"].strip().lower()
            response_parts = response_content.split(";")
            if len(response_parts) != 2:
                print(f"Skipping {custom_id}: Invalid response format. Expected 'chart_type; high_level_categories'.")
                continue

            chart_type = response_parts[0].strip()
            high_level_categories = [kw.strip() for kw in response_parts[1].split(",") if kw.strip()]
            image_filename = custom_id.replace("request-", "")

            update_csv_row(image_filename, chart_type, high_level_categories, folder_path)

def folder_in_range(folder_name, start_range, end_range):
    """Check if folder is within specified date range"""
    return start_range <= folder_name <= end_range

def clear_output_csvs(folder_name):
    """Clear existing output CSV files for a given month"""
    vis_csv_folder = os.path.join("visornot", "vis_csv")
    nonvis_csv_folder = os.path.join("visornot", "nonvis_csv")
    os.makedirs(vis_csv_folder, exist_ok=True)
    os.makedirs(nonvis_csv_folder, exist_ok=True)

    output_csv_vis = os.path.join(vis_csv_folder, f"{folder_name}-visualizations.csv")
    output_csv_nonvis = os.path.join(nonvis_csv_folder, f"{folder_name}-nonvisualizations.csv")

    # Clear existing files
    for output_csv in [output_csv_vis, output_csv_nonvis]:
        if os.path.exists(output_csv):
            os.remove(output_csv)

def process_folders(start_range, end_range, prompt):
    """Process all folders in downloaded_images within date range"""
    input_folder = "downloaded_images"
    subfolders = [item for item in os.listdir(input_folder) 
                 if os.path.isdir(os.path.join(input_folder, item)) and re.match(r"\d{4}-\d{2}", item)]
    subfolders.sort()

    for folder_name in subfolders:
        if folder_in_range(folder_name, start_range, end_range):
            print(f"\nProcessing folder: {folder_name}")
            clear_output_csvs(folder_name)
            
            folder_path = os.path.join(input_folder, folder_name)
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            image_files.sort()

            batch_size = 50
            for i in range(0, len(image_files), batch_size):
                batch_files = image_files[i:i + batch_size]
                print(f"Processing batch {i // batch_size + 1} with {len(batch_files)} images.")

                batch_input_file = os.path.join(folder_path, f"batch_input_{i // batch_size + 1}.jsonl")
                prepare_batch_input(folder_path, batch_files, batch_input_file, prompt)

                with open(batch_input_file, "rb") as f:
                    file = client.files.create(file=f, purpose="batch")

                batch = client.batches.create(
                    input_file_id=file.id,
                    endpoint="/v1/chat/completions",
                    completion_window="24h"
                )

                print(f"Batch created. Batch ID: {batch.id}")

                retry_count = 0
                max_retries = 10
                timeout = 60 * 60
                start_time = time.time()

                while True:
                    batch_status = client.batches.retrieve(batch.id)
                    if batch_status.status == "completed":
                        break
                    elif batch_status.status == "failed":
                        retry_count += 1
                        if retry_count > max_retries:
                            print(f"Batch failed after {max_retries} retries. Skipping.")
                            break
                        print(f"Batch failed. Retrying ({retry_count}/{max_retries})...")
                        time.sleep(300)
                        with open(batch_input_file, "rb") as f:
                            file = client.files.create(file=f, purpose="batch")
                        batch = client.batches.create(
                            input_file_id=file.id,
                            endpoint="/v1/chat/completions",
                            completion_window="24h"
                        )
                    elif time.time() - start_time > timeout:
                        print("Batch taking too long. Cancelling and retrying...")
                        client.batches.cancel(batch.id)
                        time.sleep(60)
                        with open(batch_input_file, "rb") as f:
                            file = client.files.create(file=f, purpose="batch")
                        batch = client.batches.create(
                            input_file_id=file.id,
                            endpoint="/v1/chat/completions",
                            completion_window="24h"
                        )
                        start_time = time.time()
                    else:
                        print(f"Batch status: {batch_status.status}. Waiting...")
                        time.sleep(30)

                if batch_status.status == "completed":
                    output_file_id = batch_status.output_file_id
                    output_file = client.files.content(output_file_id)

                    batch_output_file = os.path.join(folder_path, f"batch_output_{i // batch_size + 1}.jsonl")
                    with open(batch_output_file, "wb") as f:
                        f.write(output_file.read())

                    process_batch_results(batch_output_file, folder_path)
        else:
            print(f"Skipping folder {folder_name} (outside range {start_range} to {end_range})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categorize images from downloaded_images folder.")
    parser.add_argument("--start", required=True, help="Start range in yyyy-mm format.")
    parser.add_argument("--end", required=True, help="End range in yyyy-mm format.")
    parser.add_argument("--key", required=True, choices=["1", "2", "3"], help="API key file to use.")
    args = parser.parse_args()

    api_key = load_api_key(int(args.key))
    if not api_key:
        exit(1)

    prompt = load_prompt()
    if not prompt:
        exit(1)

    client = OpenAI(api_key=api_key)
    process_folders(args.start, args.end, prompt)
    print("Processing complete.")

    # python visornot_gpt.py --start 2012-02 --end 2012-03 --key 1