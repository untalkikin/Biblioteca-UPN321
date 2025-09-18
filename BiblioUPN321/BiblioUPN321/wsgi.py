"""
WSGI config for BiblioUPN321 project (Biblioteca UPN).

Este módulo expone la aplicación WSGI como la variable `application` que
será utilizada por servidores WSGI (Gunicorn, uWSGI) para desplegar la
aplicación en entornos síncronos. Sigue el contrato estándar de Django para
despliegues WSGI.

En el contexto de una biblioteca, WSGI suele usarse en producción cuando
no se requieren capacidades asíncronas avanzadas. Mantener este archivo
sin cambios suele ser la mejor práctica.

Referencias: https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Establece el módulo de configuración por defecto; en producción puede
# apuntar a una variante optimizada de settings (p. ej. settings.production).
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BiblioUPN321.settings')

# `application` es el callable WSGI que los servidores utilizan para
# procesar solicitudes HTTP entrantes.
application = get_wsgi_application()
