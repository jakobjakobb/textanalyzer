
import sqlite3
import os
import time
import re


PATH = os.path.dirname(__file__)
INPUT_FILE = "input.txt"
OUTPUT_FILE = "output.md"
DB_FILE = "db.db"


def read_input():
    with open(os.path.join(PATH, INPUT_FILE), "r", encoding='utf-8') as inf:
        return inf.read()


def write_output(out=''):
    with open(os.path.join(PATH, OUTPUT_FILE), "w", encoding='utf-8') as outf:
        outf.write(out)

def append_output(out):
    with open(os.path.join(PATH, OUTPUT_FILE), "a", encoding='utf-8') as outf:
        outf.write(f'{out} ')

def get_word_data(inp):
    with sqlite3.connect(os.path.join(PATH, DB_FILE)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM db WHERE Form = ?", (inp.lower(),))
        data = cursor.fetchall()
        if not data: return None
        out = []
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
        return out


def color_word(word, color_id=''):
    color_name = ''
    match color_id:
        case 'prefix': color_name = 'red'
        case 'suffix': color_name = 'green'
        case 'tag': color_name = 'gray'
        case 'invalid': color_name = 'brown'
        case _ : color_name = ''
    return f'<font color="{color_name}">{word}</font>'

def analyze_word(word):

    prefix = ''
    prefix_attempt = []
    while not prefix:
        if len(prefix_attempt) == len(word):
            if not get_word_data(word):
                return None
            break
        prefix_attempt.append(word[len(prefix_attempt)])
        stringified_prefix = "".join(prefix_attempt)
        if get_word_data(f'{stringified_prefix}-'):
            prefix = stringified_prefix

    core_word = word
    if prefix: core_word = word[len(prefix)::]

    word_data = get_word_data(core_word)
    
    if not word_data:
        return None
    
    lemma = word_data[0]['lemma']

    suffix = ''
    if core_word.startswith(lemma) and lemma != core_word:
        suffix = core_word[len(lemma)::]
        core_word = core_word[:-len(suffix)]

    grammatical_terms = f'[{" eller ".join(set(i["grammatical_terms"][0] for i in word_data))}]'

    return {
        "prefix": prefix,
        "lemma": core_word,
        "suffix": suffix,
        "tag": grammatical_terms
    }

def tokenize(inp):
    # text = ' \n '.join(inp.splitlines()).replace(',',' , ').replace('.',' . ').replace('é','e')
    # return text.split(' ')
    return ''.join(inp.replace(',',' , ').replace('.',' . ').replace('\n',' \n ')).split(' ')
    
def is_valid_word(inp):
    word = inp.strip()
    if not word: return False
    pattern = r'^[a-zA-ZæøåÆØÅ-]+$'
    return True if re.match(pattern,word) else False


def main():
    start_time = time.time()
    inp = read_input()
    write_output()
    
    for token in tokenize(inp):
        if not is_valid_word(token):
            if token == '\n':
                append_output('<br>\n')
            append_output(color_word(token, "invalid"))
            continue

        word_start_time = time.time()

        word_result = analyze_word(token)


        if not word_result:
            append_output(color_word(token, 'lemma') + color_word('[?]', 'tag'))
            continue


        word = ''.join(color_word(v, k) for k, v in word_result.items() if v)
        append_output(word)

        print(f"Analyzed word '{word_result['lemma']}' in {time.time()-word_start_time:.4f} seconds...")

    print(f"Completed in {time.time()-start_time} seconds!")

main() 