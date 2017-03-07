import sys

from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings
from django.db.backends.signals import connection_created
from django.core.management.color import color_style
from django.core.exceptions import ImproperlyConfigured

from .address import Address
from .navbar_item import NavbarItem
from .utils import get_utcnow

style = color_style()


def activate_foreign_keys(sender, connection, **kwargs):
    """Enable integrity constraint with sqlite."""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')


class AppConfig(DjangoAppConfig):
    name = 'edc_base'
    institution = 'My Institution'
    project_name = 'My Project Title'
    physical_address = Address()
    postal_address = Address()
    copyright = get_utcnow().year
    license = None
    disclaimer = 'For research purposes only.'
    default_url_name = 'home_url'
    navbars = {
        'default':
        [NavbarItem(
            label='Section',
            app_config_name='edc_base')]}

    def __init__(self, app_name, app_module):
        self._navbars = {}
        super().__init__(app_name, app_module)

    def get_navbars(self):
        return self.navbars

    def ready(self):
        self.navbars = self.get_navbars()
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        connection_created.connect(activate_foreign_keys)
        sys.stdout.write(
            ' * default TIME_ZONE {}.\n'.format(settings.TIME_ZONE))
        if not settings.USE_TZ:
            raise ImproperlyConfigured('EDC requires settings.USE_TZ = True')
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
