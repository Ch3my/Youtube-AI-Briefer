# Como parece que al LLM se le pasan los temas que estan en medio haremos un loop
# donde ira resumiendo poco a poco el contenido, luego tomaremos todos los pedazos y sin cambiar
# el contenido los unira y convertira en un texto cohesivo

def split_text_into_sections_by_number_of_words(text, words_per_section, overlap):
    # Split the text into words
    words = text.split()

    sections = []
    i = 0

    while i < len(words):
        # Define the start and end indices for the current section
        start_index = i
        end_index = i + words_per_section

        # Extract the current section of words
        section = " ".join(words[start_index:end_index])
        sections.append(section)

        # Move the index forward by the number of words per section minus the overlap
        i += words_per_section - overlap

    return sections