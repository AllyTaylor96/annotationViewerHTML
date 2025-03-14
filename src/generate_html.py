import re
from pprint import pprint

from airium import Airium

from io_functions import load_json

# Load HTML colours
html_colour_list = load_json('src/colours.json')['html_colour_list']

def sort_entities(entities: dict, total_entities: list) -> list:
    """
    Sort entities by their average position in the transcript.
    """
    entity_positions = {}
    for entity_name in total_entities:
        start_word_indexes = [x['startWordIndex'] for x in entities if x['id'] == entity_name]
        entity_positions[entity_name] = sum(start_word_indexes) / len(start_word_indexes)

    # Return a list of entities sorted by their average position in the transcript
    sorted_entities = sorted(entity_positions, key=entity_positions.get)
    return sorted_entities

def process_annotations(words: list) -> list:
    """
    Process annotations and insert <span> tags into transcript.
    """

    processed_words = []
    active_annotations = set()
    for word_idx, word in enumerate(words):
        word_annotations = set(word['annotations'])

        if word_annotations:

            annotation_name = '-'.join(list(word_annotations))
            processed_words.append({
                'wordIdx': None,
                'text': f"<span class='entity {annotation_name}'>",
                'startTime': words[word_idx - 1]['endTime'] if word_idx > 0 else word['startTime'],
                'endTime': word['startTime'],
                'speaker': words[word_idx]['speaker'] if word_idx > 0 else word['speaker'],
                'annotations': []
            })

            # Add actual word
            processed_words.append(word)

            # Insert </span> tags for turning off annotations
            processed_words.append({
                'wordIdx': None,
                'text': "</span>",
                'startTime': word['endTime'],
                'endTime': words[word_idx + 1]['startTime'] if word_idx + 1 < len(words) else word['endTime'],
                'speaker': word['speaker'],
                'annotations': []
            })
        else:
            processed_words.append(word)

    return processed_words

def divide_transcript_into_phrases(words: list) -> list:
    """
    Divide transcript into phrases based on speaker changes.
    """

    phrases = []
    current_speaker = None
    current_phrase = {
        'speaker': None,
        'text': "",
        'startTime': None,
        'endTime': None
    }

    for word in words:

        if word['speaker'] != current_speaker:
            if current_phrase['speaker'] is not None:
                phrases.append(current_phrase)

            phrases.append({
                'speaker': word['speaker'],
                'text': f"<span class='speaker'>{word['startTime']} - {word['endTime']} - {word['speaker']}:</span>\n",
                'startTime': word['startTime'],
                'endTime': word['endTime']
            })

            current_speaker = word['speaker']
            current_phrase = {
                'speaker': word['speaker'],
                'text': "",
                'startTime': word['startTime'],
                'endTime': word['endTime']
            }
        
        current_phrase['text'] += word['text'] + " "

    phrases.append(current_phrase)

    for phrase in phrases:
        phrase['text'] = merge_adjacent_spans(phrase['text'])

    return phrases

def merge_adjacent_spans(text: str):
    """
    Merges adjacent HTML spans with the same entity class in a given text.
    """
    span_pattern = re.compile(r"(<span class='entity (\w+)'>)(.*?)(</span>)")  # Match spans
    matches = span_pattern.findall(text)

    if not matches:
        return text  # If no spans, return original text

    merged_text = []
    last_entity = None
    buffer = ""

    for open_tag, entity, content, close_tag in matches:
        if entity == last_entity:
            buffer += " " + content  # Merge adjacent same entity spans
        else:
            if buffer:  # Append previous buffered span
                merged_text.append(f"<span class='entity {last_entity}'>{buffer}</span>")
            last_entity = entity
            buffer = content

    if buffer:  # Append last span
        merged_text.append(f"<span class='entity {last_entity}'>{buffer}</span>")

    # Replace original spans with merged spans
    cleaned_text = span_pattern.sub("", text)  # Remove all original spans
    reconstructed_text = cleaned_text.strip() + " " + " ".join(merged_text) # Add merged spans back
    return re.sub(r'\s+', ' ', reconstructed_text).strip()

def generate_html(file_id: str, transcript: dict, entities: dict) -> str:
    """
    Generate an HTML file with interactive Named Entity Recognition (NER) highlights.
    """

    words = transcript['words']
    annotated_words = [x for x in words[:]]  # Copy words list

    for word in annotated_words:
        word['annotations'] = []

    sorted_annotations = sorted(entities['annotations'], key=lambda x: x['startWordIndex'], reverse=True)

    # add annotations onto the words
    for annotation in sorted_annotations:
        annotation_range = range(annotation['startWordIndex'], annotation['endWordIndex']+1)
        for word_idx in annotation_range:
            annotated_words[word_idx]['annotations'].append(annotation['id'])

    # Insert <span> tags for annotations based on word positions
    processed_words = process_annotations(annotated_words)

    phrases = divide_transcript_into_phrases(processed_words)

    # Roughly-sort the entities by their average position in the transcript
    sorted_annotations = sort_entities(entities['annotations'], entities['metadata']['ids'])

    # Get all entity IDs and assign colours
    # Probably need to add a check for if the entity is not in the list of colours
    entity_colours = {}
    for i, entity_id in enumerate(sorted_annotations):
        entity_colours[entity_id] = html_colour_list[i % len(html_colour_list)]


    # Generate HTML using Airium
    a = Airium()

    a('<!DOCTYPE html>')
    with a.html():
        with a.head():
            a.meta(charset="utf-8")
            a.title(_t=file_id)
            with a.style():
                a("""
                .entity {
                    padding: 2px;
                    border-radius: 3px;
                    transition: background-color 1.0s ease;
                }
                """)
                for entity_id in sorted_annotations:
                    a(f"""
                    .entity.{entity_id} {{
                        background-color: {entity_colours[entity_id]};
                    }}
                    """)

                a("""
                  .no-highlight {
                    background-color: transparent !important;
                }
                  .speaker {
                    font-weight: bold;
                    display: inline;
                    margin-top: 5px;
                    background-color: transparent !important;
                    pointer-events: none
                """)

        with a.body():
            with a.h1(id="MainTitle", klass="main_header"):
                a(f"{file_id}: NER Highlighting")
            with a.div():
                for entity_id in sorted_annotations:
                    a.input(id=f"toggle-{entity_id}", type="checkbox", checked=True)
                    with a.label(id=f"label-{entity_id}", **{"for": f"toggle-{entity_id}"}, style=f"background-color: {entity_colours[entity_id]};"):
                        a(f" {entity_id} ")
                        a.br()
            
            with a.div(id="transcript"):
                current_speaker = None
                for phrase in phrases:
                    phrase_text = phrase['text']
                    a(phrase_text)
                    a.br()
                    if "class='speaker'" not in phrase_text:
                        a.br()

            for entity_id in sorted_annotations:
                with a.script():
                    a(f"""
                    document.getElementById("toggle-{entity_id}").addEventListener("change", function() {{
                        const elements = document.querySelectorAll(".{entity_id}");
                        elements.forEach(el => {{
                            if (!el.classList.contains("speaker")) {{ // Prevent speaker spans from being affected
                                if (this.checked) {{
                                    el.classList.remove("no-highlight");
                                }} else {{
                                    el.classList.add("no-highlight");
                                }}
                            }}
                        }});
                    }});
                    """)
    return str(a)

def save_static_html(output_filepath: str, html_content: str) -> None:
    """
    Generate and save a static HTML file.
    """
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
