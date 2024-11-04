#!/bin/bash

# Initialize Conda
source "$(conda info --base)/etc/profile.d/conda.sh"

rm -f data/api/paper_embeddings.json
rm -f fastapi/pca_model.pkl
conda activate ica
cd workflow
snakemake --cores 1
cd ..
cd mongodb
python3 main.py
cd ..
cd fastapi
fastapi dev main.py
