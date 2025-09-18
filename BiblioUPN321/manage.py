#!/usr/bin/env python
"""
Entry point for Django administrative tasks for the Biblioteca UPN project.

Este archivo se mantiene casi sin cambios respecto al esqueleto generado
por Django, pero aquí documentamos su propósito en el contexto de un
software de biblioteca:

- Permite ejecutar comandos administrativos (migraciones, servidor de
    desarrollo, creación de usuarios, carga de datos de pruebas, etc.).
- Define la variable de entorno `DJANGO_SETTINGS_MODULE` que indica el
    módulo de configuración a usar.

Ejemplos de uso desde la línea de comandos:
    python manage.py runserver
    python manage.py migrate
    python manage.py loaddata catalog/fixtures/seed.json

Comentarios sobre variables y funciones:
- `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BiblioUPN321.settings')`:
    Asegura que Django cargue la configuración del proyecto. En despliegues
    o entornos de CI/CD es común sobrescribir esta variable con otra.
- `execute_from_command_line(sys.argv)`:
    Ejecuta el sistema de comandos de Django usando los argumentos pasados
    por la línea de comandos (p. ej. `runserver`, `migrate`).

Como proyecto de biblioteca, usarás `manage.py` para tareas típicas como
importar registros bibliográficos, cargar datos de prueba y gestionar usuarios
de la aplicación.

"""

import os
import sys


def main():
        """Configura el entorno y ejecuta comandos de administración.

        Esta función se invoca cuando se ejecuta `python manage.py ...`.
        - Ajusta la variable de entorno `DJANGO_SETTINGS_MODULE` si no existe.
        - Importa la función `execute_from_command_line` de Django y la llama
            con `sys.argv` para procesar el comando solicitado.

        En el contexto de la biblioteca, los comandos más relevantes suelen ser
        migraciones, creación de datos de prueba y ejecución del servidor local
        para pruebas y demos.
        """
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BiblioUPN321.settings')
        try:
                from django.core.management import execute_from_command_line
        except ImportError as exc:
                # Si Django no está disponible se lanza un ImportError con orientación
                # para el desarrollador (activar virtualenv, instalar dependencias).
                raise ImportError(
                        "Couldn't import Django. Are you sure it's installed and "
                        "available on your PYTHONPATH environment variable? Did you "
                        "forget to activate a virtual environment?"
                ) from exc
        execute_from_command_line(sys.argv)


if __name__ == '__main__':
        main()
