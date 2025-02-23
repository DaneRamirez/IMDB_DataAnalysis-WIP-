import requests
import os


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


if __name__ == "__main__":
    for link in links:
        download_files(links)
