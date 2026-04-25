"""Tests for KPI card formatting utilities."""

import pytest
from src.visualization.components.kpi_cards import (
    format_billions,
    format_lakh_crores,
    format_percentage,
    format_indian_rupee,
)


class TestFormatBillions:
    def test_large_number(self):
        assert format_billions(15_234_000_000) == "15.2 Bn"

    def test_single_billion(self):
        assert format_billions(1_000_000_000) == "1.0 Bn"

    def test_millions(self):
        assert format_billions(500_000_000) == "500.0 Mn"

    def test_small_number(self):
        assert format_billions(12345) == "12,345"


class TestFormatLakhCrores:
    def test_lakh_crore_value(self):
        result = format_lakh_crores(20_00_000_00_00_000)
        assert "₹" in result
        assert "LCr" in result

    def test_crore_value(self):
        result = format_lakh_crores(5_00_00_000)
        assert "₹" in result
        assert "Cr" in result


class TestFormatPercentage:
    def test_positive_with_sign(self):
        assert format_percentage(0.4623) == "+46.2%"

    def test_negative_with_sign(self):
        assert format_percentage(-0.05) == "-5.0%"

    def test_without_sign(self):
        assert format_percentage(0.4623, with_sign=False) == "46.2%"


class TestFormatIndianRupee:
    def test_formatting(self):
        result = format_indian_rupee(1374.5)
        assert result == "₹1,374"

    def test_large_value(self):
        result = format_indian_rupee(25000)
        assert result == "₹25,000"
