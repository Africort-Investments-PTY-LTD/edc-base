import arrow
import sys

from dateutil.relativedelta import relativedelta

from django.apps import apps as django_apps
from django.core.management.color import color_style

from edc_consent.site_consents import site_consents
from datetime import timedelta


class DatesTestMixin:

    """A mixin for tests that changes the protocol start and end dates to be in the past.

    Also changes the consent periods for all registered consents relative to the changed
    study open/close dates.

    Use get_utcnow to return the study open date."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        style = color_style()
        sys.stdout.write(
            style.NOTICE(
                '\n{}. Overwriting study open/close and consent.start/end dates '
                'for tests only.\n'.format(cls.__name__)))
        study_open_datetime = django_apps.app_configs['edc_protocol'].study_open_datetime
        study_close_datetime = django_apps.app_configs['edc_protocol'].study_close_datetime
        django_apps.app_configs['edc_protocol']._original_study_open_datetime = study_open_datetime
        django_apps.app_configs['edc_protocol']._original_study_close_datetime = study_close_datetime
        study_open_datetime = arrow.Arrow.fromdatetime(
            study_open_datetime, study_open_datetime.tzinfo).to('utc').datetime
        study_close_datetime = arrow.Arrow.fromdatetime(
            study_close_datetime, study_close_datetime.tzinfo).to('utc').datetime
        duration_delta = relativedelta(study_close_datetime, study_open_datetime)
        django_apps.app_configs['edc_protocol'].study_open_datetime = study_open_datetime - duration_delta
        django_apps.app_configs['edc_protocol'].study_close_datetime = study_open_datetime
        edc_protocol_app_config = django_apps.get_app_config('edc_protocol')
        study_open_datetime = edc_protocol_app_config.study_open_datetime
        study_close_datetime = edc_protocol_app_config.study_close_datetime
        sys.stdout.write(style.NOTICE(' * test study open datetime: {}\n'.format(study_open_datetime)))
        sys.stdout.write(style.NOTICE(' * test study close datetime: {}\n'.format(study_close_datetime)))
        testconsents = []

        previous_consent_end_date = None
        for index, consent in enumerate(site_consents.registry):
            tdelta = consent.start - study_open_datetime
            consent_period_tdelta = consent.end - consent.start
            consent.end = consent.start + consent_period_tdelta - timedelta(minutes=24 * 60)
            if index == 0:
                consent.start = consent.start - tdelta
            else:
                consent.start = previous_consent_end_date + relativedelta(days=1)
            sys.stdout.write(style.NOTICE(' * {}: {} - {}\n'.format(consent.name, consent.start, consent.end)))
            previous_consent_end_date = consent.end
            testconsents.append(consent)
        site_consents.backup_registry()
        for consent in testconsents:
            site_consents.register(consent)

    @classmethod
    def tearDownClass(cls):
        """Restores edc_protocol app_config open/close dates and edc_consent site_consents registry."""
        super().tearDownClass()
        style = color_style()
        study_open_datetime = django_apps.app_configs['edc_protocol']._original_study_open_datetime
        study_close_datetime = django_apps.app_configs['edc_protocol']._original_study_close_datetime
        django_apps.app_configs['edc_protocol'].study_open_datetime = study_open_datetime
        django_apps.app_configs['edc_protocol'].study_close_datetime = study_close_datetime
        site_consents.restore_registry()
        sys.stdout.write(style.NOTICE('\n * restored original values\n'))

    def get_utcnow(self):
        """Returns the earliest date allowed."""
        return self.study_open_datetime

    @property
    def study_open_datetime(self):
        edc_protocol_app_config = django_apps.get_app_config('edc_protocol')
        return edc_protocol_app_config.study_open_datetime

    @property
    def study_close_datetime(self):
        edc_protocol_app_config = django_apps.get_app_config('edc_protocol')
        return edc_protocol_app_config.study_close_datetime
