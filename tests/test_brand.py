"""Tests for OpenPulse branding."""

from app.brand import API_TITLE, LEGACY_NAME, PRODUCT_NAME, TERMINAL_TITLE


class TestBrand:
    def test_product_name(self):
        assert PRODUCT_NAME == "OpenPulse"
        assert LEGACY_NAME == "IVSURF"

    def test_api_title(self):
        assert "OpenPulse" in API_TITLE

    def test_terminal_title(self):
        assert "OpenPulse" in TERMINAL_TITLE
