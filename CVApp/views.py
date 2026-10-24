from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from pypdf import PdfReader

from .models import JobRequirement, CandidateCV, CandidateNote
from .forms import HRSignUpForm, CandidateUploadForm, JobRequirementForm


# 1. Public CV Upload View
def upload_cv(request):
    jobs = JobRequirement.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = CandidateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save()

            # Extract text from uploaded PDF
            if candidate.cv_file and candidate.cv_file.name.lower().endswith('.pdf'):
                try:
                    reader = PdfReader(candidate.cv_file.path)
                    extracted_text = "\n\n".join(
                        page.extract_text() or "" for page in reader.pages
                    ).strip()

                    candidate.converted_text = extracted_text
                    
                    # Status is set to PROCESSING to signal the AI matching worker
                    if candidate.converted_text:
                        candidate.processing_status = 'PROCESSING'
                    else:
                        candidate.processing_status = 'FAILED'
                        
                    candidate.save(update_fields=['converted_text', 'processing_status'])
                except Exception:
                    candidate.processing_status = 'FAILED'
                    candidate.save(update_fields=['processing_status'])

            return JsonResponse({
                'success': True,
                'ref': candidate.reference_id,
                'message': "Application submitted successfully."
            })
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return render(request, 'cv-upload.html', {'jobs': jobs})


# 2. HR Signup View
def hr_signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = HRSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to login with a pending parameter instead of logging in
            return redirect('/login/?pending=1')
    else:
        form = HRSignUpForm()
        
    return render(request, 'signup.html', {'form': form})


# 3. HR Login View
def hr_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error_msg = None
    if request.GET.get('pending') == '1':
        error_msg = "Account created successfully. It is awaiting approval from an HR administrator before you can sign in."

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if the user exists but is not yet approved
        inactive_user = User.objects.filter(username=email, is_active=False).first()
        if inactive_user and inactive_user.check_password(password):
            error_msg = "Your account is pending approval by an active HR administrator."
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                error_msg = error_msg or "That email and password combination wasn't recognized."

    return render(request, 'login.html', {'error': error_msg})


# 4. HR Logout View
def hr_logout(request):
    logout(request)
    return redirect('login')


# 5. HR Dashboard View
from django.db.models import Avg

@login_required
def dashboard(request):
    jobs = JobRequirement.objects.filter(created_by=request.user).order_by('-created_at')
    candidates = CandidateCV.objects.filter(job__in=jobs).select_related('job').order_by('-submitted_at')
    
    avg_score = candidates.filter(processing_status='COMPLETED').aggregate(Avg('match_score'))['match_score__avg']
    avg_score_display = f"{round(avg_score)}%" if avg_score is not None else "--"
    
    # Query inactive users awaiting approval
    pending_users = User.objects.filter(is_active=False).order_by('-date_joined')

    context = {
        'jobs': jobs,
        'candidates': candidates,
        'total_candidates': candidates.count(),
        'open_roles_count': jobs.count(),
        'avg_score': avg_score_display,
        'pending_users': pending_users,
        'pending_users_count': pending_users.count(),
    }
    return render(request, 'dashboard.html', context)


# 6. AJAX Endpoint to Save Job Requirements from Dashboard
@login_required
@require_POST
def create_job_requirement(request):
    form = JobRequirementForm(request.POST)
    if form.is_valid():
        job = form.save(commit=False)
        job.created_by = request.user
        job.save()
        return JsonResponse({'success': True, 'job_id': job.id, 'title': job.title})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

# Add this function to CVApp/views.py

# In CVApp/views.py

@login_required
@require_POST
def update_candidate_stage(request, candidate_id):
    candidate = get_object_or_404(CandidateCV, id=candidate_id, job__created_by=request.user)
    new_stage = request.POST.get('stage')
    if new_stage in dict(CandidateCV.STAGE_CHOICES).keys():
        candidate.stage = new_stage
        candidate.save(update_fields=['stage'])
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid stage'}, status=400)


@login_required
@require_POST
def approve_hr_user(request, user_id):
    """Activates the pending user so they can log in."""
    user_to_approve = get_object_or_404(User, id=user_id, is_active=False)
    user_to_approve.is_active = True
    user_to_approve.save(update_fields=['is_active'])
    return JsonResponse({'success': True, 'message': 'User approved successfully.'})


@login_required
@require_POST
def reject_hr_user(request, user_id):
    """Deletes the rejected registration record from the system."""
    user_to_reject = get_object_or_404(User, id=user_id, is_active=False)
    user_to_reject.delete()
    return JsonResponse({'success': True, 'message': 'User registration rejected.'})