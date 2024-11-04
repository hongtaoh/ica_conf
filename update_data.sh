#!/bin/bash

# Initialize Conda
source "$(conda info --base)/etc/profile.d/conda.sh"

# rm -f data/processed/*
# rm -f data/api/*
# conda activate ica
# cd workflow
# snakemake --cores 1
# cd ..
cd mongodb
python3 upload_data.py
cd ..
# cd fastapi
# fastapi dev main.py
