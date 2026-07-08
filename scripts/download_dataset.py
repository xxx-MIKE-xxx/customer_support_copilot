# Install dependencies as needed:
# pip install kagglehub[hf-datasets]
import kagglehub
from kagglehub import KaggleDatasetAdapter
from src.paths import MANIFEST_PATH
import json
# Download latest version
paths = ["selener/consumer-complaint-database", "bitext/bitext-gen-ai-chatbot-customer-support-dataset",]
manifest = {}
for i in paths:
    path = kagglehub.dataset_download(i)
    print("Path to dataset files:", path)
    manifest[i] = path

MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
print(f"wrote manifest to: {MANIFEST_PATH}")
