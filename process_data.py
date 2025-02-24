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
            df["primaryTitle"] = df["primaryTitle"].fillna("Unknown Title")
            df["originalTitle"] = df["originalTitle"].fillna(df["primaryTitle"])
            # Convert boolean
            df["isAdult"] = df["isAdult"].map({"0": "f", "1": "t"}).fillna("f")

        if key == "name.basics":
            df["primaryName"] = df["primaryName"].fillna("Unknown")
            # Fix array columns if empty
            for col in ["primaryProfession", "knownForTitles"]:
                df[col] = df[col].fillna("{}")

        if key == "title.akas":
            df["title"] = df["title"].fillna("Unknown Title")

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
            table = TABLE_MAPPING[key]
            tsv_path = os.path.join(CLEANED_DIR, f"{key}.tsv")
            
            print(f"\n⏳ Loading {table}...")
            
            # Truncate table
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
            
            # Load data
            with open(tsv_path, "r", encoding="utf-8") as f:
                cursor.copy_expert(
                    f"COPY {table} FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N', HEADER)",
                    f
                )
            print(f"✅ Loaded {table}")

        # Validate foreign keys
        print("\n🔍 Validating foreign keys...")
        for table, fk_column in [
            ("title_akas", "titleId"),
            ("title_crew", "tconst"),
            ("title_episode", "parentTconst"),
            ("title_principals", "tconst"),
            ("title_ratings", "tconst")
        ]:
            cursor.execute(f"""
                DELETE FROM {table}
                WHERE {fk_column} NOT IN (SELECT tconst FROM title_basics);
            """)
            print(f"  - Cleaned orphaned rows in {table}")

        conn.commit()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("\n🎉 Database loading complete!")

# ------------------ Main Execution ------------------

if __name__ == "__main__":
    print("🚀 Starting preprocessing of TSV files...")
    preprocess_tsv_files()
    print("\n✅ Preprocessing complete. Starting data load to PostgreSQL...")
    load_tsv_to_postgres()