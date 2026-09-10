import unittest
from datetime import date


from gramps.gen.lib.gcalendar import (
    gregorian_sdn,
#    vietnamese_sdn,
#    vietnamese_ymd,
)

from ..vietnamese_lunar import (
    LunarDate,
    _jd_from_date,
    gregorian_to_lunar,
    lunar_to_gregorian,
    vietnamese_sdn,
    vietnamese_ymd,
)

GRAMPS_SDN_OFFSET = 32045

class VietnameseLunarTest(unittest.TestCase):
    """Tests for the Vietnamese lunar calendar."""

    def test_gregorian_to_lunar_new_year_2004(self):
        """22 January 2004 was lunar New Year's Day."""
        self.assertEqual(
            gregorian_to_lunar(2004, 1, 22),
            LunarDate(2004, 1, 1),
        )

    def test_gregorian_to_lunar_new_year_2024(self):
        """10 February 2024 was lunar New Year's Day."""
        self.assertEqual(
            gregorian_to_lunar(2024, 2, 10),
            LunarDate(2024, 1, 1),
        )

    def test_gregorian_to_lunar_new_year_2025(self):
        """29 January 2025 was lunar New Year's Day."""
        self.assertEqual(
            gregorian_to_lunar(2025, 1, 29),
            LunarDate(2025, 1, 1),
        )

    def test_gregorian_to_lunar_new_year_2026(self):
        """17 February 2026 was lunar New Year's Day."""
        self.assertEqual(
            gregorian_to_lunar(2026, 2, 17),
            LunarDate(2026, 1, 1),
        )

    def test_gregorian_to_lunar_before_lunar_month_11_1999(self):
        """7 December 1999 was lunar 30/10/1999."""
        self.assertEqual(
            gregorian_to_lunar(1999, 12, 7),
            LunarDate(1999, 10, 30),
        )

    def test_gregorian_to_lunar_lunar_month_11_1999(self):
        """8 December 1999 was lunar 1/11/1999."""
        self.assertEqual(
            gregorian_to_lunar(1999, 12, 8),
            LunarDate(1999, 11, 1),
        )

    def test_leap_month_2004(self):
        """2004 had a leap lunar second month."""
        self.assertEqual(
            gregorian_to_lunar(2004, 4, 18),
            LunarDate(
                2004,
                2,
                29,
                True,
            ),
        )

    def test_first_day_after_leap_month_2004(self):
        """19 April 2004 was the first day of lunar month 3."""
        self.assertEqual(
            gregorian_to_lunar(2004, 4, 19),
            LunarDate(2004, 3, 1),
        )

    def test_lunar_to_gregorian_new_year_2004(self):
        self.assertEqual(
            lunar_to_gregorian(
                LunarDate(2004, 1, 1)
            ),
            date(2004, 1, 22),
        )

    def test_lunar_to_gregorian_new_year_2024(self):
        self.assertEqual(
            lunar_to_gregorian(
                LunarDate(2024, 1, 1)
            ),
            date(2024, 2, 10),
        )

    def test_lunar_to_gregorian_new_year_2025(self):
        self.assertEqual(
            lunar_to_gregorian(
                LunarDate(2025, 1, 1)
            ),
            date(2025, 1, 29),
        )

    def test_lunar_to_gregorian_new_year_2026(self):
        self.assertEqual(
            lunar_to_gregorian(
                LunarDate(2026, 1, 1)
            ),
            date(2026, 2, 17),
        )

    def test_leap_month_2004_round_trip(self):
        lunar_date = LunarDate(
            2004,
            2,
            1,
            True,
        )

        solar_date = lunar_to_gregorian(lunar_date)

        self.assertEqual(
            gregorian_to_lunar(
                solar_date.year,
                solar_date.month,
                solar_date.day,
            ),
            lunar_date,
        )

    def test_round_trip_gregorian_to_lunar(self):
        test_dates = [
            date(1999, 12, 7),
            date(1999, 12, 8),
            date(2000, 1, 7),
            date(2004, 1, 22),
            date(2004, 4, 18),
            date(2004, 4, 19),
            date(2024, 2, 10),
            date(2025, 1, 29),
            date(2026, 2, 17),
        ]

        for solar_date in test_dates:
            with self.subTest(solar_date=solar_date):
                lunar_date = gregorian_to_lunar(
                    solar_date.year,
                    solar_date.month,
                    solar_date.day,
                )

                self.assertEqual(
                    lunar_to_gregorian(lunar_date),
                    solar_date,
                )

    def test_invalid_gregorian_date(self):
            """Kiểm tra ngày Dương lịch không hợp lệ trả về tuple an toàn (0, 0, 0, False)."""
            self.assertEqual(
                gregorian_to_lunar(2025, 2, 29),
                (0, 0, 0, False)
            )
            self.assertEqual(
                gregorian_to_lunar(-1, 1, 1),
                (0, 0, 0, False)
            )

    
    def test_invalid_lunar_month(self):
        """Kiểm tra tháng âm lịch > 12 sẽ bắn ra ValueError."""
        with self.assertRaises(ValueError):
            lunar_to_gregorian(
                LunarDate(2025, 13, 1)
            )

    def test_invalid_lunar_day(self):
        """Kiểm tra ngày âm lịch > 30 sẽ bắn ra ValueError."""
        with self.assertRaises(ValueError):
            lunar_to_gregorian(
                LunarDate(2025, 1, 31)
            )

    def test_invalid_leap_month(self):
        """Kiểm tra chỉ định tháng nhuận không tồn tại trong năm sẽ bắn ra ValueError."""
        with self.assertRaises(ValueError):
            lunar_to_gregorian(
                LunarDate(
                    2025,
                    2,
                    1,
                    is_leap_month=True,
                )
            )
    def test_jdn_2000_01_01(self):
        """Gregorian 2000-01-01 has JDN 2451545."""
        self.assertEqual(
            _jd_from_date(1, 1, 2000),
            2451545,
        )


    def test_vietnamese_sdn_known_gregorian_reference(self):
        """Gregorian 2000-01-01 must remain JDN 2451545."""
        self.assertEqual(
            _jd_from_date(1, 1, 2000),
            2451545,
        )

    def test_vietnamese_sdn(self):
        lunar = LunarDate(
            year=2026,
            month=7,
            day=15,
        )

        gregorian = lunar_to_gregorian(lunar)

        expected = _jd_from_date(
            gregorian.day,
            gregorian.month,
            gregorian.year,
        )

        self.assertEqual(
            vietnamese_sdn(2026, 7, 15),
            expected,
        )

    def test_vietnamese_ymd(self):
        lunar = LunarDate(
            year=2026,
            month=7,
            day=15,
        )

        gregorian = lunar_to_gregorian(lunar)

        sdn = _jd_from_date(
            gregorian.day,
            gregorian.month,
            gregorian.year,
        )

        self.assertEqual(
            vietnamese_ymd(sdn),
            (2026, 7, 15),
        )

    
    def test_gregorian_sdn_reference(self):
        """Gramps SDN for 2000-01-01 is 2451545."""
        self.assertEqual(
            gregorian_sdn(2000, 1, 1),
            2451545,
        )


    def test_vietnamese_sdn_matches_gramps_gregorian_sdn(self):
        """Vietnamese SDN must use the same SDN scale as Gramps."""
        lunar_date = LunarDate(
            year=2026,
            month=7,
            day=15,
        )

        gregorian_date = lunar_to_gregorian(lunar_date)

        expected_sdn = gregorian_sdn(
            gregorian_date.year,
            gregorian_date.month,
            gregorian_date.day,
        )

        self.assertEqual(
            vietnamese_sdn(
                lunar_date.year,
                lunar_date.month,
                lunar_date.day,
            ),
            expected_sdn,
        )


import unittest
from datetime import date

from ..vietnamese_lunar import (
    LunarDate,
    _jd_from_date,
    gregorian_to_lunar,
    lunar_to_gregorian,
    vietnamese_sdn,
    vietnamese_ymd,
    vietnamese_lunar_valid,
)

class VietnameseLunarExtendedTest(unittest.TestCase):
    """Bổ sung các test case kiểm tra tính chính xác của module vietnamese_lunar."""

    def test_vietnamese_vs_chinese_lunar_differences(self):
        """Kiểm tra các năm Âm lịch Việt Nam (UTC+7) khác với Âm lịch Trung Quốc (UTC+8)."""
        # Tết Mậu Dần 1998: Việt Nam là 28/01/1998, TQ là 27/01/1998
        self.assertEqual(
            gregorian_to_lunar(1998, 1, 28),
            LunarDate(1998, 1, 1),
        )
        # Tết Kỷ Mão 1999: Việt Nam là 16/02/1999, TQ là 17/02/1999
        self.assertEqual(
            gregorian_to_lunar(1999, 2, 16),
            LunarDate(1999, 1, 1),
        )
        # Tết Đinh Hợi 2007: Việt Nam là 17/02/2007
        self.assertEqual(
            gregorian_to_lunar(2007, 2, 17),
            LunarDate(2007, 1, 1),
        )

    def test_leap_months_various_years(self):
        """Kiểm tra tính chính xác của tháng nhuận ở các năm khác nhau."""
        # Năm 2020 nhuận tháng 4 (23/05/2020 là 01/04 nhuận)
        self.assertEqual(
            gregorian_to_lunar(2020, 5, 23),
            LunarDate(2020, 4, 1, is_leap_month=True),
        )
        # Năm 2023 nhuận tháng 2 (22/03/2023 là 01/02 nhuận)
        self.assertEqual(
            gregorian_to_lunar(2023, 3, 22),
            LunarDate(2023, 2, 1, is_leap_month=True),
        )

    def test_invalid_gregorian_returns_tuple(self):
        """Kiểm tra xử lý đầu vào ngày Dương lịch không hợp lệ."""
        # Kiểm tra trả về (0, 0, 0, False) theo đúng logic trong vietnamese_lunar.py
        self.assertEqual(
            gregorian_to_lunar(2025, 2, 29),
            (0, 0, 0, False)
        )
        self.assertEqual(
            gregorian_to_lunar(-1, 1, 1),
            (0, 0, 0, False)
        )

    def test_vietnamese_lunar_valid(self):
        """Kiểm tra hàm vietnamese_lunar_valid."""
        self.assertTrue(vietnamese_lunar_valid((15, 7, 2026)))
        self.assertTrue(vietnamese_lunar_valid((30, 12, 2025)))
        
        # Ngày/tháng ngoài phạm vi
        self.assertFalse(vietnamese_lunar_valid((0, 7, 2026)))
        self.assertFalse(vietnamese_lunar_valid((31, 7, 2026)))
        self.assertFalse(vietnamese_lunar_valid((15, 13, 2026)))
        self.assertFalse(vietnamese_lunar_valid((15, 7, 0)))
        self.assertFalse(vietnamese_lunar_valid("invalid_tuple"))


if __name__ == "__main__":
    unittest.main()