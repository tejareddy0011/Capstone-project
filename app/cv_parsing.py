import os
import spacy
import fitz  # PyMuPDF


# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text() + "\n"
    return text

# Extract potential skills using NER and POS tagging
def extract_skills(text):
    doc = nlp(text)
    skills_found = set()
    
    # Filter for nouns, proper nouns, or named entities
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
            skills_found.add(token.text.lower())  # Normalize to lowercase
    
    return list(skills_found)

# Score resumes based on target skills
def calculate_matching_score(found_skills, target_skills):
    # Remove spaces and convert to lowercase
    found_skills = [skill.strip().lower() for skill in found_skills]
    target_skills = [skill.strip().lower() for skill in target_skills]
    
    # Find intersection of skills
    matched_skills = set(found_skills) & set(target_skills)
    return len(matched_skills) / len(target_skills) if target_skills else 0
  # Score as a fraction of total target skills

