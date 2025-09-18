"""
ASGI config for BiblioUPN321 project (Biblioteca UPN).

Este módulo expone la aplicación ASGI como la variable `application` que
será usada por servidores ASGI (uvicorn, daphne, etc.) para desplegar la
aplicación en entornos asíncronos. Para una aplicación de biblioteca esto
permite servir peticiones HTTP y WebSocket si dichas rutas se añadieran.

Notas operacionales:
- En desarrollo normalmente no necesitas modificar este archivo.
- En despliegue, el servidor ASGI leerá `application` aquí para ejecutar
	la app. Asegúrate de que la variable de entorno `DJANGO_SETTINGS_MODULE`
	esté configurada con las opciones de producción apropiadas.

Referencias: https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Asegura que Django cargue el módulo de configuración por defecto del
# proyecto. En producción puede ponerse a otra configuración (p. ej. settings.prod).
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BiblioUPN321.settings')

# `application` es el objeto ASGI que los servidores usan para enrutar
# y atender las solicitudes. Mantenerlo como variable a nivel de módulo
# es el contrato esperado por los servidores ASGI.
application = get_asgi_application()
