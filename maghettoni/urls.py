"""
URL configuration for maghettoni project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.static import serve
from yuzzaz.views import landing

handler404 = 'yuzzaz.views.custom_404_view'

def logout_then_google(request):
    logout(request)
    return redirect('/oauth/login/google-oauth2/?next=/profile/')


urlpatterns = [
    path('', landing, name='landing'),
    path('admin/', admin.site.urls),
    path('home/', include('yuzzaz.urls')),
    path('tathmini/', include('tathmini.urls')),
    path('dashboard/', include('dashboardd.urls')),
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=True)),
    path('oauth/login/google/', logout_then_google, name='logout-then-google'),
    path('oauth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
