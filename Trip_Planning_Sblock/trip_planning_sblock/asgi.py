"""
ASGI config for trip_planning_sblock project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trip_planning_sblock.settings')

application = get_asgi_application()
