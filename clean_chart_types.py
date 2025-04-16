import os
import csv
import re

base_dir = os.path.join("visornot", "vis_csv")

# Define corrections for known typos and other fixes
corrections = {
    # "cholopleth map": "choropleth map",
    # "dotdistribution map": "dot distribution map",
    # "line chart": "line graph",
}

# Define a regex to capture valid chart type indicators (e.g., chart, plot, map, etc.)
valid_keywords = r"\b(chart(?:s)?|plot(?:s)?|map(?:s)?|diagram(?:s)?|visualization(?:s)?|graph(?:s)?|heatmap(?:s)?|histogram(?:s)?)\b"

def is_valid_chart_type(chart_type):
    matches = re.findall(valid_keywords, chart_type.lower())
    unique_matches = set(matches)
    if not unique_matches:
        return False
    if len(unique_matches) > 1:
        return False
    return True

def clean_chart_type(chart_type):
    chart_type = re.sub(r'[\'\"\(\)\[\]\-’‘]', '', chart_type)
    chart_type = re.sub(r'\s+', ' ', chart_type).strip()
    return chart_type

def normalize_chart_type(chart_type):
    ct = chart_type.lower()
    if ct.startswith("other "):
        ct = ct[len("other "):].strip()
    if ct in corrections:
        ct = corrections[ct]
    return ct

def process_chart_type(chart_type):
    chart_types = [ct.strip() for ct in re.split(r'\s*,\s*', chart_type)]
    cleaned_types = []
    for ct in chart_types:
        ct = clean_chart_type(ct)
        if ct and is_valid_chart_type(ct):
            ct = normalize_chart_type(ct)
            cleaned_types.append(ct)
    return ", ".join(cleaned_types) if cleaned_types else ""

for filename in os.listdir(base_dir):
    if filename.endswith(".csv") and "-vis" in filename.lower():
        csv_path = os.path.join(base_dir, filename)
        output_csv_path = os.path.join(base_dir, f"cleaned_{filename}")

        with open(csv_path, "r", encoding="utf-8") as csv_file, \
             open(output_csv_path, "w", encoding="utf-8", newline="") as output_csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames + ["cleaned_chart_type"]
            writer = csv.DictWriter(output_csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for row in reader:
                chart_type = row.get("chart_type", "").strip().lower()
                cleaned_chart_type = process_chart_type(chart_type)
                row["cleaned_chart_type"] = cleaned_chart_type
                writer.writerow(row)

print("Processing complete. Cleaned CSV files have been saved.")
