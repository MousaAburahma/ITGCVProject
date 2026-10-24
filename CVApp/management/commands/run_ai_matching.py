import os
import json
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from openai import OpenAI
from CVApp.models import CandidateCV


class Command(BaseCommand):
    help = 'Evaluates pending candidate CVs against job requirements using Groq.'

    def handle(self, *args, **options):
        api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("GROQ_API_KEY not found in settings or .env file!"))
            return

        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
        )

        # Active Groq models from your account
        selected_model = "openai/gpt-oss-20b"
        self.stdout.write(self.style.SUCCESS(f"Using Groq model: {selected_model}"))

        # Fetch both PROCESSING and previously FAILED candidates to re-evaluate them
        candidates = CandidateCV.objects.filter(
            processing_status__in=['PROCESSING', 'FAILED']
        ).exclude(converted_text__isnull=True).exclude(converted_text='')

        count = candidates.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No candidate CVs found to process."))
            return

        self.stdout.write(self.style.NOTICE(f"Found {count} candidate(s) to process."))

        for candidate in candidates:
            job = candidate.job
            if not job:
                self.stdout.write(self.style.WARNING(f"Candidate ID {candidate.id} has no linked job requirement. Skipping."))
                continue

            self.stdout.write(f"Processing Candidate ID {candidate.id} for job: {job.title}...")

            prompt_content = f"""
            You are an expert technical recruiter. Evaluate the candidate resume against the job requirements.

            === JOB REQUIREMENTS ===
            Job Title: {job.title}
            Experience Level: {job.experience_level}
            Required Skills: {job.required_skills}
            Education: {job.education}
            Additional Notes: {job.additional_notes}

            === CANDIDATE RESUME TEXT ===
            {candidate.converted_text}

            === INSTRUCTIONS ===
            Return strictly a JSON object with this exact structure:
            {{
              "match_score": <integer from 0 to 100>,
              "matched_skills": [<list of matched skill strings>],
              "missing_skills": [<list of missing skill strings>]
            }}
            """

            try:
                completion = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a recruitment assistant. Output strictly valid JSON matching the requested keys."
                        },
                        {"role": "user", "content": prompt_content}
                    ],
                    response_format={"type": "json_object"}
                )

                response_text = completion.choices[0].message.content
                result = json.loads(response_text)

                candidate.match_score = int(result.get("match_score", 0))
                candidate.matched_skills = result.get("matched_skills", [])
                candidate.missing_skills = result.get("missing_skills", [])
                candidate.processing_status = 'COMPLETED'

                candidate.save(update_fields=['match_score', 'matched_skills', 'missing_skills', 'processing_status'])
                
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully evaluated Candidate ID {candidate.id}. Score: {candidate.match_score}/100"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing Candidate ID {candidate.id}: {str(e)}"))
                candidate.processing_status = 'FAILED'
                candidate.save(update_fields=['processing_status'])

            time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Batch evaluation complete!"))