"""
Configuración de Django para el proyecto Biblioteca UPN (BiblioUPN321).

Este archivo contiene las opciones principales para ejecutar la aplicación
de catálogo bibliográfico: rutas base, aplicaciones instaladas, base de
datos y configuración estática. Está documentado con foco en las
necesidades de un sistema de biblioteca.

IMPORTANTE: No debe exponerse `SECRET_KEY` en repositorios públicos.
Usa variables de entorno para producción y un archivo separado de
configuración si es necesario.
"""

from pathlib import Path

# Directorio base del proyecto (dos niveles arriba: proyecto raíz)
# Usado para construir rutas absolutas (archivos estáticos, base de datos, etc.).
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------
# Seguridad y despliegue
# ---------------------------------------------------------

# Clave secreta para criptografía y sesiones. En producción, usar
# una variable de entorno o un secreto administrado.
SECRET_KEY = 'django-insecure-vzaj-jzqnwzoaggn@+$bnmf$d4xetz2yxx40wzzr-n%amz7=yy'

# Indicador de debug. False en producción para evitar fuga de información.
DEBUG = True

# Hosts permitidos. En despliegue añadir el dominio o IP del servidor.
ALLOWED_HOSTS = []


# ---------------------------------------------------------
# Aplicaciones y middlewares
# ---------------------------------------------------------

INSTALLED_APPS = [
    # Apps de Django necesarias
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # App local principal que contiene el catálogo de la biblioteca
    'catalog.apps.CatalogConfig',
    'widget_tweaks',
]

# Middlewares ejecutados por cada petición. Mantener orden recomendado.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Módulo que define las rutas de nivel raíz del proyecto
ROOT_URLCONF = 'BiblioUPN321.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # <- IMPORTANTE
        "APP_DIRS": True,                   # <- normalmente True
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Rutas de login/logout
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = 'catalog:record_list'
LOGOUT_REDIRECT_URL = 'catalog:record_list'

# Callable WSGI para despliegues síncronos (Gunicorn/uWSGI)
WSGI_APPLICATION = 'BiblioUPN321.wsgi.application'


# ---------------------------------------------------------
# Base de datos
# ---------------------------------------------------------
# Por simplicidad en desarrollo se usa SQLite. Para producción usar
# PostgreSQL o similar y leer credenciales de variables de entorno.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ---------------------------------------------------------
# Validación y seguridad de contraseñas
# ---------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ---------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------
LANGUAGE_CODE = 'en-us'

# Zona horaria del servidor; ajustar a la zona donde corre la biblioteca.
TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ---------------------------------------------------------
# Archivos estáticos
# ---------------------------------------------------------
# URL y rutas para servir CSS/JS/Imágenes. En producción usar
# `collectstatic` para recopilar en `STATIC_ROOT` y servir con un CDN
# o a través del servidor web.
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # rutas de desarrollo (assets del proyecto)
STATIC_ROOT = BASE_DIR / "staticfiles"    # destino de `collectstatic`

# Almacenamiento que comprime y cachea archivos estáticos para producción.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# ---------------------------------------------------------
# Configuraciones generales
# ---------------------------------------------------------
# Tipo de campo por defecto para claves primarias en modelos.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media (archivos subidos por usuarios, imágenes de portadas y QRs)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
