import csv
import json
import pandas as pd
from src.paths import MANIFEST_PATH, PROCESSED_DATA_DIR
from pathlib import Path
import re 

manifest = json.loads(MANIFEST_PATH.read_text())

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

datasets = ["selener", "bitext"]

selener_path = Path(manifest["selener/consumer-complaint-database"]) / "rows.csv"
bitext_path = Path(manifest["bitext/bitext-gen-ai-chatbot-customer-support-dataset"]) / "Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"

selener_output = PROCESSED_DATA_DIR / "selener.parquet"
bitext_output = PROCESSED_DATA_DIR / "bitext.parquet"

sel_df = pd.read_csv(selener_path)
bit_df = pd.read_csv(bitext_path)

sel_df.to_parquet(selener_output)
print(f"saved selener to: {selener_output}")
bit_df.to_parquet(bitext_output)
print(f"saved bitext to: {bitext_output}")

