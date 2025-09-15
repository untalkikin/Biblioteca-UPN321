from django.contrib.auth.decorators import user_passes_test

def is_cataloger(user):
    return user.is_staff and user.groups.filter(name='Catalogers').exists()

cataloger_required = user_passes_test(is_cataloger)