"""Unit tests for wttr_cli core logic."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wttr_cli import (
    _get_weather_desc,
    _safe_str,
    _temp_color,
    _wind_direction_cn,
    WEATHER_CODES,
    WIND_DIRECTIONS,
    render_simple,
)


class TestWeatherCodes:
    """Tests for weather code mapping."""

    def test_known_code_returns_emoji_and_desc(self):
        emoji, desc = _get_weather_desc("113")
        assert emoji == "☀️"
        assert desc == "晴"

    def test_unknown_code_returns_default(self):
        emoji, desc = _get_weather_desc("999")
        assert emoji == "❓"
        assert desc == "未知"

    def test_unknown_code_with_api_fallback(self):
        """When code is unknown but API desc is provided, use it."""
        emoji, desc = _get_weather_desc("999", "Smoky haze")
        assert emoji != "❓"  # Should use the API description
        assert desc == "Smoky haze"

    def test_known_code_ignores_api_fallback(self):
        """Known code should use mapping, not API description."""
        emoji, desc = _get_weather_desc("113", "Sunny")
        assert emoji == "☀️"
        assert desc == "晴"

    def test_empty_code_returns_default(self):
        emoji, desc = _get_weather_desc("")
        assert emoji == "❓"
        assert desc == "未知"

    def test_all_defined_codes_are_valid(self):
        """Every code in WEATHER_CODES should map to non-empty strings."""
        for code, (emoji, desc) in WEATHER_CODES.items():
            assert emoji, f"Code {code} has empty emoji"
            assert desc, f"Code {code} has empty description"

    def test_weather_codes_count(self):
        """Should have at least 46 weather codes defined."""
        assert len(WEATHER_CODES) >= 46


class TestSafeStr:
    """Tests for _safe_str helper."""

    def test_returns_string_value(self):
        assert _safe_str("hello") == "hello"

    def test_returns_default_for_none(self):
        assert _safe_str(None) == "N/A"

    def test_returns_default_for_empty_string(self):
        assert _safe_str("") == "N/A"

    def test_returns_custom_default(self):
        assert _safe_str(None, default="--") == "--"


class TestTempColor:
    """Tests for temperature color mapping."""

    def test_extreme_hot(self):
        assert _temp_color(40) == "bold red"

    def test_hot(self):
        assert _temp_color(35) == "bold red"

    def test_warm(self):
        assert _temp_color(30) == "red"
        assert _temp_color(25) == "yellow"

    def test_mild(self):
        assert _temp_color(20) == "yellow"
        assert _temp_color(15) == "green"

    def test_cool(self):
        assert _temp_color(10) == "green"
        assert _temp_color(5) == "cyan"

    def test_cold(self):
        assert _temp_color(0) == "cyan"
        assert _temp_color(-5) == "bold blue"
        assert _temp_color(-20) == "bold blue"


class TestWindDirection:
    """Tests for wind direction mapping."""

    def test_known_direction(self):
        assert _wind_direction_cn("N") == "北"
        assert _wind_direction_cn("SW") == "西南"
        assert _wind_direction_cn("NE") == "东北"

    def test_unknown_direction_fallback(self):
        assert _wind_direction_cn("XX") == "XX"

    def test_case_insensitive(self):
        assert _wind_direction_cn("sw") == "西南"
        assert _wind_direction_cn("n") == "北"

    def test_all_directions_defined(self):
        """All 16 compass directions should be defined."""
        expected = {"N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"}
        assert set(WIND_DIRECTIONS.keys()) == expected


class TestRenderSimple:
    """Tests for the simple text renderer."""

    def test_renders_basic_weather(self):
        data = {
            "nearest_area": [{
                "areaName": [{"value": "Beijing"}],
                "country": [{"value": "China"}],
            }],
            "current_condition": [{
                "weatherCode": "113",
                "temp_C": "25",
                "FeelsLikeC": "24",
                "humidity": "45",
                "winddir16Point": "SW",
                "windspeedKmph": "15",
            }],
        }
        result = render_simple(data)
        assert "Beijing" in result
        assert "☀️" in result
        assert "晴" in result
        assert "25°C" in result
        assert "体感 24°C" in result
        assert "45%" in result
        assert "西南" in result

    def test_handles_missing_city_name(self):
        data = {
            "nearest_area": [{
                "areaName": [{"value": ""}],
                "country": [{"value": ""}],
            }],
            "current_condition": [{
                "weatherCode": "113",
                "temp_C": "20",
                "FeelsLikeC": "19",
                "humidity": "60",
                "winddir16Point": "N",
                "windspeedKmph": "10",
            }],
        }
        result = render_simple(data)
        assert "未知" in result

    def test_handles_missing_weather_fields(self):
        data = {
            "nearest_area": [{"areaName": [{"value": "Test"}]}],
            "current_condition": [{
                "weatherCode": "",
                "temp_C": "",
                "FeelsLikeC": "",
                "humidity": "",
                "winddir16Point": "",
                "windspeedKmph": "",
            }],
        }
        result = render_simple(data)
        assert "Test" in result
        assert "❓" in result
        assert "未知" in result
        assert "--" in result