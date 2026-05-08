
import sqlite3
import os
import time
import re

##########################################
# --- Konfiguration og globale stier --- #
##########################################

# Finder mappen hvor scriptet ligger i, så stier altid er korrekte uanset hvor det køres fra.
# Kan ændres hvis database, input og output filer ligger et andet sted.
PATH = os.path.dirname(__file__)

INPUT_FILE = "input.txt"    # Filnavn af kildeteksten, der skal analyseres.
OUTPUT_FILE = "output.md"   # Filnavn af resultat, som gemmes som Markdown.
DB_FILE = "db.db"           # Filnavn af SQLite databasen med ordliste.

HIGHLIGHT_AFFIX = False     # Bestemmer om præfikser skal markeres med farve.
PRINT_PROGRESS = True       # Skriver status i konsollen undervejs

########################
# --- Cache system --- #
########################

# Bruges til at gemme opslag i RAM midlertidigt, så databasen ikke skal lede efter samme ord flere gange.
cache = {}
cache_keys = []

#####################################
# --- Forbindelse til databasen --- #
#####################################

conn = sqlite3.connect(os.path.join(PATH, DB_FILE))
cursor = conn.cursor()

#########################
# --- Filhåndtering --- #
#########################

def read_input():
    """Læser indholdet af inputfilen."""
    with open(os.path.join(PATH, INPUT_FILE), "r", encoding='utf-8') as inf:
        return inf.read()

def write_output(out=''):
    """Overskriver eller nulstiller outputfilen."""
    with open(os.path.join(PATH, OUTPUT_FILE), "w", encoding='utf-8') as outf:
        outf.write(out)

def append_output(out):
    """Tilføjer tekst til slutningen af outputfilen for løbende skrivning."""
    with open(os.path.join(PATH, OUTPUT_FILE), "a", encoding='utf-8') as outf:
        outf.write(f'{out} ')

##############################
# --- Database og opslag --- #
##############################

def get_word_data(inp):
    """Søger efter et ord eller ord-del i databasen med caching."""

    # Hvis input allerede findes i cache, skal det returneres.
    if inp in cache_keys: return cache[inp]

    # Søger i kolonnen "Form" (små bogstaver).
    cursor.execute("SELECT * FROM db WHERE Form = ?", (inp.lower(),))
    data = cursor.fetchall()

    out = []
    # Tjekker om der er data i rækken (om ordet findes i databasen).
    if not data: 
        out = None
    else:
        # Mapper databaserækker til en læsbare dictionaries
        for data_set in data:
            out.append({
            "resource": data_set[0], 
            "resource_id": data_set[1], 
            "grammatical_id": data_set[2], 
            "variation_id": data_set[3], 
            "lemma": data_set[4], 
            "glosse": data_set[5], 
            "grammatical_terms": data_set[6].split(","), 
            "form": data_set[7], 
            "normering": data_set[8]
            })
    
    # Gem resultatet i cache til næste gang
    cache[inp] = out
    cache_keys.append(inp)
    return out


def color_word(word, color_id=''):
    """Returnerer ordet pakket ind i en HTML fonttag med farve."""
    # Vælger farve ud fra color_id input.
    color_name = ''
    match color_id:
        case 'prefix': color_name = 'red' if HIGHLIGHT_AFFIX else ''
        case 'suffix': color_name = 'green' if HIGHLIGHT_AFFIX else ''
        case 'tag': color_name = 'gray'
        case 'invalid': color_name = 'brown'
        case _ : color_name = ''
    
    # HTMl fonttag formateres vha. f-strings.
    return f'<font color="{color_name}">{word}</font>'

###############################
# --- Lingvistisk analyse --- #
###############################

def analyze_word(word):
    """Forsøger at splitte ord op i præfiks, lemma og tilføje grammatiske tags."""
    
    prefix = ''
    prefix_attempt = []

    # Forsøger at finde et præfiks ved at bygge ordet op bogstav for bogstav
    # og tjekke om databasen kender det som et præfiks (kendetegnet ved en slutning på "-").
    while not prefix:
        if len(prefix_attempt) == len(word):
            if not get_word_data(word):
                return None # Ordet findes ikke
            break

        prefix_attempt.append(word[len(prefix_attempt)])
        stringified_prefix = "".join(prefix_attempt)

        # Databasen tjekkes for præfiksformatet (indikeret ved bindesteg).
        if get_word_data(f'{stringified_prefix}-'):
            prefix = stringified_prefix

    core_word = word
    if prefix: core_word = word[len(prefix)::] # Fjerner præfiks fra selve ordet

    word_data = get_word_data(core_word)
    if not word_data:
        return None # Ordet findes ikke
    
    # Suffikslogik virkede ikke super godt, derfor bruges den ikke.

    suffix = ''
    #lemma = word_data[0]['lemma']
    #if core_word.startswith(lemma) and lemma != core_word:
    #    suffix = core_word[len(lemma)::]
    #    core_word = core_word[:-len(suffix)]

    # Udtrækker de grammatiske termer og fjerner dubletter vha. set().
    grammatical_terms = f'[{" eller ".join(set(i["grammatical_terms"][0] for i in word_data))}]'

    return {
        "prefix": prefix,
        "lemma": core_word,
        "suffix": suffix,
        "tag": grammatical_terms
    }

###########################
# --- Tekstbehandling --- #
###########################

def tokenize(inp):
    """Splitter tekst op i ord, men bevarer tegnsætning og linjeskift som egne tokens."""
    return inp.replace(',',' , ').replace('.',' . ').replace('\n',' \n ').split(' ')
    
def is_valid_word(inp):
    """Tjekker om en streng er et rigtigt ord (Kun bogstaver og bindestreg)."""
    word = inp.strip()
    if not word: return False

    # Sammenligner streng med regulært udtryk.
    pattern = r'^[a-zA-ZæøåÆØÅ-]+$'
    return True if re.match(pattern,word) else False

########################
# --- Hovedprogram --- #
########################

def main():
    """Hovedfunktionalitet."""

    # Finder tidspunktet ved start for senere at beregne programmets taget tid.
    start_time = time.time()
    inp = read_input()  # Læser inputfilen
    write_output()      # Rydder outputfilen for tekst
    
    for token in tokenize(inp):
        # Håndtering af specialtegn, mellemrum og linjeskift.
        if not is_valid_word(token):
            if token == '\n':
                append_output('<br>\n')
            append_output(color_word(token, "invalid"))
            continue
        
        # Finder tidspunktet for at beregne hvor lang tid det tog at analysere ordet.
        word_start_time = time.time()

        # Kører funktionen, der analyserer ordet, og gemmer derefter resultatet.
        word_result = analyze_word(token)

        # Hvis ordet ikke kunne findes/analyseres.
        if not word_result:
            append_output(color_word(token, 'lemma') + color_word('[?]', 'tag'))
            continue

        # Samler de analyserede dele (præfiks, lemma, tag) og farverlægger dem
        word = ''.join(color_word(v, k) for k, v in word_result.items() if v)
        append_output(word)

        # Skriver status i konsollen hvis det er slået til.
        if PRINT_PROGRESS: print(f"Analyzed word '{word_result['lemma']}' in {time.time()-word_start_time:.4f} seconds...")

    # Skriver status for analyse af hele teksten.
    print(f"Completed in {time.time()-start_time:.4f} seconds!")

main() # Kører hovedprogrammet