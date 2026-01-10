import os
import pandas as pd
from datetime import datetime

RAW_DATA_PATH = "data/raw/loan_approval_dataset.csv"

def check_file_exists(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found at {file_path}")

def load_raw_data(file_path):
    return pd.read_csv(file_path)

def log_ingestion(df):
    print("----- DATA INGESTION LOG -----")
    print(f"Ingestion Time : {datetime.now()}")
    print(f"Total Records  : {df.shape[0]}")
    print(f"Total Columns  : {df.shape[1]}")

def main():
    check_file_exists(RAW_DATA_PATH)
    df = load_raw_data(RAW_DATA_PATH)
    log_ingestion(df)
    print(df.head())

if __name__ == "__main__":
    main()
