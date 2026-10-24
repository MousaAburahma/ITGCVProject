from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import JobRequirement, CandidateCV, CandidateNote


# 1. Custom Form for Adding an HR User in Admin
class HRUserCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Work email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
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
        # Use email as the Django username
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# 2. Register customized HR Admin
admin.site.unregister(User)

@admin.register(User)
class HRUserAdmin(BaseUserAdmin):
    add_form = HRUserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Form fields when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password', 'confirm_password', 'is_staff', 'is_superuser'),
        }),
    )

    # Standard edit page for existing users
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


# 3. Existing Models Admin
class CandidateNoteInline(admin.TabularInline):
    model = CandidateNote
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(JobRequirement)
class JobRequirementAdmin(admin.ModelAdmin):
    list_display = ('title', 'experience_level', 'created_by', 'created_at', 'candidate_count')
    list_filter = ('experience_level', 'created_at')
    search_fields = ('title', 'required_skills', 'education', 'created_by__username')
    ordering = ('-created_at',)

    def candidate_count(self, obj):
        return obj.candidates.count()
    candidate_count.short_description = 'Applications'


@admin.register(CandidateCV)
class CandidateCVAdmin(admin.ModelAdmin):
    list_display = (
        'reference_id',
        'full_name',
        'email',
        'job',
        'stage',
        'match_score',
        'processing_status',
        'submitted_at',
    )
    list_filter = ('stage', 'processing_status', 'job', 'submitted_at')
    search_fields = ('reference_id', 'full_name', 'email', 'job__title')
    readonly_fields = ('reference_id', 'submitted_at')
    ordering = ('-submitted_at',)
    inlines = [CandidateNoteInline]

    fieldsets = (
        ('Candidate Information', {
            'fields': ('reference_id', 'full_name', 'email', 'job', 'cv_file', 'submitted_at')
        }),
        ('Recruitment Stage', {
            'fields': ('stage',)
        }),
        ('AI Teammate Handoff & Pipeline Data', {
            'description': 'Fields updated during PDF parsing and AI scoring.',
            'fields': ('processing_status', 'match_score', 'converted_text', 'matched_skills', 'missing_skills')
        }),
    )


@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('candidate__full_name', 'author__username', 'content')
    readonly_fields = ('created_at',)