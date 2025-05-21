"""
WSGI config for trip_planning_sblock project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trip_planning_sblock.settings')

application = get_wsgi_application()
