"""
WSGI config for nestora project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application
import socketio

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nestora.settings')

django_application = get_wsgi_application()

# Wrap Django WSGI app with Socket.IO server middleware
from housing.sockets import sio
application = socketio.WSGIApp(sio, django_application)
