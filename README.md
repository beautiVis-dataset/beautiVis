# beautiVis

## About the Dataset

beautiVis is a richly annotated dataset of 50,000+ static images sourced from Reddit's _r/dataisbeautiful_ subreddit between February 2012 and January 2025. The dataset was built through a three-phase pipeline:

**Phase 1: Data Collection**  
First, we downloaded the complete post history from _r/dataisbeautiful_ using the [Arctic-Shift Reddit Download Tool](https://arctic-shift.photon-reddit.com/download-tool), which provided raw JSON data containing post metadata, titles, and image URLs. During this initial phase, we automatically filtered out any posts that had been deleted by users or removed by moderators. The remaining post metadata were saved to CSV files organized by monthly batches (yyyy-mm).

**Phase 2: Data Processing and Metadata Structuring**  
From the remaining posts, we identified static visualization images (PNG/JPG) while excluding animated or non-visual content. Each valid image was downloaded and systematically named using the yyyy-mm-nnnn format, where:
- yyyy-mm represents the year and month of the post
- nnnn is a zero-padded sequential identifier unique within each month

These images were then organized into corresponding yyyy-mm directories, creating both a temporally structured archive and a consistent naming scheme for images and their source metadata. This also ensured precise tracking of each visualization back to its original post and efficient batch processing in Phase 3.

**Phase 3: Automated Labeling with ChatGPT API**  
We processed each image through OpenAI's GPT-4o model via their Batch API. For each submission, we provided: the image itself, the original post title, and a detailed prompt designed to classify chart types and extract topical information. For images with identified chart types (classified as "vis"), we saved their metadata to vis_csv folders in CSV files named with year and month notation (e.g., vis_csv/2024-01-visualizations.csv), while moving the corresponding image files to vis_images folders organized by year and month (e.g., vis_images/2024-01/2024-01-0001.png). Content without any identified chart types (classified as "nonvis") were similarly organized, with metadata saved to nonvis_csv files (e.g., nonvis_csv/2024-01-nonvisualizations.csv) and images stored in corresponding nonvis_images subfolders (e.g., nonvis_images/2024-01/2024-01-0002.png). This structure enables direct cross-referencing while preserving temporal relationships for analysis.

The automated labeling initially produced over 600 distinct chart types. We consolidated these into 12 standardized MASSVIS categories (Bar, Line, Maps, Point, Diagrams, Circle, Area, Grid & Matrix, Distribution, Table, Text, Trees & Networks, plus Other). This normalization supports: (1) statistically robust comparisons by reducing category sparsity, (2) alignment with human perceptual patterns, and (3) direct benchmarking against prior visualization research. We implemented this by having ChatGPT map the over 600 types to MASSVIS categories using the MASSVIS taxonomy documentation.

## Dataset Structure and Access

### combined_csv and combined_images  
The `combined_csv` folder contains raw monthly CSV files (e.g., `2012-02-combined.csv`) preserving the original Reddit metadata before any AI processing. These files include the following columns:  
- `title`: Original post title  
- `author`: Reddit username of submitter  
- `created_date`: Timestamp of submission  
- `url`: Direct link to hosted image  
- `full_permalink`: Reddit post URL  
- `score`: Net upvote count  
- `ups`: Total upvotes  
- `downs`: Total downvotes  
- `num_comments`: Comment count  
- `sanitized_title`: Cleaned version of title  
- `image_file`: Corresponding image filename in `yyyy-mm-nnnn` format  

The complete image collection is available as `combined_images.zip` in our [Hugging Face repository](https://huggingface.co/datasets/beautiVis/beautiVis).

### vis_csv and vis_images  
The `vis_csv` folder contains GPT-annotated monthly files (e.g., `2012-02-visualizations.csv`) for verified visualizations, with these additional columns:  
- `json_title`: Original post title  
- `json_author`: Reddit username of submitter  
- `json_created_date`: Timestamp of submission  
- `json_url`: Direct link to hosted image  
- `json_full_permalink`: Reddit post URL  
- `json_score`: Net upvote count  
- `json_ups`: Total upvotes  
- `json_downs`: Total downvotes  
- `json_num_comments`: Comment count  
- `pp_sanitized_title`: Cleaned version of title  
- `pp_image_file`: Corresponding image filename in `yyyy-mm-nnnn` format  
- `gpt_chart_type`: Outputed list of chart types by GPT
- `gpt_high_level_categories`: Outputed list of topics by GPT
- `gpt_cleaned_chart_type`: Cleaned and standardized list of chart types 
- `gpt_overarching_chart_type`: MASSVIS category (e.g. "Bar")

The complete vis collection is available as `vis_images.zip` in our [Hugging Face repository](https://huggingface.co/datasets/beautiVis/beautiVis).

### nonvis_csv and nonvis_images  
The `nonvis_csv` folder contains monthly files (e.g., `2012-02-nonvisualizations.csv`) for excluded content, featuring:  
- All base metadata columns from `combined_csv`  
- `chart_type`: GPT-4o's classification rationale (all of which are 'none')  
- `high_level_categories`: Detected non-visual topics  

The complete nonvis collection is available as `nonvis_images.zip` in our [Hugging Face repository](https://huggingface.co/datasets/beautiVis/beautiVis).
