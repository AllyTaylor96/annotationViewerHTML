import argparse
import logging
import os
from pathlib import Path

from io_functions import load_json, write_json
from generate_html import generate_html, save_static_html

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create a HTML displaying annotations on text.')
    parser.add_argument('--transcript_file', '-t', help='Path to a transcript file', required=True)
    parser.add_argument('--annotation_file', '-a', help='Path to an annotation file', required=True)
    parser.add_argument('--output_dir', '-o', help='Path to the output directory', required=True)

    args = parser.parse_args()

    return args

def configure_logging() -> logging.Logger:
    """Sets up a useful logger."""

    # create project-specific logger
    logger = logging.getLogger('htmlCreator')
    logger.setLevel(logging.DEBUG)

    # set up logger to output to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # set up console to output to log file
    file_handler = logging.FileHandler(f'{os.getcwd()}/logs/create_html.log',
                                      mode = 'w')
    file_handler.setLevel(logging.DEBUG)

    # set up log formatting
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # add specific handlers to the main logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def main():

    logger = configure_logging()
    args = parse_args()

    logger.info('Loading transcript and annotations...')
    logger.debug(f'Transcript file: {args.transcript_file}')
    logger.debug(f'Annotation file: {args.annotation_file}')

    file_id = args.transcript_file.split('/')[-1].split('.')[0]
    logger.info(f'File ID: {file_id}')

    transcript = load_json(args.transcript_file)
    entities = load_json(args.annotation_file)

    logger.info(f'Creating the HTML file...')
    generated_html = generate_html(file_id, transcript, entities)

    output_filepath = Path(args.output_dir) / 'annotated_transcript.html'
    save_static_html(output_filepath, generated_html)

    logger.info(f'HTML file saved to: {output_filepath}')

if __name__ == "__main__":
    main()
