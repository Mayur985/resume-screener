# Resume Screener

An NLP tool that ranks resumes against a job description and shows missing skills.

## Status
Work in progress.

## Tech
Python, pandas, scikit-learn, spaCy, sentence-transformers, Streamlit

## Dataset
Kaggle Resume Dataset (https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)

## Plan
- [x] Set up project and load data
- [x] Explore data and clean resume text
- [x] Extract skills with spaCy
- [x] Match resumes to job using TF-IDF
- [ ] Improve matching with sentence embeddings
- [ ] Build Streamlit app
- [ ] Add demo GIF and screenshots


## Progress so far
- Loaded the Kaggle resume dataset and explored the categories
- Wrote a `clean_text` function (`src/cleaning.py`) that lowercases text and removes links, emails, and symbols
- Built a skill extractor (`src/skills.py`) using spaCy PhraseMatcher that finds skills like Python, SQL, and machine learning in resumes
- Built TF-IDF matching (`src/matching.py`) with unigrams and bigrams to rank resumes against a job description
- Added a skill gap function (`src/skills.py`) that shows matched and missing skills for each resume

## Findings
- The HR job matched HR resumes very well (all top 5 were HR, scores about 0.36 to 0.42).
- Tech jobs matched weakly. The dataset has no Data Science category, and most IT resumes are about IT support, not programming.
- TF-IDF matches words, not meaning, so generic words can pull in unrelated resumes. I plan to try sentence embeddings next.

## How to run
Coming soon.
