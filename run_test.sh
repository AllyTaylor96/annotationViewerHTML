#!/bin/bash

source env/bin/activate

python3 src/create_html.py \
	--transcript_file "${PWD}/test_files/in/techpod-259-hey-google-its-time-for-bed.json" \
	--annotation_file "${PWD}/test_files/in/annotations.json" \
	--output_dir "${PWD}/test_files/out"
deactivate
