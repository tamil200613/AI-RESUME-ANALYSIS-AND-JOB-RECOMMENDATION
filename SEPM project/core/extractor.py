import spacy
import pdfplumber
import re
import json

# Try to load spaCy model, if it fails, fallback gracefully and download
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading en_core_web_sm model...")
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

def extract_entities(text):
    """
    Extracts skills, education, and experience entities from text using spaCy and RegEx.
    """
    doc = nlp(text)
    
    # Static master skill ontology for ATS
    KNOWN_SKILLS = [
        "python", "java", "javascript", "react", "node.js", "sql", "flask", 
        "django", "machine learning", "deep learning", "nlp", "aws", "docker", 
        "kubernetes", "c++", "c#", "html", "css", "vue.js", "next.js", "pytorch", 
        "tensorflow", "pandas", "numpy", "scikit-learn", "git", "linux", "gcp", "azure"
    ]
    
    found_skills = set()
    
    # 1. Look for known skills in text via boundary matching (case insensitive)
    text_lower = text.lower()
    for skill in KNOWN_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill.title())
            
    # 2. Extract Organizations via spaCy NER
    organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    
    return {
        "skills": list(found_skills),
        "organizations": list(set(organizations))
    }
