import os
import gzip
import shutil


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


if __name__ == "__main__":
    extract_tsv_gz()
