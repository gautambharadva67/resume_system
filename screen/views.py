from django.shortcuts import render
import re
import string
import PyPDF2
import pandas as pd
import os
from django.conf import settings



# ----------------------------
# Load Skills & Education from CSV
# ----------------------------
def load_keywords_from_csv():

    file_path = os.path.join(settings.BASE_DIR, "screen", "resumedata.csv")
    df = pd.read_csv(file_path)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Extract all unique skills from dataset
    skills_list = []

    for skills in df["skills"]:

        skill_split = skills.split(",")
        skills_list.extend([s.strip().lower() for s in skill_split])

    skills_list = list(set(skills_list))  # remove duplicates

    # Extract education / degree
    education_list = df["education"].str.lower().unique().tolist()

    return skills_list, education_list

# ----------------------------
# Clean Text
# ----------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)

    # Remove punctuation EXCEPT . + # /
    allowed_chars = ".+#/"
    punctuation_to_remove = ''.join(
        ch for ch in string.punctuation if ch not in allowed_chars
    )

    text = text.translate(str.maketrans('', '', punctuation_to_remove))

    return text


# ----------------------------
# Extract Keywords (From CSV Data)
# ----------------------------
def extract_valid_keywords(text):

    SKILLS, EDUCATION = load_keywords_from_csv()

    found_skills = []
    found_education = []

    for skill in SKILLS:
        if skill in text:
            found_skills.append(skill)

    for edu in EDUCATION:
        if edu in text:
            found_education.append(edu)

    return list(set(found_skills)), list(set(found_education))


# ----------------------------
# Calculate Match (Same Logic)
# ----------------------------
def calculate_match(resume, job_description):

    resume_clean = clean_text(resume)
    job_clean = clean_text(job_description)

    resume_skills, resume_edu = extract_valid_keywords(resume_clean)
    job_skills, job_edu = extract_valid_keywords(job_clean)

    matched_skills = list(set(resume_skills) & set(job_skills))
    missing_skills = list(set(job_skills) - set(resume_skills))

    matched_edu = list(set(resume_edu) & set(job_edu))
    missing_edu = list(set(job_edu) - set(resume_edu))

    # Skill Score
    skill_score = round(
        (len(matched_skills) / len(job_skills)) * 100, 2
    ) if job_skills else 0

    # Education Score
    if job_edu:
        edu_score = 100 if matched_edu else 0
    else:
        edu_score = 0

    # overall_score = round((skill_score + edu_score) / 2, 2)
    overall_score = round((skill_score * 0.6) + (edu_score * 0.4), 2)

    return (
        skill_score,
        edu_score,
        overall_score,
        job_skills, job_edu,
        matched_skills, matched_edu,
        missing_skills, missing_edu
    )


# ----------------------------
# Extract Text From PDF
# ----------------------------
def extract_text_from_pdf(pdf_file):
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


# ----------------------------
# Django View
# ----------------------------
def home(request):

    skill_score = edu_score = overall_score = None
    resume_text = job_description_text = ""

    job_skills = job_edu = None
    matched_skills = matched_edu = None
    missing_skills = missing_edu = None

    if request.method == "POST":

        resume_file = request.FILES.get("resume_file")
        jd_file = request.FILES.get("jd_file")

        if resume_file:
            resume_text = extract_text_from_pdf(resume_file)

        if jd_file:
            job_description_text = extract_text_from_pdf(jd_file)

        if resume_text and job_description_text:
            (
                skill_score,
                edu_score,
                overall_score,
                job_skills, job_edu,
                matched_skills, matched_edu,
                missing_skills, missing_edu
            ) = calculate_match(resume_text, job_description_text)

    return render(request, "index.html", {
        "skill_score": skill_score,
        "edu_score": edu_score,
        "overall_score": overall_score,
        "job_skills": job_skills,
        "job_edu": job_edu,
        "matched_skills": matched_skills,
        "matched_edu": matched_edu,
        "missing_skills": missing_skills,
        "missing_edu": missing_edu,
    })
