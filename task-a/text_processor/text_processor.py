import re
import json
import statistics
from collections import Counter
from pathlib import Path

def load_stop_words(file_path='stop_words.json'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return set()
    except json.JSONDecodeError:
        print(f"File {file_path} has incorrect JSON formatting.")
        return set()

STOP_WORDS = load_stop_words()


def get_clean_words(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return words


def get_word_freq(file_content):
    words = get_clean_words(file_content)
    filtered_words = [w for w in words if w not in STOP_WORDS]
    return Counter(filtered_words).most_common(20)


def get_sentence_starts(file_content):
    sentences = re.split(r'[.!?]\s*', file_content)
    starts = []
    for s in sentences:
        words = re.findall(r'\b\w+\b', s.lower())
        if words:
            starts.append(words[0])
    return Counter(starts).most_common(10)


def get_length_stats(file_content):
    sentences = re.split(r'[.!?]\s*', file_content)
    lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences if s.strip()]
    
    if not lengths:
        return 0, 0, 0

    mean_val = statistics.mean(lengths)
    median_val = statistics.median(lengths)
    stdev_val = statistics.stdev(lengths) if len(lengths) > 1 else 0
    
    return mean_val, median_val, stdev_val


def run_analysis(text, tasks=None):
    if tasks is None:
        tasks = ['frequency', 'starts', 'stats']
    
    results = {}
    
    if 'frequency' in tasks:
        results['word_frequency'] = get_word_freq(text)
    if 'starts' in tasks:
        results['sentence_starts'] = get_sentence_starts(text)
    if 'stats' in tasks:
        results['sentence_length_metrics'] = get_length_stats(text)
        
    return results
