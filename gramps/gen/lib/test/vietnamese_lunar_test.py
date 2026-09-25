#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  <Ten ban / PTL-2026>
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
Unit tests for gramps.gen.lib.vietnamese_lunar

Location: gramps/gen/lib/test/vietnamese_lunar_test.py
(next to gcalendar_test.py / date_test.py, matching where the module
under test itself lives)

Run with:
    python3 -m unittest gramps.gen.lib.test.vietnamese_lunar_test -v
or, from the repository root, simply:
    python3 -m pytest gramps/gen/lib/test/vietnamese_lunar_test.py -v
"""

import unittest
import datetime

from gramps.gen.lib.vietnamese_lunar import (
    LunarDate,
    EMPTY_LUNAR_DATE,
    gregorian_to_lunar,
    lunar_to_gregorian,
    vietnamese_sdn,
    vietnamese_ymd,
    vietnamese_lunar_valid,
)
from gramps.gen.lib.gcalendar import gregorian_sdn, gregorian_ymd
from gramps.gen.lib.date import Date


# ---------------------------------------------------------------------------
#
# Known reference dates (Tet / Lunar New Year), independently verifiable
# against any published Vietnamese lunar calendar.
#
# ---------------------------------------------------------------------------
KNOWN_TET_DATES = {
    # lunar_year: (gregorian_year, gregorian_month, gregorian_day)
    2000: (2000, 2, 5),
    2020: (2020, 1, 25),
    2023: (2023, 1, 22),
    2024: (2024, 2, 10),
    2025: (2025, 1, 29),
}


class TestKnownTetDates(unittest.TestCase):
    """Tet (mung 1 thang 1 am lich) phai khop ngay Duong lich da cong bo."""

    def test_gregorian_to_lunar_matches_known_tet(self):
        for lunar_year, (gy, gm, gd) in KNOWN_TET_DATES.items():
            with self.subTest(lunar_year=lunar_year):
                result = gregorian_to_lunar(gy, gm, gd)
                self.assertEqual(result.month, 1)
                self.assertEqual(result.day, 1)
                self.assertFalse(result.is_leap_month)
                self.assertEqual(result.year, lunar_year)

    def test_lunar_to_gregorian_matches_known_tet(self):
        for lunar_year, (gy, gm, gd) in KNOWN_TET_DATES.items():
            with self.subTest(lunar_year=lunar_year):
                result = lunar_to_gregorian(
                    LunarDate(year=lunar_year, month=1, day=1, is_leap_month=False)
                )
                self.assertEqual(result, datetime.date(gy, gm, gd))


class TestCenturyLeapYearRegression(unittest.TestCase):
    """
    Bug da phat hien va sua: ban port truoc day cua thuat toan Ho Ngoc Duc
    tinh sai nam nhuan the ky (chia het 100, khong chia het 400), lam lech
    1 ngay tu 1/3 tro di cua cac nam do. Khoa lai bang test regression nay.
    """

    NON_LEAP_CENTURY_YEARS = (1700, 1800, 1900, 2100, 2200, 2300)
    LEAP_CENTURY_YEARS = (1600, 2000, 2400)

    def test_gregorian_sdn_matches_around_feb_29_non_leap_century(self):
        for year in self.NON_LEAP_CENTURY_YEARS:
            with self.subTest(year=year):
                # 28/2 -> 1/3 phai chi cach dung 1 ngay (khong co 29/2)
                d1 = gregorian_to_lunar(year, 2, 28)
                d2 = gregorian_to_lunar(year, 3, 1)
                sdn1 = gregorian_sdn(year, 2, 28)
                sdn2 = gregorian_sdn(year, 3, 1)
                self.assertEqual(sdn2 - sdn1, 1)
                self.assertIsInstance(d1, LunarDate)
                self.assertIsInstance(d2, LunarDate)

    def test_gregorian_sdn_matches_around_feb_29_leap_century(self):
        for year in self.LEAP_CENTURY_YEARS:
            with self.subTest(year=year):
                sdn_28 = gregorian_sdn(year, 2, 28)
                sdn_29 = gregorian_sdn(year, 2, 29)
                sdn_mar1 = gregorian_sdn(year, 3, 1)
                self.assertEqual(sdn_29 - sdn_28, 1)
                self.assertEqual(sdn_mar1 - sdn_29, 1)


class TestRoundTrip(unittest.TestCase):
    """Duong lich -> Am lich -> Duong lich phai tra ve dung ngay ban dau."""

    def test_round_trip_2000_to_2030(self):
        start = datetime.date(2000, 1, 1)
        end = datetime.date(2030, 12, 31)
        d = start
        checked = 0
        while d <= end:
            lunar = gregorian_to_lunar(d.year, d.month, d.day)
            if lunar.year != 0:
                back = lunar_to_gregorian(lunar)
                with self.subTest(date=d):
                    self.assertEqual(back, d)
                checked += 1
            d += datetime.timedelta(days=17)
        # dam bao vong lap thuc su co chay, khong phai gia mao pass
        self.assertGreater(checked, 400)


class TestInvalidInput(unittest.TestCase):
    """Input khong hop le phai duoc xu ly gon gang, khong crash."""

    def test_gregorian_to_lunar_invalid_returns_empty(self):
        for year, month, day in [
            (0, 1, 1),
            (2024, 13, 1),
            (2024, 2, 30),
            (-4712, 1, 1),  # gia tri mac dinh cua Date() chua khoi tao
        ]:
            with self.subTest(y=year, m=month, d=day):
                result = gregorian_to_lunar(year, month, day)
                self.assertEqual(result, EMPTY_LUNAR_DATE)
                # phai la LunarDate that su, khong phai tuple thuong
                self.assertIsInstance(result, LunarDate)
                self.assertTrue(hasattr(result, "year"))

    def test_lunar_to_gregorian_invalid_month_raises(self):
        with self.assertRaises(ValueError):
            lunar_to_gregorian(LunarDate(year=2024, month=13, day=1))

    def test_lunar_to_gregorian_invalid_day_raises(self):
        with self.assertRaises(ValueError):
            lunar_to_gregorian(LunarDate(year=2024, month=1, day=31))

    def test_vietnamese_lunar_valid(self):
        self.assertTrue(vietnamese_lunar_valid((1, 1, 2024)))
        self.assertFalse(vietnamese_lunar_valid((31, 1, 2024)))  # ngay > 30
        self.assertFalse(vietnamese_lunar_valid((1, 13, 2024)))  # thang > 12
        self.assertFalse(vietnamese_lunar_valid((1, 1, 0)))  # nam 0
        self.assertFalse(vietnamese_lunar_valid("not a tuple"))
        self.assertFalse(vietnamese_lunar_valid((1, 1)))  # thieu phan tu


class TestLeapMonth(unittest.TestCase):
    """
    Gioi han V1 da biet: Date.dateval khong co cho luu co nhuan, nhung
    ham cap thap vietnamese_sdn/lunar_to_gregorian van phai tinh dung khi
    duoc goi truc tiep voi leap=True.
    """

    def _find_a_leap_month_year(self):
        """Do mot vai nam gan day de tim nam co thang nhuan that su."""
        for year in range(2020, 2030):
            for month in range(1, 13):
                try:
                    lunar_to_gregorian(
                        LunarDate(year=year, month=month, day=1, is_leap_month=True)
                    )
                    return year, month
                except ValueError:
                    continue
        return None, None

    def test_leap_month_round_trip_if_found(self):
        year, month = self._find_a_leap_month_year()
        if year is None:
            self.skipTest("Khong tim thay thang nhuan trong khoang 2020-2030")
        greg = lunar_to_gregorian(
            LunarDate(year=year, month=month, day=1, is_leap_month=True)
        )
        # Chuyen nguoc lai qua gregorian_to_lunar phai nhan dung is_leap_month
        back = gregorian_to_lunar(greg.year, greg.month, greg.day)
        self.assertTrue(back.is_leap_month)
        self.assertEqual(back.month, month)
        self.assertEqual(back.year, year)

    def test_vietnamese_ymd_does_not_report_leap_flag(self):
        """
        Regression-guard cho gioi han V1: vietnamese_ymd() (dung boi
        Date qua gcalendar.py) tra ve tuple (year, month, day) 3 phan tu,
        KHONG co co nhuan. Neu test nay that bai vi tuple co 4 phan tu,
        nghia la ai do da mo rong dinh dang - phai cap nhat lai gcalendar.py
        va Date.dateval tuong ung, khong duoc de lech ngam.
        """
        sdn = vietnamese_sdn(2024, 1, 1, leap=False)
        result = vietnamese_ymd(sdn)
        self.assertEqual(len(result), 3)


class TestDateClassIntegration(unittest.TestCase):
    """Kiem tra qua dung API cong khai Date, nhu nguoi dung GUI se dung."""

    def test_date_set_and_convert_to_gregorian(self):
        d = Date()
        d.set_calendar(Date.CAL_VIETNAMESE_LUNAR)
        d.set_yr_mon_day(2024, 1, 1)
        greg = d.to_calendar("gregorian")
        self.assertEqual(
            (greg.get_year(), greg.get_month(), greg.get_day()), (2024, 2, 10)
        )

    def test_date_round_trip_through_sdn(self):
        d = Date()
        d.set_calendar(Date.CAL_VIETNAMESE_LUNAR)
        d.set_yr_mon_day(2025, 1, 1)
        sdn = d.get_sort_value()

        # Chuyen sang Gregorian bang API cong khai, kiem tra sort value
        # (SDN) khong doi qua qua trinh chuyen doi lich.
        d_greg = d.to_calendar("gregorian")
        self.assertEqual(sdn, d_greg.get_sort_value())

        # Chuyen nguoc lai ve Vietnamese Lunar, phai ra dung ngay ban dau.
        d_back = d_greg.to_calendar("vietnamese lunar")
        self.assertEqual(
            (d_back.get_year(), d_back.get_month(), d_back.get_day()),
            (d.get_year(), d.get_month(), d.get_day()),
        )


if __name__ == "__main__":
    unittest.main()
