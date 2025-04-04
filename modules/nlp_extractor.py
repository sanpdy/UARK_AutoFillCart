# modules/nlp_extractor.py

from keybert import KeyBERT

kw_model = KeyBERT()

def extract_items(query: str) -> list:
    # 1-gram (single word) focus and remove common stop words
    keywords = kw_model.extract_keywords(query, keyphrase_ngram_range=(1, 1), stop_words='english')
    # (keyword, score); return only the keywords
    extracted = [word for word, score in keywords]
    return extracted

# testing:
if __name__ == '__main__':
    sample_query = "I want to make beef and broccoli"
    print("Extracted items:", extract_items(sample_query))
