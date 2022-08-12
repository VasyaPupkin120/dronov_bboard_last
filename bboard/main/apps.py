from django.apps import AppConfig
from django.dispatch import Signal
from .utilities import send_activation_notification


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    verbose_name = 'Доска объявлений'

# user_regidstered = Signal(providing_args=['instance'])
# странно, в нашем варианте Django такого ключевого параметра (providing_args) нет...

user_registered = Signal(use_caching=['instance'])

def user_registered_dispatcher(sender, **kwargs):
    send_activation_notification(kwargs['instance'])
