#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  <Tên bạn / PTL-2026>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <https://www.gnu.org/licenses/>.
#
"""
Vietnamese lunar calendar conversion.

This module lives in ``gramps/gen/lib/`` (next to ``gcalendar.py``), not in
``gramps/gen/datehandler/``. The conversion between a Serial Day Number
(SDN) and a Vietnamese lunar date is pure arithmetic with no locale
dependency, so it belongs in the generic ``gen/lib`` layer, exactly like
``hebrew_sdn``/``hebrew_ymd`` or ``islamic_sdn``/``islamic_ymd`` in
``gcalendar.py``. Locale-specific parsing/formatting of Vietnamese lunar
dates (e.g. "ngay 1 thang 1 (nhuan) nam Giap Thin") belongs in
``gen/datehandler/_date_vi.py``, which may import from here, never the
other way around.

The astronomical part of this module (new moon / solar term detection) is
based on the Vietnamese lunar calendar algorithm developed by Ho Ngoc Duc,
adapted from the original Java implementation. The Vietnamese time zone is
fixed at UTC+7, matching the reference algorithm.

Design decisions for V1
------------------------
1. Gregorian/Julian conversion is delegated to Gramps' own
   ``gregorian_sdn``/``gregorian_ymd`` (see below) instead of a
   reimplementation of Ho Ngoc Duc's Gregorian<->JD formulas. Two reasons:

   a. Gramps' ``Date.CAL_GREGORIAN`` is a *proleptic* Gregorian calendar:
      it is applied uniformly to every year, and never silently switches
      to the Julian calendar for dates before 1582 the way the original
      Ho Ngoc Duc algorithm does. Reusing ``gregorian_sdn``/``gregorian_ymd``
      keeps the Vietnamese lunar calendar numerically consistent with
      every other calendar Gramps supports.
   b. The original Ho Ngoc Duc Gregorian<->JD formulas, as ported, computed
      the wrong day count across century years that are *not* leap years
      (1700, 1800, 1900, 2100, ...): tested against ``gregorian_sdn``, dates
      after 28 February in 1900 were off by one day. ``gregorian_sdn``/
      ``gregorian_ymd`` are the versions already exercised by the rest of
      Gramps and do not have this bug, so delegating to them fixes it.

2. Gramps' ``Date.dateval`` tuple has no slot for a "this is a leap month"
   flag (unlike, say, the Hebrew calendar's embolismic years, which do not
   need a per-instance flag). As a result:

   - ``vietnamese_sdn(year, month, day, leap=True)`` *can* compute the
     correct SDN for a leap-month date when called directly.
   - But ``Date._calendar_convert[calendar](year, month, day)`` is always
     called with exactly three positional arguments elsewhere in
     ``date.py``, so ``leap`` can never be set to ``True`` through the
     normal ``Date`` API.
   - ``vietnamese_ymd()`` (SDN -> lunar y/m/d) does not return whether the
     resulting month is a leap month, for the same reason.

   This is a known, accepted V1 limitation, not an oversight: a leap month
   is indistinguishable from the regular month of the same number until
   ``Date`` itself gains a place to store that flag. Do not silently
   "fix" this here without a corresponding, broader change to
   ``Date.dateval``.
"""

from dataclasses import dataclass
from datetime import date
from math import floor, pi, sin

from .gcalendar import gregorian_sdn, gregorian_ymd

# Vietnamese local time zone: UTC+7.
TIME_ZONE = 7.0

# Julian day of the reference new moon used by the algorithm.
NEW_MOON_BASE = 2415021.076998695

# Mean synodic month.
SYNODIC_MONTH = 29.530588853


@dataclass(frozen=True)
class LunarDate:
    """A Vietnamese lunar calendar date."""

    year: int
    month: int
    day: int
    is_leap_month: bool = False


# Returned for input that cannot be converted (e.g. the (-4712, 1, 1)
# default of an uninitialised Date). Kept as a single instance so callers
# can compare against it directly if needed.
EMPTY_LUNAR_DATE = LunarDate(0, 0, 0, False)


def _int(value: float) -> int:
    """Return the mathematical floor of a number."""
    return floor(value)


# -------------------------------------------------------------------------
#
# Gregorian <-> SDN bridge
#
# These two functions used to contain an independent, hand-rolled
# reimplementation of the Ho Ngoc Duc Gregorian/Julian <-> Julian Day
# formulas. They now delegate to Gramps' own ``gregorian_sdn``/
# ``gregorian_ymd`` (see the module docstring for why). The argument and
# return order below (day, month, year) is kept as-is so the astronomical
# functions further down do not need to change.
#
# -------------------------------------------------------------------------
def _jd_from_date(day: int, month: int, year: int) -> int:
    """Convert a proleptic Gregorian date to an SDN-style day number.

    This is the same numbering as every other Gramps calendar
    (``gregorian_sdn``, ``julian_sdn``, ...): an integer count of days,
    contiguous, with no timezone or fractional component.
    """
    return gregorian_sdn(year, month, day)


def _universal_from_jd(day_number: float) -> tuple[int, int, int]:
    """Convert an SDN-style day number back to a Gregorian date.

    Returns ``(day, month, year)`` to match the original module's
    convention (callers below do ``date(*reversed(...))``).
    """
    year, month, day = gregorian_ymd(_int(day_number))
    return day, month, year


def _local_from_jd(jd: float) -> tuple[int, int, int]:
    """Convert a real-valued day number to a Vietnamese local date.

    ``jd`` may carry a fractional part coming from the UTC+7 timezone
    shift used elsewhere in this module; it is resolved to a whole day
    before being handed to ``_universal_from_jd``.
    """
    return _universal_from_jd(jd + TIME_ZONE / 24.0)


def _new_moon(k: int) -> float:
    """Calculate the Julian day of new moon number k.

    This is the NewMoon() function from Ho Ngoc Duc's algorithm.
    """
    t = k / 1236.85
    t2 = t * t
    t3 = t2 * t
    dr = pi / 180.0

    jd1 = 2415020.75933 + SYNODIC_MONTH * k + 0.0001178 * t2 - 0.000000155 * t3

    jd1 += 0.00033 * sin((166.56 + 132.87 * t - 0.009173 * t2) * dr)

    m = 359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3

    m_pr = 306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3

    f = 21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3

    c1 = (
        (0.1734 - 0.000393 * t) * sin(m * dr)
        + 0.0021 * sin(2 * m * dr)
        - 0.4068 * sin(m_pr * dr)
        + 0.0161 * sin(2 * m_pr * dr)
        - 0.0004 * sin(3 * m_pr * dr)
        + 0.0104 * sin(2 * f * dr)
        - 0.0051 * sin((m + m_pr) * dr)
        - 0.0074 * sin((m - m_pr) * dr)
        + 0.0004 * sin((2 * f + m) * dr)
        - 0.0004 * sin((2 * f - m) * dr)
        - 0.0006 * sin((2 * f + m_pr) * dr)
        + 0.0010 * sin((2 * f - m_pr) * dr)
        + 0.0005 * sin((2 * m_pr + m) * dr)
    )

    if t < -11:
        delta_t = (
            0.001
            + 0.000839 * t
            + 0.0002261 * t2
            - 0.00000845 * t3
            - 0.000000081 * t * t3
        )
    else:
        delta_t = -0.000278 + 0.000265 * t + 0.000262 * t2

    return jd1 + c1 - delta_t


def _get_new_moon_day(k: int) -> int:
    """Return the local Vietnamese calendar day containing new moon k."""
    return _int(_new_moon(k) + 0.5 + TIME_ZONE / 24.0)


def _sun_longitude(jd: float) -> float:
    """Calculate the Sun's true longitude in radians."""
    # 2000-01-01 12:00 UTC in astronomical Julian Date.
    j2000 = 2451545.0

    t = (jd - j2000) / 36525.0
    t2 = t * t
    dr = pi / 180.0

    m = 357.52910 + 35999.05030 * t - 0.0001559 * t2 - 0.00000048 * t * t2

    l0 = 280.46645 + 36000.76983 * t + 0.0003032 * t2

    dl = (1.914600 - 0.004817 * t - 0.000014 * t2) * sin(dr * m)

    dl += (0.019993 - 0.000101 * t) * sin(2 * dr * m)

    dl += 0.000290 * sin(3 * dr * m)

    longitude = (l0 + dl) * dr

    return longitude - 2 * pi * _int(longitude / (2 * pi))


def _get_sun_longitude(day_number: int) -> int:
    """Return the 30-degree solar-longitude sector."""
    jd = day_number - 0.5 - TIME_ZONE / 24.0
    return _int(_sun_longitude(jd) / pi * 6)


def _get_lunar_month_11(year: int) -> int:
    """Return the first day of lunar month 11 for a Gregorian year."""
    off = _jd_from_date(31, 12, year) - 2415021

    k = _int(off / SYNODIC_MONTH)
    new_moon_day = _get_new_moon_day(k)

    sun_longitude = _get_sun_longitude(new_moon_day)

    if sun_longitude >= 9:
        new_moon_day = _get_new_moon_day(k - 1)

    return new_moon_day


def _get_leap_month_offset(a11: int) -> int:
    """Return the position of the leap month after lunar month 11."""
    k = _int(0.5 + (a11 - NEW_MOON_BASE) / SYNODIC_MONTH)

    last = 0
    i = 1

    arc = _get_sun_longitude(_get_new_moon_day(k + i))

    while True:
        last = arc
        i += 1

        arc = _get_sun_longitude(_get_new_moon_day(k + i))

        if arc == last or i >= 14:
            break

    return i - 1


def gregorian_to_lunar(
    year: int,
    month: int,
    day: int,
) -> LunarDate:
    """Convert a Gregorian date to a Vietnamese lunar date."""
    # Chan cac gia tri khong hop le (vi du nam -4712 mac dinh khi Date
    # chua duoc khoi tao) thay vi de date() nem ValueError ra ngoai.
    if year < 1 or year > 9999 or month < 1 or month > 12 or day < 1 or day > 31:
        return EMPTY_LUNAR_DATE

    try:
        date(year, month, day)
    except ValueError:
        return EMPTY_LUNAR_DATE

    day_number = _jd_from_date(day, month, year)

    k = _int((day_number - NEW_MOON_BASE) / SYNODIC_MONTH)

    month_start = _get_new_moon_day(k + 1)

    if month_start > day_number:
        month_start = _get_new_moon_day(k)

    a11 = _get_lunar_month_11(year)
    b11 = a11

    if a11 >= month_start:
        lunar_year = year
        a11 = _get_lunar_month_11(year - 1)
    else:
        lunar_year = year + 1
        b11 = _get_lunar_month_11(year + 1)

    lunar_day = day_number - month_start + 1

    diff = _int((month_start - a11) / 29)

    lunar_month = diff + 11
    is_leap_month = False

    if b11 - a11 > 365:
        leap_month_diff = _get_leap_month_offset(a11)

        if diff >= leap_month_diff:
            lunar_month = diff + 10

            if diff == leap_month_diff:
                is_leap_month = True

    if lunar_month > 12:
        lunar_month -= 12

    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1

    return LunarDate(
        year=lunar_year,
        month=lunar_month,
        day=lunar_day,
        is_leap_month=is_leap_month,
    )


def lunar_to_gregorian(lunar_date: LunarDate) -> date:
    """Convert a Vietnamese lunar date to a Gregorian date."""
    lunar_year = lunar_date.year
    lunar_month = lunar_date.month

    if not 1 <= lunar_month <= 12:
        raise ValueError(f"Invalid lunar month: {lunar_month}")

    if not 1 <= lunar_date.day <= 30:
        raise ValueError(f"Invalid lunar day: {lunar_date.day}")

    if lunar_month < 11:
        a11 = _get_lunar_month_11(lunar_year - 1)
        b11 = _get_lunar_month_11(lunar_year)
    else:
        a11 = _get_lunar_month_11(lunar_year)
        b11 = _get_lunar_month_11(lunar_year + 1)

    off = lunar_month - 11

    if off < 0:
        off += 12

    if b11 - a11 > 365:
        leap_month_diff = _get_leap_month_offset(a11)
        leap_month = leap_month_diff - 2

        if leap_month < 0:
            leap_month += 12

        if lunar_date.is_leap_month and lunar_month != leap_month:
            raise ValueError("Specified lunar month is not a leap month")

        if lunar_date.is_leap_month or off >= leap_month_diff:
            off += 1

    k = _int(0.5 + (a11 - NEW_MOON_BASE) / SYNODIC_MONTH)

    month_start = _get_new_moon_day(k + off)

    gregorian_day = _local_from_jd(month_start + lunar_date.day - 1)

    result = date(*reversed(gregorian_day))

    # Validate that the requested lunar day actually exists.
    converted = gregorian_to_lunar(
        result.year,
        result.month,
        result.day,
    )

    if converted != lunar_date:
        raise ValueError(f"Invalid Vietnamese lunar date: {lunar_date}")

    return result


def vietnamese_sdn(year: int, month: int, day: int, leap: bool = False) -> int:
    """Convert a Vietnamese lunar date to a serial day number (SDN).
    Returns 0 for any input that cannot be converted (out-of-range year,
    non-existent lunar day, invalid leap-month combination...), instead of
    raising. This mirrors every other Gramps calendar's sdn function, all
    of which are total functions that never raise - Date._calc_sort_value()
    calls this unconditionally, including while the user is still typing
    a provisional/incomplete date in the GUI, so it must never crash.
    Use lunar_to_gregorian() directly if you need the ValueError instead.
    """
    lunar_date = LunarDate(
        year=year,
        month=month,
        day=day,
        is_leap_month=leap,
    )
    try:
        gregorian_date = lunar_to_gregorian(lunar_date)
    except ValueError:
        return 0

    return _jd_from_date(
        gregorian_date.day,
        gregorian_date.month,
        gregorian_date.year,
    )


def vietnamese_ymd(sdn: int) -> tuple[int, int, int]:
    """Convert a serial day number to a Vietnamese lunar date.

    NOTE (V1 limitation, see module docstring point 2): this does not
    and cannot report whether the result falls in a leap month, because
    ``Date.dateval`` has no slot to carry that information back to the
    caller. A date in a leap month is returned with the same month
    number as the regular month it duplicates.
    """
    if not sdn or sdn <= 0:
        return (0, 0, 0)

    day, month, year = _universal_from_jd(sdn)

    lunar_date = gregorian_to_lunar(
        year,
        month,
        day,
    )

    return (
        lunar_date.year,
        lunar_date.month,
        lunar_date.day,
    )


def vietnamese_lunar_valid(date_tuple):
    """
    Check whether date_tuple (day, month, year) is a valid
    Vietnamese lunar date.
    """
    if not isinstance(date_tuple, (tuple, list)) or len(date_tuple) < 3:
        return False

    day, month, year = date_tuple[0], date_tuple[1], date_tuple[2]

    if year == 0:
        return False

    if not 1 <= month <= 12:
        return False

    if not 1 <= day <= 30:
        return False

    # TODO:
    # Use Vietnamese Lunar calculation to determine whether
    # this month has 29 or 30 days.
    #
    # This part should use the existing lunar algorithm,
    # not duplicate calendar calculation here.

    return True
