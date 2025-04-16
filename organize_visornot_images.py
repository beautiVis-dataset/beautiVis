import os
import shutil
import csv
from pathlib import Path

def organize_images():
    base_dir = "visornot"
    vis_csv_dir = os.path.join(base_dir, "vis_csv")
    nonvis_csv_dir = os.path.join(base_dir, "nonvis_csv")
    vis_img_dir = os.path.join(base_dir, "vis_images")
    nonvis_img_dir = os.path.join(base_dir, "nonvis_images")
    downloaded_img_dir = "downloaded_images"

    os.makedirs(vis_img_dir, exist_ok=True)
    os.makedirs(nonvis_img_dir, exist_ok=True)

    for csv_type, target_dir in [("visualizations", vis_img_dir), 
                               ("nonvisualizations", nonvis_img_dir)]:
        for csv_file in Path(vis_csv_dir if csv_type == "visualizations" else nonvis_csv_dir).glob("*.csv"):
            year_month = csv_file.stem.split("-")[0] + "-" + csv_file.stem.split("-")[1]
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'image_file' not in row:
                        continue
                        
                    src_path = os.path.join(downloaded_img_dir, year_month, row['image_file'])
                    dest_folder = os.path.join(target_dir, year_month)
                    os.makedirs(dest_folder, exist_ok=True)
                    
                    try:
                        shutil.move(src_path, dest_folder)
                        print(f"Moved {row['image_file']} to {dest_folder}")
                    except FileNotFoundError:
                        print(f"Warning: Image not found at {src_path}")
                    except Exception as e:
                        print(f"Error moving {row['image_file']}: {str(e)}")

if __name__ == "__main__":
    organize_images()
    print("Image organization complete!")