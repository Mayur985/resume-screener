import base64
import glob
import os
from urllib.parse import quote

import pandas as pd
import pdfplumber
import streamlit as st

from src.cleaning import clean_text
from src.matching import build_index, score_job
from src.skills import extract_skills, extract_skills_batch, skill_gap_from_lists

st.set_page_config(page_title="Resume Screener", page_icon="📄", layout="wide")

WEIGHT = 0.5  # fixed mix: 50% text match, 50% skill match

# ------------------------------------------------------------------
# Look and feel
# ------------------------------------------------------------------
PAGE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='1600' height='900'>
<defs><filter id='b'><feGaussianBlur stdDeviation='90'/></filter></defs>
<rect width='100%' height='100%' fill='#0B1620'/>
<g filter='url(#b)'>
<circle cx='150' cy='120' r='280' fill='#0E4A55'/>
<circle cx='1450' cy='160' r='300' fill='#17375A'/>
<circle cx='800' cy='880' r='340' fill='#0F4B45'/>
</g></svg>"""

HERO_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='520' height='220' viewBox='0 0 520 220'>
<g fill='none'>
<rect x='300' y='30' width='120' height='160' rx='10' fill='#FFFFFF' fill-opacity='0.10' stroke='#FFFFFF' stroke-opacity='0.35'/>
<rect x='330' y='20' width='120' height='160' rx='10' fill='#FFFFFF' fill-opacity='0.14' stroke='#FFFFFF' stroke-opacity='0.45'/>
<rect x='360' y='10' width='120' height='160' rx='10' fill='#FFFFFF' fill-opacity='0.95'/>
<circle cx='392' cy='44' r='13' fill='#0E7C86'/>
<rect x='414' y='36' width='50' height='7' rx='3' fill='#0F2A43'/>
<rect x='414' y='49' width='34' height='6' rx='3' fill='#9DB4C0'/>
<rect x='376' y='72' width='88' height='6' rx='3' fill='#C9D8E0'/>
<rect x='376' y='86' width='78' height='6' rx='3' fill='#C9D8E0'/>
<rect x='376' y='100' width='84' height='6' rx='3' fill='#C9D8E0'/>
<rect x='376' y='122' width='26' height='12' rx='6' fill='#BFE9D6'/>
<rect x='408' y='122' width='32' height='12' rx='6' fill='#BFE9D6'/>
<rect x='376' y='140' width='38' height='12' rx='6' fill='#F9D9B8'/>
<circle cx='300' cy='150' r='34' stroke='#FFFFFF' stroke-width='7'/>
<line x1='324' y1='174' x2='352' y2='202' stroke='#FFFFFF' stroke-width='9' stroke-linecap='round'/>
</g></svg>"""


def build_css():
    custom = "assets/background.jpg"
    if os.path.exists(custom):
        with open(custom, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        page_bg = (
            "linear-gradient(rgba(11,22,32,0.88), rgba(11,22,32,0.93)), "
            f"url('data:image/jpeg;base64,{b64}')"
        )
    else:
        page_bg = f"url(\"data:image/svg+xml;utf8,{quote(PAGE_SVG)}\")"
    hero_img = f"url(\"data:image/svg+xml;utf8,{quote(HERO_SVG)}\")"

    css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {font-family: 'Manrope', sans-serif;}
.stApp {
    background: PAGE_BG;
    background-size: cover;
    background-attachment: fixed;
    color: #E6EEF3;
}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 2rem; max-width: 1150px;}

[data-testid="stSidebar"] {
    background: rgba(10, 20, 30, 0.88);
    backdrop-filter: blur(10px);
    border-right: 1px solid #1E3345;
}
[data-testid="stSidebar"] h2 {font-size: 1.05rem; color: #7FD6DD; margin-top: 0.6rem;}

.hero {
    background: #12344D HERO_IMG no-repeat right 24px center;
    background-size: auto 85%;
    border-radius: 16px;
    border: 1px solid #1F4A68;
    padding: 34px 40px;
    margin-bottom: 22px;
}
.hero h1 {color: #FFFFFF; font-size: 2.1rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;}
.hero p {color: #BFD3DF; margin: 8px 0 0 0; max-width: 520px; font-size: 1rem; line-height: 1.5;}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(18, 34, 48, 0.88);
    border: 1px solid #1E3345;
    border-radius: 14px;
}

.badge {display: inline-block; padding: 3px 11px; margin: 2px 5px 2px 0;
        border-radius: 999px; font-size: 0.8rem; font-weight: 600;}
.ok {background: #134E3A; color: #A7F3D0;}
.miss {background: #5A3511; color: #FDE0B8;}
.rank {font-size: 1.5rem; font-weight: 800; color: #4FD1C5;}

div.stButton > button[kind="primary"] {
    background: #0E7C86; color: #FFFFFF; border: none; font-weight: 700; padding: 0.6rem 1.6rem;
}
div.stButton > button[kind="primary"]:hover {background: #0B646C;}
</style>
"""
    return css.replace("PAGE_BG", page_bg).replace("HERO_IMG", hero_img)


st.markdown(build_css(), unsafe_allow_html=True)
st.markdown(
    '<div class="hero"><h1>Resume Screener</h1>'
    "<p>Paste a job description and see which resumes fit best, "
    "and which required skills each one has or lacks.</p></div>",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# Data and caching (slow work happens once, then stays in memory)
# ------------------------------------------------------------------
@st.cache_resource(show_spinner="Preparing resumes (first time only, about a minute)...")
def prepare_dataset():
    df = pd.read_csv("data/Resume.csv")
    df["name"] = df["Category"] + " #" + df["ID"].astype(str)
    df["text"] = df["Resume_str"]
    df["clean_text"] = df["text"].apply(clean_text)
    vectorizer, matrix = build_index(df["clean_text"])
    skills = extract_skills_batch(df["clean_text"].tolist())
    return df, vectorizer, matrix, skills


def read_file(file):
    if file.name.lower().endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            return " ".join(page.extract_text() or "" for page in pdf.pages)
    return file.read().decode("utf-8", errors="ignore")


def badges(skills, css):
    if not skills:
        return "<i>none</i>"
    return "".join(f'<span class="badge {css}">{s}</span>' for s in skills)


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
cats = []
upload_df = None

with st.sidebar:
    st.header("1. Choose resumes")
    source = st.radio(
        "Where are the resumes from?",
        ["Sample dataset", "My own files"],
        help="The sample dataset has about 2,500 resumes. Or upload your own PDF or TXT files.",
    )

    if source == "Sample dataset":
        all_cats = sorted(pd.read_csv("data/Resume.csv", usecols=["Category"])["Category"].unique())
        cats = st.multiselect(
            "Only these job types (optional)",
            all_cats,
            help="Leave empty to search all resumes.",
        )
    else:
        files = st.file_uploader("Upload resumes", type=["pdf", "txt"], accept_multiple_files=True)
        if files:
            upload_df = pd.DataFrame({"name": [f.name for f in files],
                                      "text": [read_file(f) for f in files]})
            upload_df["clean_text"] = upload_df["text"].apply(clean_text)

    st.header("2. How many results?")
    top_n = st.slider("Number of results", 1, 50, 10)

# ------------------------------------------------------------------
# Job description
# ------------------------------------------------------------------
job_files = sorted(glob.glob("data/*.txt"))
names = ["(write my own)"] + [os.path.basename(p) for p in job_files]
choice = st.selectbox("Start from a sample job", names)

default_text = ""
if choice != "(write my own)":
    with open(f"data/{choice}", encoding="utf-8") as f:
        default_text = f.read()

job_input = st.text_area("Job description", value=default_text, height=180, key=f"job_{choice}")
run = st.button("Rank resumes", type="primary")

# ------------------------------------------------------------------
# Scoring
# ------------------------------------------------------------------
if run:
    if not job_input.strip():
        st.warning("Add a job description first.")
    elif source == "My own files" and (upload_df is None or upload_df.empty):
        st.warning("Upload at least one resume in the sidebar.")
    else:
        try:
            with st.spinner("Scoring resumes..."):
                if source == "Sample dataset":
                    df, vectorizer, matrix, all_skills = prepare_dataset()
                else:
                    df = upload_df
                    vectorizer, matrix = build_index(df["clean_text"])
                    all_skills = extract_skills_batch(df["clean_text"].tolist())

                job_text = clean_text(job_input)
                job_skills = extract_skills(job_text)

                res = df.copy()
                res["text_score"] = score_job(job_text, vectorizer, matrix)
                res["skills_found"] = all_skills
                if cats:
                    res = res[res["Category"].isin(cats)]

                gaps = [skill_gap_from_lists(job_skills, s) for s in res["skills_found"]]
                res["skill_score"] = [g["skill_score"] for g in gaps]
                res["matched"] = [g["matched"] for g in gaps]
                res["missing"] = [g["missing"] for g in gaps]

                best = res["text_score"].max()
                res["text_norm"] = res["text_score"] / best if best > 0 else 0.0
                if job_skills:
                    res["final"] = (WEIGHT * res["text_norm"] + (1 - WEIGHT) * res["skill_score"]) * 100
                else:
                    res["final"] = res["text_norm"] * 100

                st.session_state["result"] = res.sort_values("final", ascending=False)
                st.session_state["total"] = len(res)
                st.session_state["job_skills"] = job_skills
        except ValueError:
            st.error("Could not read any words from the text. Check the job description and the resumes.")

# ------------------------------------------------------------------
# Results
# ------------------------------------------------------------------
if "result" in st.session_state:
    top = st.session_state["result"].head(top_n)

    if not st.session_state["job_skills"]:
        st.info("No known skills were found in this job description, so the ranking uses text match only. "
                "Add more skills to SKILLS in src/skills.py to improve this.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Resumes scanned", st.session_state["total"])
    c2.metric("Best match", f"{top['final'].max():.0f} / 100")
    c3.metric("Average skill match", f"{top['skill_score'].mean() * 100:.0f}%")

    tab1, tab2, tab3 = st.tabs(["Top matches", "Chart", "Table"])

    with tab1:
        for i, row in enumerate(top.itertuples(), 1):
            with st.container(border=True):
                a, b = st.columns([1, 8])
                a.markdown(f'<div class="rank">#{i}</div>', unsafe_allow_html=True)
                b.markdown(
                    f"**{row.name}** &nbsp; Match **{row.final:.0f}/100** &nbsp; "
                    f"Text {row.text_norm * 100:.0f}% &nbsp; Skills {row.skill_score * 100:.0f}%"
                )
                b.progress(min(max(row.final / 100, 0.0), 1.0))
                st.markdown("**Has:** " + badges(row.matched, "ok"), unsafe_allow_html=True)
                st.markdown("**Lacks:** " + badges(row.missing, "miss"), unsafe_allow_html=True)
                with st.expander("Read resume"):
                    st.write(row.text[:3000])

    with tab2:
        st.bar_chart(top.set_index("name")["final"])

    with tab3:
        table = top[["name", "final", "text_norm", "skill_score"]].copy()
        table["Lacks"] = top["missing"].apply(", ".join)
        table["text_norm"] = table["text_norm"] * 100
        table["skill_score"] = table["skill_score"] * 100
        table.columns = ["Resume", "Match (0-100)", "Text %", "Skills %", "Lacks"]
        st.dataframe(table.round(0), hide_index=True)
else:
    st.info("Pick or paste a job description, then click **Rank resumes**.")