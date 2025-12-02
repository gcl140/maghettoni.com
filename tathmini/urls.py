from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    # Phone verification endpoints
    path('api/send-verification/', views.send_verification_code, name='send_verification'),
    path('api/verify-phone/', views.verify_phone_code, name='verify_phone'),
    path('api/check-verification/', views.check_phone_verified, name='check_verification'),
    
    # Form submission
    path('api/submit-assessment/', views.submit_assessment, name='submit_assessment'),
    
    # Admin dashboard (optional)
    path('admin/assessment-dashboard/', views.assessment_dashboard, name='assessment_dashboard'),
    
    # Include Django admin URLs
    path('admin/', admin.site.urls),
]