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
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from yuzzaz.views import landing

handler404 = 'yuzzaz.views.custom_404_view'

def logout_then_google(request):
    logout(request)
    return redirect('/oauth/login/google-oauth2/?next=/profile/')

import os

def _read_static(relative_path):
    """Find a static file in dev (finders) or prod (STATIC_ROOT)."""
    path_ = finders.find(relative_path)
    if not path_:
        path_ = os.path.join(settings.STATIC_ROOT, relative_path)
    with open(path_, 'r', encoding='utf-8') as f:
        return f.read()

def service_worker(request):
    resp = HttpResponse(_read_static('js/sw.js'), content_type='application/javascript')
    resp['Service-Worker-Allowed'] = '/'
    return resp

def pwa_manifest(request):
    return HttpResponse(_read_static('manifest.json'), content_type='application/manifest+json')


urlpatterns = [
    path('sw.js', service_worker, name='service_worker'),
    path('manifest.json', pwa_manifest, name='pwa_manifest'),
    path('', landing, name='landing'),
    path('admin/', admin.site.urls),
    path('home/', include('yuzzaz.urls')),
    path('tathmini/', include('tathmini.urls')),
    path('dashboard/', include('dashboardd.urls')),
    path('tenant/', include('tenant_portal.urls')),
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=True)),
    path('oauth/login/google/', logout_then_google, name='logout-then-google'),
    path('oauth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
