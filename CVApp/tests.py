import os
import shutil
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from .models import JobRequirement, CandidateCV
from .forms import HRSignUpForm, CandidateUploadForm

# Use a temporary directory for uploaded files during testing
TEST_MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'test_media')


class HRAuthTests(TestCase):
    def setUp(self):
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.dashboard_url = reverse('dashboard')

    def test_hr_signup_success(self):
        payload = {
            'email': 'hr@itgsolutions.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        }
        form = HRSignUpForm(data=payload)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, 'hr@itgsolutions.com')
        self.assertEqual(user.email, 'hr@itgsolutions.com')
        self.assertTrue(user.check_password('StrongPassword123!'))

    def test_hr_signup_password_mismatch(self):
        payload = {
            'email': 'hr@itgsolutions.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'DifferentPassword123!',
        }
        form = HRSignUpForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_dashboard_requires_login(self):
        response = self.client.get(self.dashboard_url)
        # Unauthenticated users must be redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)


class JobRequirementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='hr@itgsolutions.com',
            email='hr@itgsolutions.com',
            password='Password123!'
        )

    def test_create_job_requirement(self):
        job = JobRequirement.objects.create(
            title='Backend Developer',
            experience_level='1-3',
            required_skills='Python, Django, PostgreSQL',
            education='BSc Computer Science',
            additional_notes='Focus on ORM and query optimization.',
            created_by=self.user
        )
        self.assertEqual(str(job), 'Backend Developer')
        self.assertEqual(job.created_by.username, 'hr@itgsolutions.com')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class CandidateCVUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='hr@itgsolutions.com',
            email='hr@itgsolutions.com',
            password='Password123!'
        )
        self.job = JobRequirement.objects.create(
            title='Network Engineer — Internship',
            experience_level='entry',
            required_skills='Cisco, Subnetting',
            created_by=self.user
        )
        self.upload_url = reverse('upload_cv')

    def tearDown(self):
        # Remove uploaded test files after running tests
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def test_valid_pdf_form_save(self):
        fake_pdf = SimpleUploadedFile(
            name='resume.pdf',
            content=b'%PDF-1.4 fake pdf data',
            content_type='application/pdf'
        )
        data = {
            'full_name': 'Ahmad Zaid',
            'email': 'ahmad@example.com',
            'job': self.job.id,
            'cv_file': fake_pdf,
        }
        form = CandidateUploadForm(data=data, files={'cv_file': fake_pdf})
        self.assertTrue(form.is_valid(), form.errors)
        
        candidate = form.save()
        self.assertTrue(candidate.reference_id.startswith('REF-'))
        # Raw form submission initially defaults to PENDING
        self.assertEqual(candidate.processing_status, 'PENDING')
        self.assertEqual(candidate.stage, 'new')

    def test_invalid_file_extension(self):
        fake_executable = SimpleUploadedFile(
            name='script.exe',
            content=b'malicious binary',
            content_type='application/octet-stream'
        )
        data = {
            'full_name': 'Jane Doe',
            'email': 'jane@example.com',
            'job': self.job.id,
            'cv_file': fake_executable,
        }
        form = CandidateUploadForm(data=data, files={'cv_file': fake_executable})
        self.assertFalse(form.is_valid())
        self.assertIn('cv_file', form.errors)

    @patch('CVApp.views.PdfReader')
    def test_upload_view_pdf_extraction_success(self, mock_pdf_reader):
        # Mock PdfReader returning extracted text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Python Django Developer with networking skills."
        mock_instance = MagicMock()
        mock_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_instance

        fake_pdf = SimpleUploadedFile(
            name='cv.pdf',
            content=b'%PDF-1.4 mock content',
            content_type='application/pdf'
        )
        response = self.client.post(self.upload_url, {
            'full_name': 'Lina Mansour',
            'email': 'lina@example.com',
            'job': self.job.id,
            'cv_file': fake_pdf,
        })
        
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['success'])
        self.assertTrue(json_data['ref'].startswith('REF-'))

        candidate = CandidateCV.objects.get(reference_id=json_data['ref'])
        self.assertEqual(candidate.converted_text, "Python Django Developer with networking skills.")
        # Status must advance to PROCESSING for the AI scoring step
        self.assertEqual(candidate.processing_status, 'PROCESSING')

    @patch('CVApp.views.PdfReader')
    def test_upload_view_pdf_extraction_failure(self, mock_pdf_reader):
        # Mock PdfReader throwing an exception (e.g. corrupted PDF)
        mock_pdf_reader.side_effect = Exception("Corrupted PDF structure")

        fake_pdf = SimpleUploadedFile(
            name='corrupted.pdf',
            content=b'not a valid pdf',
            content_type='application/pdf'
        )
        response = self.client.post(self.upload_url, {
            'full_name': 'Sami Kamal',
            'email': 'sami@example.com',
            'job': self.job.id,
            'cv_file': fake_pdf,
        })

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['success'])

        candidate = CandidateCV.objects.get(reference_id=json_data['ref'])
        # When extraction fails, status must become FAILED
        self.assertEqual(candidate.processing_status, 'FAILED')
        self.assertEqual(candidate.converted_text, "")