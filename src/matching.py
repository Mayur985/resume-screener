from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_index(resume_texts):
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(resume_texts)
    return vectorizer, matrix


def score_job(job_text, vectorizer, matrix):
    job_vector = vectorizer.transform([job_text])
    return cosine_similarity(job_vector, matrix).flatten()


def rank_resumes(job_text, resume_texts):
    vectorizer, matrix = build_index(resume_texts)
    return score_job(job_text, vectorizer, matrix)