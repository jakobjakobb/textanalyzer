import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "db.db")

def getWord(inp):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM db WHERE Form = ?", (inp.lower(),))
        data = cursor.fetchall()
        return {
            "resource": data[0][0], 
            "resource_id": data[0][1], 
            "grammatical_id": data[0][2], 
            "variation_id": data[0][3], 
            "lemma": data[0][4], 
            "glosse": data[0][5], 
            "grammatical_terms": data[0][6].split(","), 
            "form": data[0][7], 
            "normering": data[0][8]
        } if data else None

def analyze(inp):
    out = []
    sentences = ' \n '.join(inp.splitlines()).replace(',','').replace('é','e').split('.')
    for sentence in sentences:
        words = sentence.split(' ')
        for word in words:
            start_time = time.time()
            if word.strip() == '':
                out.append(word)
                continue
            word_info = getWord(word)
            if not word_info:
                word_attempt = []
                while not word_info:
                    word_attempt.append(word[len(word_attempt)])
                    if getWord(f'{''.join(word_attempt)}-'):
                        word_info = getWord(word[len(word_attempt)::])
            word_tag = f'[{word_info['grammatical_terms'][0]}]' if word_info else '[?]'
            out.append(f" {word}{word_tag}")
            print(f"Found the word '{word}' in {time.time()-start_time}s")
        out.append('.')
    return ''.join(out)

def main():
    start_time = time.time()
    with open("output.txt", "w", encoding='utf-8') as outf:
        outf.write(analyze(open("input.txt", "r", encoding='utf-8').read()))
        print(f"Completed in {time.time()-start_time}s")