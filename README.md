📄 ITG CV — AI-Powered HR Recruitment Portal



An intelligent Applicant Tracking System (ATS) built with Django that automates the recruitment pipeline. ITG CV uses the Groq API to instantly screen candidate resumes (PDFs) against custom job requirements, score their compatibility, and hand HR a ranked shortlist.



✨ Features



\- AI-Driven CV Matching: Automatically extracts text from uploaded PDFs and evaluates them against job requirements using high-speed LLMs via Groq (`openai/gpt-oss-20b`).

\- HR Dashboard \& Kanban Pipeline: A clean, responsive interface to track metrics, view candidate scores, and move applicants between "Interview" and "Rejected" stages.

\- Dynamic Job Requirements: HR administrators can define required skills, experience levels, and education for new roles.

\- Secure HR Access: New HR account registrations are locked by default and require approval from an existing administrator before accessing the dashboard.

\- Asynchronous Batch Processing: AI processing is decoupled from the web interface to ensure high reliability and zero UI freezing.



🛠️ Tech Stack



\- Backend: Python, Django, SQLite

\- Frontend: HTML5, CSS3, Vanilla JavaScript (AJAX)

\- AI Integration: Groq API (OpenAI Python SDK)

\- Document Parsing: PyPDF2



\---



🚀 Local Setup \& Installation



Prerequisites

\- Python 3.10+

\- A valid \[Groq API Key](https://console.groq.com/keys)



1\. Clone the repository

```bash

git clone \[https://github.com/MousaAburahma/ITGCVProject.git] cd ITGCVProject


