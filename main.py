import requests
import os
import pandas as pd
import gzip
import shutil
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
#List of links from https://developer.imdb.com/non-commercial-datasets/

links=["https://datasets.imdbws.com/name.basics.tsv.gz",
        "https://datasets.imdbws.com/title.akas.tsv.gz",
        "https://datasets.imdbws.com/title.basics.tsv.gz",
        "https://datasets.imdbws.com/title.crew.tsv.gz",
        "https://datasets.imdbws.com/title.episode.tsv.gz",
        "https://datasets.imdbws.com/title.principals.tsv.gz",
        "https://datasets.imdbws.com/title.ratings.tsv.gz"
        ]

def download_files(url, output_folder="imdb_data"):
    #just makes sure output folder exists yk
    os.makedirs(output_folder, exist_ok=True)

    #urlk filename extractiion
    filename= url.split("/")[-1]
    output_path= os.path.join(output_folder,filename)

    response= requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            #chunk seperation into 1kb aka incremental downloads
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download: {filename}")

#for early development, downloading is off
# for link in links:
#     download_files(link)


def extract_tsv_gz(input_folder="imdb_data", output_folder="imdb_extracted"): 

    #for outputfolder
    os.makedirs(output_folder, exist_ok=True)

    #uses os module to iterate through and lists those that end with .gz
    gz_files = [f for f in os.listdir(input_folder) if f.endswith(".gz")]
    
    for file in gz_files:
        input_path= os.path.join(input_folder, file)
        output_path = os.path.join(output_folder, file.replace(".gz", "")) #removes .gz

        with gzip.open (input_path,'rb') as f_in, open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        print(f"Extracted: {file} → {output_path}")

#commented to disable extraction per test case     
# extract_tsv_gz()

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

