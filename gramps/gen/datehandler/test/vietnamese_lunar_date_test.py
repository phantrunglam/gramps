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
Unit tests for Vietnamese Lunar calendar support in the datehandler layer
(_dateparser.py / _datedisplay.py).

Location: gramps/gen/datehandler/test/vietnamese_lunar_date_test.py

Khac voi vietnamese_lunar_test.py (thuan toan hoc, khong can GTK), file
nay import gramps.gen.datehandler, kich hoat toan bo co che locale/GTK
cua Gramps - phai chay trong dung venv da dung (co gi, PyGObject...).

Run with:
    python3 -m unittest gramps.gen.datehandler.test.vietnamese_lunar_date_test -v
"""

import unittest

from gramps.gen.lib.date import Date
from gramps.gen.datehandler._dateparser import DateParser
from gramps.gen.datehandler._datedisplay import DateDisplay


class TestCalendarRegistration(unittest.TestCase):
    """Kiem tra 3 bang tra cuu duoc dang ky dung, truoc khi test parse/display."""

    def setUp(self):
        self.dp = DateParser()

    def test_calendar_name_recognized(self):
        # day chinh la diem hay gay loi do cache __pycache__/_langs cu -
        # neu test nay that bai ngay ca sau khi sua code, kiem tra lai
        # DateParser._langs (bien cap class) va __pycache__.
        self.assertIn("vietnamese lunar", self.dp.calendar_to_int)
        self.assertEqual(
            self.dp.calendar_to_int["vietnamese lunar"], Date.CAL_VIETNAMESE_LUNAR
        )

    def test_month_table_has_12_entries(self):
        # vietnamese_lunar_to_int anh xa ten thang (co dau + khong dau + so)
        # ve dung 12 gia tri thang 1..12
        values = set(self.dp.vietnamese_lunar_to_int.values())
        self.assertEqual(values, set(range(1, 13)))

    def test_parser_dispatch_registered(self):
        self.assertIn(Date.CAL_VIETNAMESE_LUNAR, self.dp.parser)
        self.assertEqual(
            self.dp.parser[Date.CAL_VIETNAMESE_LUNAR], self.dp._parse_vietnamese_lunar
        )


class TestParseIsoWithCalendarSuffix(unittest.TestCase):
    """Dinh dang nguoi dung se go tay pho bien nhat: YYYY-MM-DD (Vietnamese Lunar)."""

    def setUp(self):
        self.dp = DateParser()

    def test_parses_calendar_and_strips_suffix(self):
        d = self.dp.parse("2024-01-01 (Vietnamese Lunar)")
        self.assertEqual(d.get_calendar(), Date.CAL_VIETNAMESE_LUNAR)
        self.assertNotEqual(d.get_modifier(), Date.MOD_TEXTONLY)
        self.assertEqual(d.get_year(), 2024)
        self.assertEqual(d.get_month(), 1)
        self.assertEqual(d.get_day(), 1)

    def test_round_trip_gregorian_conversion(self):
        d = self.dp.parse("2024-01-01 (Vietnamese Lunar)")
        greg = d.to_calendar("gregorian")
        self.assertEqual(
            (greg.get_year(), greg.get_month(), greg.get_day()), (2024, 2, 10)
        )

    def test_invalid_day_rejected_not_silently_accepted(self):
        """
        Day chinh la bug da phat hien: truoc khi sua _parse_subdate,
        ngay khong hop le (vd thang 13, ngay 31) van duoc chap nhan am
        tham vi thieu ham check. Test nay khoa lai hanh vi dung.
        """
        d = self.dp.parse("2024-13-40 (Vietnamese Lunar)")
        # Ngay khong hop le -> phai roi ve text-only, KHONG duoc parse
        # thanh cong voi thang=13 / ngay=40
        self.assertEqual(d.get_modifier(), Date.MOD_TEXTONLY)


class TestParseMonthName(unittest.TestCase):
    """Dinh dang co ten thang am lich, co dau lan khong dau."""

    def setUp(self):
        self.dp = DateParser()

    def test_parses_month_name_with_diacritics(self):
        d = self.dp.parse("1 Tháng Giêng 2024 (Vietnamese Lunar)")
        self.assertEqual(d.get_calendar(), Date.CAL_VIETNAMESE_LUNAR)
        self.assertNotEqual(d.get_modifier(), Date.MOD_TEXTONLY)
        self.assertEqual(d.get_month(), 1)

    def test_parses_month_name_without_diacritics(self):
        d = self.dp.parse("1 Thang Chap 2023 (Vietnamese Lunar)")
        self.assertEqual(d.get_calendar(), Date.CAL_VIETNAMESE_LUNAR)
        self.assertNotEqual(d.get_modifier(), Date.MOD_TEXTONLY)
        self.assertEqual(d.get_month(), 12)


class TestDisplay(unittest.TestCase):
    """Hien thi Date object nguoc lai thanh chuoi text."""

    def setUp(self):
        self.dd = DateDisplay()

    def test_display_does_not_crash(self):
        d = Date()
        d.set_calendar(Date.CAL_VIETNAMESE_LUNAR)
        d.set_yr_mon_day(2024, 1, 1)
        text = self.dd.display(d)
        self.assertTrue(text)  # khong rong, khong crash IndexError

    def test_display_contains_calendar_suffix(self):
        d = Date()
        d.set_calendar(Date.CAL_VIETNAMESE_LUNAR)
        d.set_yr_mon_day(2024, 1, 1)
        text = self.dd.display(d)
        # hau to co the la "(Vietnamese Lunar)" hoac ban dich - kiem tra
        # long leo bang cach xem no khac hoan toan voi ban hien thi Gregorian
        d_greg = Date()
        d_greg.set_yr_mon_day(2024, 1, 1)
        text_greg = self.dd.display(d_greg)
        self.assertNotEqual(text, text_greg)

    def test_display_all_12_months_no_crash(self):
        for month in range(1, 13):
            with self.subTest(month=month):
                d = Date()
                d.set_calendar(Date.CAL_VIETNAMESE_LUNAR)
                d.set_yr_mon_day(2024, month, 1)
                text = self.dd.display(d)
                self.assertTrue(text)


class TestParseDisplayRoundTrip(unittest.TestCase):
    """Parse roi display lai, dam bao khong mat thong tin lich."""

    def setUp(self):
        self.dp = DateParser()
        self.dd = DateDisplay()

    def test_parse_then_display_keeps_calendar(self):
        d = self.dp.parse("2024-01-01 (Vietnamese Lunar)")
        text = self.dd.display(d)
        d2 = self.dp.parse(text)
        self.assertEqual(d2.get_calendar(), Date.CAL_VIETNAMESE_LUNAR)
        self.assertEqual(d2.get_year(), d.get_year())
        self.assertEqual(d2.get_month(), d.get_month())
        self.assertEqual(d2.get_day(), d.get_day())


if __name__ == "__main__":
    unittest.main()
