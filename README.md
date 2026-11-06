# Resume Screener

An NLP tool that ranks resumes against a job description and shows missing skills.

## Status
Work in progress.

## Plan
- [x] Set up project and load data
- [x] Explore data and clean resume text
- [ ] Extract skills with spaCy
- [ ] Match resumes to job using TF-IDF
- [ ] Improve matching with sentence embeddings
- [ ] Build Streamlit app
- [ ] Add demo GIF and screenshots

## Progress so far
- Loaded the Kaggle resume dataset and explored the categories
- Wrote a `clean_text` function (`src/cleaning.py`) that lowercases text and removes links, emails, and symbols

## Tech
Python, pandas, scikit-learn, spaCy, sentence-transformers, Streamlit

## Dataset
Kaggle Resume Dataset (https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)

## How to run
Coming soon.
