Overview
The AI Resume Analysis and Job Recommendation System is a web-based application that uses Natural Language Processing (NLP) to analyze resumes and recommend suitable job roles. The system helps students/job seekers improve their resumes and assists recruiters in selecting the best candidates efficiently.

🎯 Features
👨‍🎓 Student Module
Upload Resume (PDF/DOCX)

Automatic Skill Extraction using NLP

Resume Score Generation

Job Recommendations based on skills

Skill Gap Analysis (missing skills)

🏢 Recruiter Module
Post Job Descriptions

View Candidate Profiles

Candidate Ranking based on scores

Filter candidates by skills

🔐 Authentication
Secure Login & Registration

Role-based access (Student / Recruiter)

🧠 Technologies Used
💻 Frontend
HTML

CSS

Bootstrap

⚙️ Backend
Python (Flask)

📊 NLP Libraries
spaCy / NLTK

🗄️ Database
SQLite / MySQL

🛠️ Tools
VS Code

Git & GitHub

Postman

🏗️ System Architecture
The system follows a 3-tier architecture:

Frontend (UI Layer) – User interaction

Backend (Application Layer) – Processing & logic

Database (Data Layer) – Data storage

🔄 Workflow
User logs in (Student / Recruiter)

Student uploads resume

System analyzes resume using NLP

Skills are extracted

Job matching is performed

Resume score is generated

Job recommendations & skill gaps are displayed

Recruiter views ranked candidates

📂 Project Structure
AI-RESUME-ANALYSIS/
│── app.py
│── templates/
│── static/
│── models/
│── database/
│── requirements.txt
▶️ How to Run
1️⃣ Clone Repository
git clone https://github.com/tamil200613/AI-RESUME-ANALYSIS-AND-JOB-RECOMMENDATION.git
cd AI-RESUME-ANALYSIS-AND-JOB-RECOMMENDATION
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Run Application
python app.py
4️⃣ Open in Browser
http://127.0.0.1:5000/
🧪 Testing
Manual Testing

Functional Testing

Performance Testing

Security Testing

📈 Future Enhancements
Advanced AI models for better accuracy

Resume feedback suggestions

Integration with job portals

Email notifications

Dashboard analytics

🤝 Contributors
Tamilselvan A

Abhinav K

Ranjith K

📜 License
This project is developed for academic purposes.

⭐ Acknowledgment
Thanks to our faculty and institution for guidance and support.
