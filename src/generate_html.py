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

def generate_html(file_id: str, transcript: dict, entities: dict) -> str:
    """
    Generate an HTML file with interactive Named Entity Recognition (NER) highlights.
    """

    words = transcript['words']
    annotated_words = [x['text'] for x in words[:]]  # Copy words list

    """
    Currently entities are sorted by startWordIndex in descending order.
    This prevents the need to adjust the index of the words as we write out to the HTML.
    We likely need to adjust this to be smarter in the future.
    """
    sorted_entities = sorted(entities['annotations'], key=lambda x: x['startWordIndex'], reverse=True)

    # Insert <span> tags for entities based on word positions
    for entity in sorted_entities:
        start = entity['startWordIndex']
        end = entity['endWordIndex']
        entity_class = entity['id']

        # Wrap entity words with <span> tags
        annotated_words[start:end+1] = [f"<span class='entity {entity_class}'>{' '.join(annotated_words[start:end+1])}</span>"]

    # Convert transcript to string for writing out
    annotated_transcript = " ".join(annotated_words)



    # Need to roughly-sort the entities by their average position in the transcript
    # Ie. average out startIndex of all entities, sort by that, then assign colours
    sorted_entities = sort_entities(entities['annotations'], entities['metadata']['ids'])

    # Get all entity IDs and assign colours
    # Probably need to add a check for if the entity is not in the list of colours
    entity_colours = {}
    for i, entity_id in enumerate(sorted_entities):
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
                for entity_id in sorted_entities:
                    a(f"""
                    .entity.{entity_id} {{
                        background-color: {entity_colours[entity_id]};
                    }}
                    """)

                a("""
                  .no-highlight {
                    background-color: transparent !important;
                }
                """)

        with a.body():
            with a.h1(id="MainTitle", klass="main_header"):
                a(f"{file_id}: NER Highlighting")
            with a.div():
                for entity_id in sorted_entities:
                    a.input(id=f"toggle-{entity_id}", type="checkbox", checked=True)
                    with a.label(id=f"label-{entity_id}", **{"for": f"toggle-{entity_id}"}, style=f"background-color: {entity_colours[entity_id]};"):
                        a(f" {entity_id} ")
                        a.br()
            
            with a.p(id="transcript"):
                a(annotated_transcript)  # Insert the formatted transcript

            for entity_id in sorted_entities:
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
