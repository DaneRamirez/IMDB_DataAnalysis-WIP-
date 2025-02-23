import requests
import os
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine 

#db connection. 
#use own credentials in .env file
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)


def load_tsv_df(input_folder="imdb_extracted"):

    dataframes={}

    tsv_files= [f for f in os.listdir(input_folder) if f.endswith(".tsv")]

    for tsvfile in tsv_files:
        filepath= os.path.join(input_folder, tsvfile)

        #read tsv file into dataframe
        df=pd.read_csv(filepath, sep="\t", na_values="\\n", dtype=str)

        table_name= tsvfile.replace(".tsv", "")

        dataframes[table_name]=df

        print(f"Loaded {tsvfile} to Dataframe with {len(df)} rows.")

    return dataframes

# # Load all extracted IMDb .tsv files into DataFrames
# imdb_data = load_tsv_df()
# #test case
# print(imdb_data["title.basics"].head())

