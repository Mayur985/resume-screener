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
]

nlp=spacy.load('en_core_web_sm')
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("SKILLS", [nlp.make_doc(skill) for skill in SKILLS])

def extract_skills(text):
    text = str(text).lower()        
    doc=nlp(text)
    found=set()
    for _,start,end in matcher(doc):
        found.add(doc[start:end].text)
    return sorted(found)