import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import sys
import csv

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

# Load environment variables
load_dotenv()

# Directories
EXTRACTED_DIR = "imdb_extracted"
CLEANED_DIR = "cleaned"
os.makedirs(CLEANED_DIR, exist_ok=True)

# Table mapping and load order
TABLE_MAPPING = {
    "title.akas": "title_akas",
    "title.basics": "title_basics",
    "title.crew": "title_crew",
    "title.episode": "title_episode",
    "title.principals": "title_principals",
    "title.ratings": "title_ratings",
    "name.basics": "name_basics"
}

LOAD_ORDER = [
    "title.basics",
    "name.basics",
    "title.crew",
    "title.episode",
    "title.principals",
    "title.ratings",
    "title.akas"
]

# ------------------ Preprocessing Code ------------------

def preprocess_tsv_files():
    """Cleans TSV files and prepares them for PostgreSQL loading."""
    ARRAY_COLUMNS = {
        "title.akas": ["types", "attributes"],
        "title.basics": ["genres"],
        "title.crew": ["directors", "writers"],
        "name.basics": ["primaryProfession", "knownForTitles"]
    }

    INTEGER_COLUMNS = {
        "title.basics": ["startYear", "endYear", "runtimeMinutes"],
        "title.episode": ["seasonNumber", "episodeNumber"],
        "title.ratings": ["numVotes"]
    }

    # Load title.basics to get valid tconst values
    title_basics_path = os.path.join(EXTRACTED_DIR, "title.basics.tsv")
    title_df = pd.read_csv(title_basics_path, sep="\t", dtype=str, na_values=r"\N", encoding="utf-8")
    valid_tconsts = set(title_df["tconst"].dropna().unique())

    # Load name.basics to get valid nconst values
    name_basics_path = os.path.join(EXTRACTED_DIR, "name.basics.tsv")
    name_df = pd.read_csv(name_basics_path, sep="\t", dtype=str, na_values=r"\N", encoding="utf-8")
    valid_nconsts = set(name_df["nconst"].dropna().unique())

    tsv_files = [f for f in os.listdir(EXTRACTED_DIR) if f.endswith(".tsv")]
    
    for file in tsv_files:
        input_path = os.path.join(EXTRACTED_DIR, file)
        key = file.replace(".tsv", "")
        print(f"Processing {key}...")

        try:
            # Read TSV with proper null handling
            df = pd.read_csv(
                input_path, sep="\t", dtype=str, 
                na_values=r"\N", encoding="utf-8", 
                on_bad_lines="warn"
            )
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

        # ---- Data Cleaning ----
        # Convert integer columns
        if key in INTEGER_COLUMNS:
            for col in INTEGER_COLUMNS[key]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

        # Process array columns
        if key in ARRAY_COLUMNS:
            for col in ARRAY_COLUMNS[key]:
                if col in df.columns:
                    df[col] = df[col].apply(
                        lambda x: f"{{{','.join(s.strip() for s in str(x).split(','))}}}" 
                        if pd.notnull(x) and str(x).strip() != "" 
                        else None
                    )

        # Handle specific tables
        if key == "title.basics":
            # Ensure required columns are populated
            df["primaryTitle"] = df["primaryTitle"].replace('', "Unknown Title").fillna("Unknown Title")
            df["originalTitle"] = df["originalTitle"].replace('', "Unknown Title").fillna(df["primaryTitle"])
            # Convert boolean
            df["isAdult"] = df["isAdult"].map({"0": "f", "1": "t"}).fillna("f")

        if key == "name.basics":
            df["primaryName"] = df["primaryName"].replace('', "Unknown").fillna("Unknown")
            # Fix array columns if empty
            for col in ["primaryProfession", "knownForTitles"]:
                df[col] = df[col].fillna("{}")

        if key == "title.akas":
            df["title"] = df["title"].replace('', "Unknown Title").fillna("Unknown Title")
            # Filter invalid titleId (tconst)
            df = df[df["titleId"].isin(valid_tconsts)]

        if key == "title.principals":
            # Filter invalid tconst and nconst
            df = df[df["tconst"].isin(valid_tconsts) & df["nconst"].isin(valid_nconsts)]

        # Save cleaned file
        output_path = os.path.join(CLEANED_DIR, file)
        df.to_csv(output_path, sep="\t", index=False, na_rep=r"\N", encoding="utf-8")
        print(f"✅ Saved cleaned {key} ({len(df):,} rows)")

# ------------------ Loading Code ------------------

def get_connection():
    """Returns a PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def load_tsv_to_postgres():
    """Loads cleaned TSV files into PostgreSQL."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for key in LOAD_ORDER:
            table_name = TABLE_MAPPING.get(key)
            file_path = os.path.join(CLEANED_DIR, f"{key}.tsv")

            print(f"Loading {table_name}...")

            # Start a transaction block
            conn.autocommit = False  # Disable autocommit

            try:
                cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
                with open(file_path, 'r', encoding="utf-8") as f:
                    cursor.copy_expert(
                        f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N', HEADER)",
                        f
                    )
                conn.commit()  # Commit only if both TRUNCATE and COPY succeed
                print(f"✅ Loaded {table_name}")
            except Exception as e:
                conn.rollback()  # Rollback TRUNCATE if COPY fails
                print(f"❌ Failed to load {table_name}: {e}")

    finally:
        conn.autocommit = True  # Re-enable autocommit
        cursor.close()
        conn.close()
        print("🎉 Database loading complete!")

# ------------------ Main Execution ------------------

if __name__ == "__main__":
    print("🚀 Starting preprocessing of TSV files...")
    preprocess_tsv_files()
    print("\n✅ Preprocessing complete. Starting data load to PostgreSQL...")
    load_tsv_to_postgres()