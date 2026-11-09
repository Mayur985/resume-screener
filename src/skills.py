import spacy
from spacy.matcher import PhraseMatcher

SKILLS = [
    "python", "java", "sql", "excel", "tableau", "power bi",
    "machine learning", "deep learning", "nlp", "statistics",
    "pandas", "numpy", "scikit learn", "tensorflow", "pytorch",
    "aws", "docker", "git", "html", "css", "javascript",
    "react", "django", "flask", "mongodb", "mysql",
    "communication", "leadership", "project management",
    "recruitment", "payroll", "accounting", "sales", "marketing",
    "onboarding", "employee relations", "performance reviews", "benefits", "training",
]

nlp = spacy.load("en_core_web_sm")

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("SKILLS", [nlp.make_doc(skill) for skill in SKILLS])


def extract_skills(text):
    text = str(text).lower()
    doc = nlp(text)
    found = set()
    for _, start, end in matcher(doc):
        found.add(doc[start:end].text)
    return sorted(found)


def extract_skills_batch(texts):
    """Fast version for many texts: only tokenizes, then matches."""
    results = []
    with nlp.select_pipes(enable=[]):
        for doc in nlp.pipe([str(t).lower() for t in texts], batch_size=50):
            found = {doc[s:e].text for _, s, e in matcher(doc)}
            results.append(sorted(found))
    return results


def skill_gap_from_lists(job_skills, resume_skills):
    """Compare two skill lists that were already extracted."""
    job_skills, resume_skills = set(job_skills), set(resume_skills)
    matched = sorted(job_skills & resume_skills)
    missing = sorted(job_skills - resume_skills)
    score = len(matched) / len(job_skills) if job_skills else 0
    return {"matched": matched, "missing": missing, "skill_score": round(score, 2)}


def skill_gap(job_text, resume_text):
    """Older version that takes raw texts. Still used by the notebook."""
    return skill_gap_from_lists(extract_skills(job_text), extract_skills(resume_text))