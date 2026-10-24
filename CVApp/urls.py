# In CVApp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_cv, name='upload_cv'),
    path('signup/', views.hr_signup, name='signup'),
    path('login/', views.hr_login, name='login'),
    path('logout/', views.hr_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/job/create/', views.create_job_requirement, name='create_job'),
    # Route for updating candidate stage:
    path('dashboard/candidate/<int:candidate_id>/stage/', views.update_candidate_stage, name='update_candidate_stage'),
    path('dashboard/user/<int:user_id>/approve/', views.approve_hr_user, name='approve_user'),
    path('dashboard/user/<int:user_id>/reject/', views.reject_hr_user, name='reject_user'),
]