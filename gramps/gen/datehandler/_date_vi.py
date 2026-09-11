# -*- coding: utf-8 -*-
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
Vietnamese-specific classes for parsing and displaying dates.
"""

# -------------------------------------------------------------------------
#
# Python modules
#
# -------------------------------------------------------------------------
import re

# -------------------------------------------------------------------------
#
# Gramps modules
#
# -------------------------------------------------------------------------
from ..lib.date import Date
from ._dateparser import DateParser
from ._datedisplay import DateDisplay
from ._datehandler import register_datehandler


# -------------------------------------------------------------------------
#
# Vietnamese parser class
#
# -------------------------------------------------------------------------
class DateParserVi(DateParser):
    """
    Convert a text string into a Date object, expecting a date
    notation in the Vietnamese language.
    """

    # Bổ sung các từ hạn định thời gian bằng tiếng Việt
    modifier_to_int = {
        "trước": Date.MOD_BEFORE,
        "truoc": Date.MOD_BEFORE,
        "sau": Date.MOD_AFTER,
        "khoảng": Date.MOD_ABOUT,
        "khoang": Date.MOD_ABOUT,
        "khoảng chừng": Date.MOD_ABOUT,
        "ca": Date.MOD_ABOUT,
        "c:a": Date.MOD_ABOUT,
        "từ": Date.MOD_FROM,
        "tu": Date.MOD_FROM,
        "đến": Date.MOD_TO,
        "den": Date.MOD_TO,
    }

    bce = ["TCN", "tcn", "Tr.CN", "tr.cn"]

    # Ánh xạ từ khóa tên hệ lịch khi gõ vào ô Date
    calendar_to_int = {
        "dương lịch": Date.CAL_GREGORIAN,
        "duong lich": Date.CAL_GREGORIAN,
        "gregorian": Date.CAL_GREGORIAN,
        "g": Date.CAL_GREGORIAN,
        "julian": Date.CAL_JULIAN,
        "j": Date.CAL_JULIAN,
        "do thái": Date.CAL_HEBREW,
        "do thai": Date.CAL_HEBREW,
        "h": Date.CAL_HEBREW,
        "hồi giáo": Date.CAL_ISLAMIC,
        "hoi giao": Date.CAL_ISLAMIC,
        "i": Date.CAL_ISLAMIC,
        "pháp": Date.CAL_FRENCH,
        "f": Date.CAL_FRENCH,
        "ba tư": Date.CAL_PERSIAN,
        "p": Date.CAL_PERSIAN,
        "thụy điển": Date.CAL_SWEDISH,
        "s": Date.CAL_SWEDISH,
        # Từ khóa Âm lịch Việt Nam
        "âm lịch": Date.CAL_VIETNAMESE_LUNAR,
        "am lich": Date.CAL_VIETNAMESE_LUNAR,
        "âm": Date.CAL_VIETNAMESE_LUNAR,
        "am": Date.CAL_VIETNAMESE_LUNAR,
        "al": Date.CAL_VIETNAMESE_LUNAR,
        "a.l": Date.CAL_VIETNAMESE_LUNAR,
    }

    quality_to_int = {
        "ước tính": Date.QUAL_ESTIMATED,
        "uoc tinh": Date.QUAL_ESTIMATED,
        "đánh giá": Date.QUAL_ESTIMATED,
        "tính toán": Date.QUAL_CALCULATED,
        "tinh toan": Date.QUAL_CALCULATED,
    }

    def init_strings(self):
        """Define, in Vietnamese, span and range regular expressions"""
        DateParser.init_strings(self)
        self._numeric = re.compile(r"((\d+)/)?\s*((\d+)/)?\s*(\d+)[/ ]?$")
        self._text2 = re.compile(
            r"((\d+)(/\d+)?)?\s+?%s\s*(\d+)?\s*$" % self._mon_str, re.IGNORECASE
        )
        self._span = re.compile(
            r"(từ|tu)?\s*(?P<start>.+)\s*(đến|den|--|–)\s*(?P<stop>.+)", re.IGNORECASE
        )
        self._range = re.compile(
            r"(giữa|mellan|mặt từ)\s+(?P<start>.+)\s+và\s+(?P<stop>.+)", re.IGNORECASE
        )

    def _parse_vietnamese_lunar(self, date_val):
            """Phân tích chuỗi ngày nhập cho Lịch Âm Việt Nam."""
            # Gọi parser mặc định hoặc parser phân tích ngày Âm lịch
            return self._parse_gregorian(date_val)

# -------------------------------------------------------------------------
#
# Vietnamese display class
#
# -------------------------------------------------------------------------
class DateDisplayVi(DateDisplay):
    """
    Vietnamese language date display class.
    """

    _bce_str = "%s TCN"

    formats = (
        "DD/MM/YYYY (Chuẩn VN)",
        "YYYY-MM-DD (ISO)",
        "Ngày DD tháng MM năm YYYY",
    )

    def _display_vietnamese_lunar(self, date_val, inflect="", **kwargs):
            """
            PTL2026: Hiển thị ngày Âm lịch Việt Nam kèm cờ Nhuận nếu có.
            """
            is_leap = bool(date_val[3]) if len(date_val) > 3 else False
            leap_str = " " + self._("Nhuận") if is_leap else ""

            # Gọi cách định dạng tiếng Việt đã định nghĩa ở trên
            base_str = self._display_calendar(date_val, self.long_months, self.short_months, inflect=inflect, **kwargs)
            return f"{base_str}{leap_str}"

    def _display_calendar(self, date_val, long_months, short_months=None, inflect=""):
        if short_months is None:
            short_months = long_months

        if self.format == 0:
            # Ngày/Tháng/Năm
            value = self.dd_dformat01_vi(date_val)
        elif self.format == 1:
            # ISO
            return self.display_iso(date_val)
        else:
            # Ngày ... tháng ... năm ...
            value = self.dd_dformat02_vi(date_val, long_months)

        if date_val[2] < 0:
            return self._bce_str % value
        else:
            return value

    def dd_dformat01_vi(self, date_val):
        # DD/MM/YYYY
        year = self._slash_year(date_val[2], date_val[3])
        if date_val[0] == 0:
            if date_val[1] == 0:
                return year
            else:
                return "%02d/%s" % (date_val[1], year)
        elif date_val[1] == 0:
            return self.display_iso(date_val)
        else:
            return "%02d/%02d/%s" % (date_val[0], date_val[1], year)

    def dd_dformat02_vi(self, date_val, long_months):
        # Ngày DD tháng MM năm YYYY
        year = self._slash_year(date_val[2], date_val[3])
        if date_val[0] == 0:
            if date_val[1] == 0:
                return year
            else:
                return "%s %s" % (long_months[date_val[1]], year)
        elif date_val[1] == 0:
            return self.display_iso(date_val)
        else:
            return "%d %s %s" % (date_val[0], long_months[date_val[1]], year)

    display = DateDisplay.display_formatted


# -------------------------------------------------------------------------
#
# Register classes
#
# -------------------------------------------------------------------------
register_datehandler(
    ("vi_VN", "vi_VN.UTF-8", "vi", "Vietnamese", ("%d/%m/%Y", "%Y-%m-%d")),
    DateParserVi,
    DateDisplayVi,
)