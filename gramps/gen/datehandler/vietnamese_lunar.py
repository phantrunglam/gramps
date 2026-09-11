"""
Vietnamese lunar calendar conversion.

This module is based on the Vietnamese lunar calendar algorithm
developed by Ho Ngoc Duc.

The implementation is adapted from the original Java algorithm
to Python. The Vietnamese time zone is UTC+7.

The module provides conversion between Gregorian dates and
Vietnamese lunar dates.

This is intentionally a small, self-contained module for V1.
"""

from dataclasses import dataclass
from datetime import date
from math import floor, pi, sin

# Vietnamese local time zone: UTC+7.
TIME_ZONE = 7.0

# Julian day of the reference new moon used by the algorithm.
NEW_MOON_BASE = 2415021.076998695

# Mean synodic month.
SYNODIC_MONTH = 29.530588853

# GRAMPS_SDN_OFFSET = 32045


@dataclass(frozen=True)
class LunarDate:
    """A Vietnamese lunar calendar date."""

    year: int
    month: int
    day: int
    is_leap_month: bool = False


def _int(value: float) -> int:
    """Return the mathematical floor of a number."""
    return floor(value)


def _jd_from_date(day: int, month: int, year: int) -> int:
    """Convert a Gregorian date to Julian day number.

    This follows the Julian/Gregorian calendar conversion used
    by Ho Ngoc Duc's algorithm.
    """
    if (
        year > 1582
        or (year == 1582 and month > 10)
        or (year == 1582 and month == 10 and day > 14)
    ):
        jd = (
            367 * year
            - _int(7 * (year + _int((month + 9) / 12)) / 4)
            - _int(3 * (_int((year + _int((month - 9) / 7)) / 100) + 1) / 4)
            + _int(275 * month / 9)
            + day
            + 1721028.5
        )
    else:
        jd = (
            367 * year
            - _int(7 * (year + 5001 + _int((month - 9) / 7)) / 4)
            + _int(275 * month / 9)
            + day
            + 1729776.5
        )

    return _int(jd + 0.5)


def _universal_from_jd(jd: float) -> tuple[int, int, int]:
    """Convert a Julian day to Gregorian date."""
    z = _int(jd + 0.5)
    f = (jd + 0.5) - z

    if z < 2299161:
        a = z
    else:
        alpha = _int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - _int(alpha / 4)

    b = a + 1524
    c = _int((b - 122.1) / 365.25)
    d = _int(365.25 * c)
    e = _int((b - d) / 30.6001)

    day = _int(b - d - _int(30.6001 * e) + f)

    if e < 14:
        month = e - 1
    else:
        month = e - 13

    if month < 3:
        year = c - 4715
    else:
        year = c - 4716

    return day, month, year


def _local_to_jd(day: int, month: int, year: int) -> float:
    """Convert local Vietnamese midnight to Julian day."""
    return _jd_from_date(day, month, year) - TIME_ZONE / 24.0


def _local_from_jd(jd: float) -> tuple[int, int, int]:
    """Convert Julian day to Vietnamese local date."""
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
    # Julian Day Number of Gregorian 2000-01-01.
    # JDN = 2451545.
    #
    # The astronomical calculations use Julian Date (JD),
    # where 2000-01-01 12:00 UTC = 2451545.0.
    J2000 = 2451545.0

    t = (jd - J2000) / 36525.0
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
    # Chặn các năm không hợp lệ (như năm -4712 mặc định khi Date chưa khởi tạo)
    if year < 1 or year > 9999 or month < 1 or month > 12 or day < 1 or day > 31:
        # Trả về giá trị mặc định an toàn thay vì crash
        return (0, 0, 0, False)
    try:
        date(year, month, day)
    except ValueError as exc:
        return (0, 0, 0, False)
        # raise ValueError(
        #     f"Invalid Gregorian date: {year}-{month:02d}-{day:02d}"
        # ) from exc

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
    """Convert a Vietnamese lunar date to a serial day number (JDN)."""
    lunar_date = LunarDate(
        year=year,
        month=month,
        day=day,
        is_leap_month=leap,
    )

    gregorian_date = lunar_to_gregorian(lunar_date)

    return _jd_from_date(
        gregorian_date.day,
        gregorian_date.month,
        gregorian_date.year,
    )


def vietnamese_ymd(sdn: int) -> tuple[int, int, int]:
    """Convert a serial day number to a Vietnamese lunar date."""
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
