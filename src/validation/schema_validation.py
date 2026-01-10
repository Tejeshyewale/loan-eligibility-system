import pandas as pd
import yaml

def load_schema(schema_path):
    with open(schema_path, "r") as file:
        schema = yaml.safe_load(file)
    return schema["columns"]

def validate_columns(df, schema_columns):
    data_columns = set(df.columns)
    schema_columns = set(schema_columns.keys())

    missing_cols = schema_columns - data_columns
    extra_cols = data_columns - schema_columns

    if missing_cols:
        raise Exception(f"❌ Missing columns: {missing_cols}")

    if extra_cols:
        raise Exception(f"❌ Unexpected columns: {extra_cols}")

    print("✅ Column name validation passed")

def validate_data_types(df, schema_columns):
    for col, expected_type in schema_columns.items():
        actual_type = df[col].dtype

        # Integer check
        if expected_type == "int":
            if not pd.api.types.is_integer_dtype(actual_type):
                raise Exception(f"❌ Column {col} should be integer")

        # Float check (accept int OR float)
        elif expected_type == "float":
            if not pd.api.types.is_numeric_dtype(actual_type):
                raise Exception(f"❌ Column {col} should be numeric (int/float)")

        # Object check
        elif expected_type == "object":
            if not pd.api.types.is_object_dtype(actual_type):
                raise Exception(f"❌ Column {col} should be object")

    print("✅ Data type validation passed")


def main():
    print("🚀 STEP 2: Schema Validation Started")

    df = pd.read_csv("data/raw/loan_approval_dataset.csv")

    # 🔑 Real-world fix: normalize column names
    df.columns = df.columns.str.strip()

    schema_columns = load_schema("config/schema.yaml")

    validate_columns(df, schema_columns)
    validate_data_types(df, schema_columns)

    print("🎉 STEP 2 COMPLETED: Schema validation successful")

if __name__ == "__main__":
    main()

