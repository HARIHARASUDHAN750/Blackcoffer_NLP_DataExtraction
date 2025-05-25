# main.py

import os
import re
import string
import syllapy
import requests
import pandas as pd
from bs4 import BeautifulSoup
from textblob import TextBlob
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Load Input File
input_df = pd.read_excel("Input.xlsx")

# Create directory to save extracted texts
os.makedirs("text_files", exist_ok=True)

# Load positive and negative word lists
with open("stopwords/positive-words.txt", "r") as f:
    positive_words = set(f.read().split())
with open("stopwords/negative-words.txt", "r") as f:
    negative_words = set(f.read().split())

# Load custom stopwords
stopword_files = [
    'stopwords/stopwords_auditor.txt',
    'stopwords/stopwords_currency.txt',
    'stopwords/stopwords_datesandnumbers.txt',
    'stopwords/stopwords_generic.txt',
    'stopwords/stopwords_names.txt',
    'stopwords/stopwords_places.txt',
    'stopwords/stopwords_connectors.txt'
]
stop_words = set(stopwords.words('english'))
for file in stopword_files:
    with open(file, 'r') as f:
        stop_words.update(f.read().splitlines())

# Utility functions
def get_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1').text.strip() if soup.find('h1') else ""
        paragraphs = soup.find_all('p')
        text = ' '.join([p.text for p in paragraphs])
        return title + "\n" + text
    except:
        return ""

def clean_text(text):
    text = re.sub(r"[^A-Za-z\s]", "", text)
    return text

def count_syllables(word):
    return syllapy.count(word)

def is_complex(word):
    return count_syllables(word) >= 3

def count_personal_pronouns(text):
    return len(re.findall(r"\b(I|we|my|ours|us)\b", text, re.I))

# Analysis functions
def analyze_text(text):
    text_clean = clean_text(text)
    words = word_tokenize(text_clean.lower())
    words_filtered = [w for w in words if w not in stop_words and w.isalpha()]
    sentences = sent_tokenize(text)

    positive_score = sum(1 for w in words_filtered if w in positive_words)
    negative_score = sum(1 for w in words_filtered if w in negative_words)
    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (len(words_filtered) + 0.000001)

    avg_sentence_length = len(words_filtered) / len(sentences) if sentences else 0
    complex_word_count = sum(1 for w in words_filtered if is_complex(w))
    percentage_complex_words = complex_word_count / len(words_filtered) if words_filtered else 0
    fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)
    avg_words_per_sentence = avg_sentence_length
    syllable_per_word = sum(count_syllables(w) for w in words_filtered) / len(words_filtered) if words_filtered else 0
    avg_word_length = sum(len(w) for w in words_filtered) / len(words_filtered) if words_filtered else 0
    personal_pronouns = count_personal_pronouns(text)

    return [
        positive_score,
        negative_score,
        polarity_score,
        subjectivity_score,
        avg_sentence_length,
        percentage_complex_words,
        fog_index,
        avg_words_per_sentence,
        complex_word_count,
        len(words_filtered),
        syllable_per_word,
        personal_pronouns,
        avg_word_length
    ]

# Output Columns
output_columns = list(input_df.columns) + [
    'POSITIVE SCORE', 'NEGATIVE SCORE', 'POLARITY SCORE', 'SUBJECTIVITY SCORE',
    'AVG SENTENCE LENGTH', 'PERCENTAGE OF COMPLEX WORDS', 'FOG INDEX',
    'AVG NUMBER OF WORDS PER SENTENCE', 'COMPLEX WORD COUNT', 'WORD COUNT',
    'SYLLABLE PER WORD', 'PERSONAL PRONOUNS', 'AVG WORD LENGTH']

results = []

for _, row in input_df.iterrows():
    url_id = row['URL_ID']
    url = row['URL']
    print(f"Processing {url_id}...")

    article_text = get_article_text(url)
    with open(f"text_files/{url_id}.txt", "w", encoding="utf-8") as f:
        f.write(article_text)

    metrics = analyze_text(article_text)
    results.append(list(row) + metrics)

# Save Output
output_df = pd.DataFrame(results, columns=output_columns)
output_df.to_csv("output.csv", index=False)
