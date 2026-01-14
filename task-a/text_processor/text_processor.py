import re
import json
import statistics
from collections import Counter


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


def get_clean_words(text):
    return re.findall(r'\b[^\W\d_]+\b', text.lower(), re.UNICODE)


def get_sentences(text):
    return re.split(r'[.!?\n]\s*', text)


def get_word_freq(file_content):
    words = get_clean_words(file_content)
    stop_words = load_stop_words()
    filtered_words = [w for w in words if w not in stop_words]
    return Counter(filtered_words).most_common(20)


def get_sentence_starts(file_content):
    sentences = get_sentences(file_content)
    starts = []
    for sentence in sentences:
        words = get_clean_words(sentence)
        if words:
            starts.append(words[0])
    return Counter(starts).most_common(10)


def get_length_stats(file_content):
    sentence_lengths = [
        len(get_clean_words(sentence))
        for sentence in get_sentences(file_content)
    ]
    
    if not sentence_lengths:
        return 0, 0, 0

    mean_val = statistics.mean(sentence_lengths)
    median_val = statistics.median(sentence_lengths)
    stdev_val = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
    
    return {
        "mean": mean_val,
        "median": median_val,
        "standard_deviation": stdev_val
    }


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
