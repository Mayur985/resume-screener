

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank_resumes(job_text, resume_texts):
    texts = [job_text] + list(resume_texts)
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vectorizer.fit_transform(texts)
    scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    return scores