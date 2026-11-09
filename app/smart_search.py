from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _doc(record):
    """The text of one record that we search over."""
    return " ".join([
        record.get("topic", ""),
        record.get("insurance_type", ""),
        record.get("rule_summary", ""),
        record.get("time_limit", ""),
        record.get("who_to_contact", ""),
    ])


def rank(records, query, top_k=5):
    """Return up to top_k records most similar to the query, best first.
    Each result is a copy of the record with an added 'score' field."""
    query = query.strip()
    if not records or not query:
        return []

    docs = [_doc(r) for r in records]
    vectorizer = TfidfVectorizer(stop_words="english")
    doc_matrix = vectorizer.fit_transform(docs)
    query_vec = vectorizer.transform([query])

    scores = cosine_similarity(query_vec, doc_matrix).ravel()
    order = scores.argsort()[::-1][:top_k]

    results = []
    for i in order:
        if scores[i] > 0:  # skip records with nothing in common with the query
            results.append({**records[i], "score": round(float(scores[i]), 4)})
    return results