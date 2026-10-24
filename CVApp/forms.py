from django import forms
from django.contrib.auth.models import User
from .models import JobRequirement, CandidateCV

class HRSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        # New users remain inactive until an existing HR user approves them
        user.is_active = False
        if commit:
            user.save()
        return user


class JobRequirementForm(forms.ModelForm):
    class Meta:
        model = JobRequirement
        fields = ['title', 'experience_level', 'required_skills', 'education', 'additional_notes']


class CandidateUploadForm(forms.ModelForm):
    class Meta:
        model = CandidateCV
        fields = ['full_name', 'email', 'job', 'cv_file']

    def clean_cv_file(self):
        file = self.cleaned_data.get('cv_file')
        if file:
            valid_extensions = ['.pdf']
            if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError("File must be a PDF document only (.pdf).")
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must not exceed 5 MB.")
        return file