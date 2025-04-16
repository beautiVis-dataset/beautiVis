import os
import csv
import re

base_dir = os.path.join("visornot", "vis_csv")

chart_type_counts = {}

# Define corrections for known typos
corrections = {
    # "cholopleth map": "choropleth map",
    # "dotdistribution map": "dot distribution map",
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

for filename in os.listdir(base_dir):
    if filename.endswith(".csv") and "cleaned_" in filename.lower():
        csv_path = os.path.join(base_dir, filename)
        with open(csv_path, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                chart_type = row.get("cleaned_chart_type", "").strip().lower()
                chart_types = [ct.strip() for ct in re.split(r'\s*,\s*', chart_type)]
                for ct in chart_types:
                    ct = clean_chart_type(ct)
                    if ct and is_valid_chart_type(ct):
                        ct = normalize_chart_type(ct)
                        chart_type_counts[ct] = chart_type_counts.get(ct, 0) + 1

chart_type_counts = {ct.replace("other ", ""): count for ct, count in chart_type_counts.items()}

# Sort by count (descending) and then by chart type (alphabetically)
sorted_chart_types = sorted(chart_type_counts.items(), key=lambda x: (-x[1], x[0]))

for chart_type, count in sorted_chart_types:
    print(f"{chart_type}: {count}")
