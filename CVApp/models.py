from django.db import models
from django.contrib.auth.models import User
import uuid

class JobRequirement(models.Model):
    EXPERIENCE_CHOICES = [
        ('entry', 'Internship / entry-level'),
        ('1-3', '1–3 years'),
        ('3-5', '3–5 years'),
        ('5+', '5+ years'),
    ]

    title = models.CharField(max_length=255)
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_CHOICES)
    required_skills = models.TextField(help_text="Comma-separated skills")
    education = models.CharField(max_length=255, blank=True)
    additional_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_postings')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CandidateCV(models.Model):
    STAGE_CHOICES = [
        ('new', 'New'),
        ('interview', 'Interview'),
        ('shortlisted', 'Shortlisted'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]

    PROCESSING_STATUS = [
        ('PENDING', 'Pending Conversion'),
        ('PROCESSING', 'Processing AI'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    # Public submission fields (from cv-upload.html)
    reference_id = models.CharField(max_length=16, unique=True, editable=False)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    job = models.ForeignKey(JobRequirement, on_delete=models.CASCADE, related_name='candidates')
    cv_file = models.FileField(upload_to='cvs/%Y/%m/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Recruitment stage (for Dashboard Kanban / Filtering)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')

    # Teammate handoff contract fields
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='PENDING')
    converted_text = models.TextField(blank=True, help_text="Filled by parsing pipeline")
    match_score = models.IntegerField(default=0, help_text="Filled by matching AI (0-100)")
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if not self.reference_id:
            self.reference_id = f"REF-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.job.title}"


class CandidateNote(models.Model):
    candidate = models.ForeignKey(CandidateCV, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)