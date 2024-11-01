#!/bin/bash

# Initialize Conda
source "$(conda info --base)/etc/profile.d/conda.sh"

# Your existing script commands
rm -f data/api/*
conda deactivate 
conda activate ica
cd workflow
snakemake --cores 1
cd ..
cd mongodb
conda deactivate
conda activate farm
python3 upload_data.py
cd ..
cd fastapi
fastapi dev main.py
