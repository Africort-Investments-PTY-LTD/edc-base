import random
import pytz
import re

from dateutil import parser
from dateutil.relativedelta import relativedelta
from decimal import Decimal, InvalidOperation
from math import ceil

from django.utils import timezone
from django.utils.encoding import force_text
from django.test.utils import override_settings


class ConvertError(Exception):
    pass


tz = pytz.timezone('UTC')

safe_allowed_chars = 'ABCDEFGHKMNPRTUVWXYZ2346789'


def round_up(value, digits):
    ceil(value * (10 ** digits)) / (10 ** digits)


def get_safe_random_string(self, length=12, safe=None, allowed_chars=None):
    safe = True if safe is None else safe
    allowed_chars = (allowed_chars or
                     'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRTUVWXYZ012346789!@#%^&*()?<>.,[]{}')
    if safe:
        allowed_chars = 'ABCDEFGHKMNPRTUVWXYZ2346789'
    return ''.join([random.choice(allowed_chars) for _ in range(length)])


def age(born, reference_datetime):
    """Age is local."""
    if not born:
        raise ValueError('DOB cannot be None.')
    reference_date = timezone.localtime(reference_datetime).date()
    if relativedelta(born, reference_date) > 0:
        raise ValueError('Reference date precedes DOB.')
    return relativedelta(born, reference_date)


def formatted_age(born, reference_datetime=None):
    reference_datetime = reference_datetime or timezone.now()
    reference_date = timezone.localtime(reference_datetime).date()
    if born:
        rdelta = relativedelta(reference_date, born)
        if born > reference_date:
            return '?'
        elif rdelta.years == 0 and rdelta.months <= 0:
            return '%sd' % (rdelta.days)
        elif rdelta.years == 0 and rdelta.months > 0 and rdelta.months <= 2:
            return '%sm%sd' % (rdelta.months, rdelta.days)
        elif rdelta.years == 0 and rdelta.months > 2:
            return '%sm' % (rdelta.months)
        elif rdelta.years == 1:
            m = rdelta.months + 12
            return '%sm' % (m)
        elif rdelta.years > 1:
            return '%sy' % (rdelta.years)
        else:
            raise TypeError(
                'Age template tag missed a case... today - born. '
                'rdelta = {} and {}'.format(rdelta, born))


def get_age_in_days(reference_datetime, dob):
    reference_date = timezone.localtime(reference_datetime).date()
    rdelta = relativedelta(reference_date, dob)
    return rdelta.days


def convert_from_camel(name):
    """Converts from camel case to lowercase divided by underscores."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class Convert(object):

    def __init__(self, value, convert=None, time_format=None):
        self.value = value
        self.convert = False if convert is False else True
        self.time_format = time_format or '%H:%M'

    def to_value(self):
        """Converts a string representation of a value into its original datatype.

        For dates and datetimes always returns a time zone aware datetime."""
        string_value = self.value.strip(' "')
        if self.convert:
            try:
                return self.to_time(string_value)
            except ConvertError:
                pass
            try:
                return self.to_boolean(string_value)
            except ConvertError:
                pass
            try:
                return self.to_decimal(string_value)
            except ConvertError:
                pass
            try:
                return self.to_int(string_value)
            except ConvertError:
                pass
            try:
                return self.to_datetime(string_value)
            except ConvertError:
                pass
            # raise ConvertError('Cannot convert string to value. Got \'{}\''.format(self.value))
        return string_value

    def to_string(self):
        try:
            string_value = self.value.isoformat()
            try:
                self.value.time()
                string_value = '{} {}'.format(string_value, self.value.strftime(self.time_format))
            except AttributeError:
                pass
        except AttributeError:
            string_value = str(self.value)
        return string_value or force_text(self.value)

    def to_time(self, string_value):
        if re.match('^[0-9]{1,2}\:[0-9]{2}$', string_value):
            return string_value
        else:
            raise ConvertError()

    def to_boolean(self, string_value):
        if string_value.lower() in ['true', 'false', 'none']:
            return eval(string_value)
        else:
            raise ConvertError()

    def to_decimal(self, string_value):
        if '.' in string_value:
            try:
                value = Decimal(string_value)
                if str(value) == string_value:
                    return value
            except ValueError:
                pass
            except InvalidOperation:
                pass
        raise ConvertError()

    def to_int(self, string_value):
        try:
            value = int(string_value)
            if str(value) == string_value:
                return value
        except ValueError:
            pass
        raise ConvertError()

    @override_settings(USE_TZ=True)
    def to_datetime(self, string_value):
        """Returns a timezone aware date.

        If you want a naive date, then you will need to convert it to naive yourself."""
        try:
            value = parser.parse(string_value)
            value = timezone.make_aware(value, timezone=pytz.timezone('UTC'))
            return value
        except ValueError:
            pass
        except TypeError:
            pass
        raise ConvertError()
