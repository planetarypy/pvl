# -*- coding: utf-8 -*-
from six import b
import re
import datetime
import pytz


RE_FRAGMENTS = {
    'int': r'(?:[-+]?[0-9]+)',
    'float': r'(?:[-+]?(?:[0-9]+\.[0-9]*|[0-9]*\.[0-9]+))',
    'day_of_month': r'(0[1-9]|[1-2][0-9]|3[0-1])',
    'day_of_year': r'(00[1-9]|0[1-9][0-9]|[1-2][0-9][0-9]|3[0-5][0-9]|36[0-6])',
    'hour': r'([0-1][0-9]|2[0-3])',
    'minute': r'([0-5][0-9])',
    'month': r'(0[1-9]|1[0-2])',
    # 60 is allowed for leap seconds
    'seconds': r'(?:([0-5][0-9]|60)(?:\.([0-9]*))?)',
    'year': r'([0-9][0-9][0-9][0-9])',
    'tz': r'(Z|z|[+-][0-1]?[0-9]|[+-]2[0-3])'
}

RE_FRAGMENTS['date_month_day'] = r'%(year)s-%(month)s-%(day_of_month)s' % RE_FRAGMENTS  # noqa
RE_FRAGMENTS['date_day_of_year'] = r'%(year)s-%(day_of_year)s' % RE_FRAGMENTS
RE_FRAGMENTS['time'] = r'%(hour)s:%(minute)s(?:\:%(seconds)s)?%(tz)s?' % RE_FRAGMENTS  # noqa

TIME = r'^%(time)s$' % RE_FRAGMENTS
DATE_MONTH_DAY = r'^%(date_month_day)s$' % RE_FRAGMENTS
DATE_DAY_OF_YEAR = r'^%(date_day_of_year)s$' % RE_FRAGMENTS
DATETIME_MONTH_DAY = r'^%(date_month_day)sT%(time)s$' % RE_FRAGMENTS
DATETIME_DAY_OF_YEAR = r'^%(date_day_of_year)sT%(time)s$' % RE_FRAGMENTS


TIME_RE = re.compile(b(TIME))
DATE_MONTH_DAY_RE = re.compile(b(DATE_MONTH_DAY))
DATE_DAY_OF_YEAR_RE = re.compile(b(DATE_DAY_OF_YEAR))
DATETIME_MONTH_DAY_RE = re.compile(b(DATETIME_MONTH_DAY))
DATETIME_DAY_OF_YEAR_RE = re.compile(b(DATETIME_DAY_OF_YEAR))


def is_time(value):
    return bool(TIME_RE.match(value))


def is_date_month_day(value):
    return bool(DATE_MONTH_DAY_RE.match(value))


def is_date_day_of_year(value):
    return bool(DATE_DAY_OF_YEAR_RE.match(value))


def is_datetime_month_day(value):
    return bool(DATETIME_MONTH_DAY_RE.match(value))


def is_datetime_day_of_year(value):
    return bool(DATETIME_DAY_OF_YEAR_RE.match(value))


def is_date(value):
    return is_date_month_day(value) or is_date_day_of_year(value)


def is_datetime(value):
    return is_datetime_month_day(value) or is_datetime_day_of_year(value)


def is_date_or_time(value):
    return is_time(value) or is_date(value) or is_datetime(value)


def parse_time(value):
    match = TIME_RE.match(value)
    hour, minute, second, microsecond, timezone = match.groups()
    second = second or '0'
    microsecond = (microsecond or b'0').ljust(6, b'0')[:6]
    return datetime.time(
        hour=int(hour, 10),
        minute=int(minute, 10),
        second=int(second, 10),
        microsecond=int(microsecond, 10),
        tzinfo=parse_timezone(timezone),
    )


def parse_date_month_day(value):
    year, month, day = DATE_MONTH_DAY_RE.match(value).groups()
    return datetime.date(
        year=int(year, 10),
        month=int(month, 10),
        day=int(day, 10),
    )


def parse_date_day_of_year(value):
    year, days = DATE_DAY_OF_YEAR_RE.match(value).groups()
    year = int(year)
    days = int(days) - 1
    return datetime.date(year, 1, 1) + datetime.timedelta(days=days)


def parse_datetime_month_day(value):
    date, time = value.split(b'T')
    return datetime.datetime.combine(
        parse_date_month_day(date),
        parse_time(time),
    )


def parse_datetime_day_of_year(value):
    date, time = value.split(b'T')
    return datetime.datetime.combine(
        parse_date_day_of_year(date),
        parse_time(time),
    )


def parse_timezone(timezone):
    if not timezone:
        return None

    if timezone.upper() == b'Z':
        return pytz.utc

    offset = int(timezone, 10)
    if offset == 0:
        return pytz.utc

    return pytz.FixedOffset(60 * offset)


def parse_datetime(value):
    if is_time(value):
        return parse_time(value)

    if is_date_month_day(value):
        return parse_date_month_day(value)

    if is_date_day_of_year(value):
        return parse_date_day_of_year(value)

    if is_datetime_month_day(value):
        return parse_datetime_month_day(value)

    if is_datetime_day_of_year(value):
        return parse_datetime_day_of_year(value)

    raise ValueError('not a date or time')
