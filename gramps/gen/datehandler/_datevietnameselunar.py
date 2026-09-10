#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

"""
Vietnamese Lunar Calendar Handler for Gramps.
"""

# -------------------------------------------------------------------------
#
# Gramps modules
#
# -------------------------------------------------------------------------
# from ._datehandler import DateHandler

# -------------------------------------------------------------------------
#
# Helper Functions: Thuật toán chuyển đổi Lịch Âm - Dương (Hồ Ngọc Đức)
#
# -------------------------------------------------------------------------
def vietnamese_lunar_to_jdn(day, month, year, leap=False):
    """
    Chuyển đổi từ ngày Âm lịch Việt Nam sang chỉ số Julian Day Number (JDN).
    """
    if year == 0 or month == 0 or day == 0:
        return 0
    # TODO: Thay bằng thuật toán Âm lịch Việt Nam đầy đủ của TS. Hồ Ngọc Đức
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn


def jdn_to_vietnamese_lunar(jdn):
    """
    Chuyển đổi từ chỉ số Julian Day Number (JDN) sang ngày Âm lịch Việt Nam.
    Trả về tuple: (day, month, year, is_leap)
    """
    if jdn == 0:
        return (0, 0, 0, False)
    # TODO: Thay bằng thuật toán Âm lịch Việt Nam đầy đủ
    f = jdn + 1401 + (((4 * jdn + 274274) // 146097) * 3) // 4 - 38
    e = 4 * f + 3
    g = (e % 1461) // 4
    h = 5 * g + 2
    day = (h % 153) // 5 + 1
    month = (h // 153 + 2) % 12 + 1
    year = e // 1461 - 4716 + (14 - month) // 12
    is_leap = False
    
    return (day, month, year, is_leap)


# -------------------------------------------------------------------------
#
# Vietnamese Lunar Date Handler Class
#
# -------------------------------------------------------------------------

class DateVietnameseLunar:
    """
    Lớp Transformer xử lý chuyển đổi giữa JDN và Lịch Âm Việt Nam.
    """
    @staticmethod
    def to_calendar(jdn):
        """
        Nhận vào JDN (số nguyên) -> Trả về tuple: (day, month, year, leap)
        """
        # Gọi hàm tính toán Lịch Âm của bạn
        day, month, year, leap = jdn_to_vietnamese_lunar(jdn)
        return (day, month, year, leap)

    @staticmethod
    def from_calendar(day, month, year, leap=False):
        """
        Nhận vào (day, month, year, leap) -> Trả về JDN (số nguyên)
        """
        # Gọi hàm chuyển Lịch Âm sang JDN của bạn
        jdn = vietnamese_lunar_to_jdn(day, month, year, leap)
        return jdn