import sys
import os

# Project home directory
project_home = '/home/maghsrtc/maghettoni.com'
if project_home not in sys.path:
    sys.path.append(project_home)

# Django app directory (contains settings.py)
app_folder = os.path.join(project_home, 'maghettoni')
if app_folder not in sys.path:
    sys.path.append(app_folder)

# Set Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'maghettoni.settings'

# Activate virtualenv
activate_env = '/home/maghsrtc/virtualenv/maghettoni.com/3.9/bin/activate_this.py'
with open(activate_env) as f:
    exec(f.read(), dict(__file__=activate_env))

# Get WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
