from io_functions import load_json

from airium import Airium

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
        new_annotations = set(word['annotations'])
        turning_on = new_annotations - active_annotations
        turning_off = active_annotations - new_annotations

        # Insert <span> tags for turning on annotations
        if turning_on:
            for annotation in turning_on:
                processed_words.append({
                    'wordIdx': None,
                    'text': f"<span class='entity {annotation}'>",
                    'startTime': words[word_idx - 1]['endTime'] if word_idx > 0 else word['startTime'],
                    'endTime': word['startTime'],
                    'speaker': words[word_idx]['speaker'] if word_idx > 0 else word['speaker'],
                    'annotations': []
                })
        
        # Add actual word
        processed_words.append(word)

        # Insert </span> tags for turning off annotations
        if turning_off:
            for annotation in turning_off:
                processed_words.append({
                    'wordIdx': None,
                    'text': "</span>",
                    'startTime': word['endTime'],
                    'endTime': words[word_idx + 1]['startTime'] if word_idx + 1 < len(words) else word['endTime'],
                    'speaker': word['speaker'],
                    'annotations': []
                })
        
        # Update active annotations
        active_annotations = new_annotations

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
            current_speaker = word['speaker']
            current_phrase = {
                'speaker': word['speaker'],
                'text': "",
                'startTime': word['startTime'],
                'endTime': word['endTime']
            }
        
        current_phrase['text'] += word['text'] + " "

    phrases.append(current_phrase)
    return phrases

def generate_html(file_id: str, transcript: dict, entities: dict) -> str:
    """
    Generate an HTML file with interactive Named Entity Recognition (NER) highlights.
    """

    words = transcript['words']
    # phrases = transcript['phrases']
    annotated_words = [x for x in words[:]]  # Copy words list

    for word in annotated_words:
        word['annotations'] = []

    sorted_annotations = sorted(entities['annotations'], key=lambda x: x['startWordIndex'], reverse=True)

    # add annotations onto the words
    for annotation in sorted_annotations:
        annotation_range = range(annotation['startWordIndex'], annotation['endWordIndex'])
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
                    transition: background-color 0.3s ease;
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
                    phrase_start = phrase['startTime']
                    phrase_end = phrase['endTime']
                    speaker = phrase['speaker']
                    if speaker != current_speaker:
                        if current_speaker is not None:
                            a.br()
                            a(f"<span class='speaker'>{phrase_start}-{phrase_end} - {speaker} -- </span>")
                        current_speaker = speaker
                    phrase_text = phrase['text']
                    a(phrase_text)
                    a.br()

            for entity_id in sorted_annotations:
                with a.script():
                    a(f"""
                    document.getElementById("toggle-{entity_id}").addEventListener("change", function() {{
                        const elements = document.querySelectorAll(".{entity_id}");
                        elements.forEach(el => {{
                            if (this.checked) {{
                                el.classList.remove("no-highlight");
                            }} else {{
                                el.classList.add("no-highlight");
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
