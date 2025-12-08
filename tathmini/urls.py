from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('api/send-verification/', views.send_verification_code, name='send_verification'),
    path('api/verify-phone/', views.verify_phone_code, name='verify_phone'),
    path('api/check-verification/', views.check_phone_verified, name='check_verification'),
    path('api/submit-assessment/', views.submit_assessment, name='submit_assessment'),
    path('admin/assessment-dashboard/', views.assessment_dashboard, name='assessment_dashboard'),
    path('subscribe/', views.subscribe, name='subscribe'),
    
]