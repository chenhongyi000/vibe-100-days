#!/usr/bin/env python3
"""wttr-cli — 终端天气极简仪

A minimal terminal weather dashboard powered by wttr.in.
Zero config, zero API key, one command to check the weather.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

import requests
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ── WWO Weather Code Mapping ──────────────────────────────────────────────
# wttr.in uses World Weather Online codes (not WMO).
# Map each code to (emoji, Chinese description).

WEATHER_CODES: dict[str, tuple[str, str]] = {
    "113": ("☀️", "晴"),
    "116": ("⛅", "多云"),
    "119": ("☁️", "阴"),
    "122": ("☁️", "阴"),
    "143": ("🌫️", "雾"),
    "149": ("🌫️", "霾"),       # Hazy
    "176": ("🌦️", "阵雨"),
    "179": ("🌨️", "雨夹雪"),
    "182": ("🌧️", "雨夹雪"),
    "185": ("🌧️", "冻雨"),
    "200": ("⛈️", "雷阵雨"),
    "227": ("🌨️", "暴雪"),
    "230": ("🌨️", "暴雪"),
    "248": ("🌫️", "雾"),
    "260": ("🌫️", "雾"),
    "263": ("🌧️", "小雨"),
    "266": ("🌧️", "小雨"),
    "281": ("🌧️", "冻雨"),
    "284": ("🌧️", "冻雨"),
    "293": ("🌧️", "小雨"),
    "296": ("🌧️", "小雨"),
    "299": ("🌧️", "中雨"),
    "302": ("🌧️", "中雨"),
    "305": ("🌧️", "大雨"),
    "308": ("🌧️", "大雨"),
    "311": ("🌧️", "冻雨"),
    "314": ("🌧️", "冻雨"),
    "317": ("🌧️", "雨夹雪"),
    "320": ("🌧️", "雨夹雪"),
    "323": ("🌨️", "小雪"),
    "326": ("🌨️", "小雪"),
    "329": ("🌨️", "中雪"),
    "332": ("🌨️", "中雪"),
    "335": ("🌨️", "大雪"),
    "338": ("🌨️", "大雪"),
    "350": ("🌨️", "冰雹"),
    "353": ("🌧️", "阵雨"),
    "356": ("🌧️", "大雨"),
    "359": ("🌧️", "暴雨"),
    "362": ("🌧️", "雨夹雪"),
    "365": ("🌧️", "雨夹雪"),
    "368": ("🌨️", "小雪"),
    "371": ("🌨️", "大雪"),
    "374": ("🌨️", "冰雹"),
    "377": ("🌨️", "冰雹"),
    "386": ("⛈️", "雷阵雨"),
    "389": ("⛈️", "雷暴"),
    "392": ("⛈️", "雷阵雪"),
    "395": ("🌨️", "大雪"),
}

# ── Wind Direction Mapping ────────────────────────────────────────────────

WIND_DIRECTIONS: dict[str, str] = {
    "N": "北", "NNE": "北东北", "NE": "东北", "ENE": "东东北",
    "E": "东", "ESE": "东东南", "SE": "东南", "SSE": "南东南",
    "S": "南", "SSW": "南西南", "SW": "西南", "WSW": "西西南",
    "W": "西", "WNW": "西西北", "NW": "西北", "NNW": "北西北",
}


# ── Utility Functions ─────────────────────────────────────────────────────

def _get_weather_desc(code: str, api_desc: str = "") -> tuple[str, str]:
    """Get (emoji, description) for a weather code.

    Falls back to the API's weather description if the code is not in our
    mapping table, or returns (❓, 未知) if both are unavailable.
    """
    if code in WEATHER_CODES:
        return WEATHER_CODES[code]
    if api_desc:
        return ("🌡️", api_desc)
    return ("❓", "未知")


def _safe_str(value, default: str = "N/A") -> str:
    """Convert value to string, returning default if None or empty."""
    if value is None or value == "":
        return default
    return str(value)


def _temp_color(temp_c: int) -> str:
    """Return a Rich color/style string based on temperature in Celsius."""
    if temp_c >= 35:
        return "bold red"
    elif temp_c >= 30:
        return "red"
    elif temp_c >= 20:
        return "yellow"
    elif temp_c >= 10:
        return "green"
    elif temp_c >= 0:
        return "cyan"
    else:
        return "bold blue"


def _wind_direction_cn(abbr: str) -> str:
    """Convert wind direction abbreviation to Chinese, fallback to original."""
    return WIND_DIRECTIONS.get(abbr.upper(), abbr)


# ── API Fetching ──────────────────────────────────────────────────────────

def fetch_weather(city: str | None = None, timeout: int = 10) -> dict:
    """Fetch weather data from wttr.in JSON API.

    Args:
        city: City name in Chinese or English. None for IP auto-detection.
        timeout: HTTP request timeout in seconds.

    Returns:
        Parsed JSON response as a dict.

    Raises:
        SystemExit: On network errors, invalid response, or city not found.
    """
    base_url = "https://wttr.in/"
    if city:
        location = requests.utils.quote(city.strip())
    else:
        location = ""

    url = f"{base_url}{location}?format=j1"
    headers = {"User-Agent": "wttr-cli/0.1.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise SystemExit("❌ 网络超时，请检查网络连接后重试。")
    except requests.exceptions.ConnectionError:
        raise SystemExit("❌ 无法连接到 wttr.in，请检查网络连接。")
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 404:
            raise SystemExit(f"❌ 未找到城市「{city}」，请检查拼写后重试。")
        raise SystemExit(f"❌ wttr.in API 返回 HTTP {resp.status_code} 错误。")

    try:
        data = resp.json()
    except ValueError:
        raise SystemExit("❌ wttr.in API 返回数据异常，请稍后重试。")

    if not data.get("current_condition"):
        raise SystemExit("❌ 该地区暂无天气数据。")

    return data


# ── Simple Text Renderer ──────────────────────────────────────────────────

def render_simple(data: dict) -> str:
    """Render weather data as a single line of plain text.

    Format: 城市名: ☀️ 晴 25°C (体感 24°C) | 湿度 45% | 西南风 15 km/h
    """
    current = data["current_condition"][0]
    area = data.get("nearest_area", [{}])[0]
    city_name = (
        area.get("areaName", [{}])[0].get("value", "未知")
        or "未知"
    )

    code = _safe_str(current.get("weatherCode"), "")
    api_desc = _safe_str(
        current.get("weatherDesc", [{}])[0].get("value", ""), ""
    )
    emoji, desc = _get_weather_desc(code, api_desc)
    temp_c = _safe_str(current.get("temp_C"), "--")
    feels_like = _safe_str(current.get("FeelsLikeC"), "--")
    humidity = _safe_str(current.get("humidity"), "--")
    wind_dir = _safe_str(current.get("winddir16Point"), "")
    wind_dir_cn = _wind_direction_cn(wind_dir)
    wind_speed = _safe_str(current.get("windspeedKmph"), "--")

    parts = [
        f"{city_name}: {emoji} {desc} {temp_c}°C (体感 {feels_like}°C)",
        f"湿度 {humidity}%",
        f"{wind_dir_cn}风 {wind_speed} km/h",
    ]
    return " | ".join(parts)


# ── Rich Terminal Renderer ────────────────────────────────────────────────

def render_current_panel(data: dict, console: Console) -> Panel:
    """Build a Rich Panel for current weather conditions."""
    current = data["current_condition"][0]
    area = data.get("nearest_area", [{}])[0]

    # City name
    city_cn = (
        area.get("areaName", [{}])[0].get("value", "未知")
        or "未知"
    )
    country = (
        area.get("country", [{}])[0].get("value", "")
        or ""
    )
    city_display = f"{city_cn}" if not country else f"{city_cn} ({country})"

    # Weather condition
    code = _safe_str(current.get("weatherCode"), "")
    emoji, desc = _get_weather_desc(code)
    temp_c = _safe_str(current.get("temp_C"), "--")
    feels_like = _safe_str(current.get("FeelsLikeC"), "--")

    # Build large temperature display
    temp_text = Text(f"{emoji}  {desc}  {temp_c}°C", style="bold")
    feels_text = Text(f"体感温度: {feels_like}°C", style="dim")

    # Metrics grid
    metrics = Table(box=None, show_header=False, padding=(0, 2))
    metrics.add_column(style="dim")
    metrics.add_column()

    humidity = _safe_str(current.get("humidity"), "--")
    wind_dir = _safe_str(current.get("winddir16Point"), "")
    wind_dir_cn = _wind_direction_cn(wind_dir)
    wind_speed = _safe_str(current.get("windspeedKmph"), "--")
    visibility = _safe_str(current.get("visibility"), "--")
    pressure = _safe_str(current.get("pressure"), "--")
    uv_index = _safe_str(current.get("uvIndex"), "--")

    metrics.add_row("💧 湿度", f"{humidity}%")
    metrics.add_row("🌬️ 风向", f"{wind_dir_cn} {wind_speed} km/h")
    metrics.add_row("👁️ 能见度", f"{visibility} km")
    metrics.add_row("📊 气压", f"{pressure} hPa")
    metrics.add_row("☀️ UV 指数", uv_index)

    # Observation time
    obs_time = _safe_str(current.get("observation_time"), "")
    obs_text = Text(f"观测时间: {obs_time}", style="dim italic")

    # Assemble
    content = Table(box=None, show_header=False, padding=(0, 0))
    content.add_column(justify="center")
    content.add_row(temp_text)
    content.add_row(feels_text)
    content.add_row("")
    content.add_row(metrics)
    content.add_row("")
    content.add_row(obs_text)

    return Panel(
        content,
        title=f"[bold]{city_display}[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )


def render_forecast_table(data: dict, days: int) -> Table:
    """Build a Rich Table for multi-day forecast."""
    table = Table(
        title="天气预报",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("日期", style="dim")
    table.add_column("天气")
    table.add_column("高温/低温")
    table.add_column("湿度")
    table.add_column("风力")

    weather_list = data.get("weather", [])
    for entry in weather_list[:days]:
        date_str = _safe_str(entry.get("date"), "----")
        # Parse date for weekday display
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_display = f"{dt.month:02d}-{dt.day:02d} 周{['一','二','三','四','五','六','日'][dt.weekday()]}"
        except (ValueError, IndexError):
            date_display = date_str

        hourly_data = entry.get("hourly", [{}])[4] if len(entry.get("hourly", [])) > 4 else {}
        code = _safe_str(hourly_data.get("weatherCode"), "")
        api_desc = _safe_str(
            hourly_data.get("weatherDesc", [{}])[0].get("value", ""), ""
        )
        emoji, desc = _get_weather_desc(code, api_desc)
        high = _safe_str(entry.get("maxtempC"), "--")
        low = _safe_str(entry.get("mintempC"), "--")

        # Color-code the high temperature
        try:
            high_int = int(high)
            high_style = _temp_color(high_int)
        except (ValueError, TypeError):
            high_style = ""

        temp_display = (
            f"[{high_style}]{high}°C[/{high_style}]/{low}°C"
            if high_style
            else f"{high}°C/{low}°C"
        )

        # Average humidity from hourly data
        hourly = entry.get("hourly", [])
        if hourly:
            humidities = [
                int(h.get("humidity", 0))
                for h in hourly
                if h.get("humidity")
            ]
            avg_humidity = sum(humidities) // len(humidities) if humidities else "--"
        else:
            avg_humidity = "--"

        # Wind from midday (index 4)
        mid_hourly = hourly[4] if len(hourly) > 4 else {}
        wind_dir = _safe_str(mid_hourly.get("winddir16Point"), "")
        wind_dir_cn = _wind_direction_cn(wind_dir)
        wind_speed = _safe_str(mid_hourly.get("windspeedKmph"), "--")

        weather_display = f"{emoji} {desc}"
        wind_display = f"{wind_dir_cn} {wind_speed}"

        table.add_row(date_display, weather_display, temp_display, f"{avg_humidity}%", wind_display)

    return table


def render_rich(data: dict, days: int = 3) -> None:
    """Render weather data with Rich formatting."""
    console = Console()

    # Current weather panel
    panel = render_current_panel(data, console)
    console.print(panel)

    # Forecast table
    if days > 0:
        console.print()
        forecast = render_forecast_table(data, days)
        console.print(forecast)


# ── CLI Entry Point ───────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point for wttr-cli."""
    # Ensure UTF-8 encoding on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="wttr",
        description="终端天气极简仪 — 一行命令，看一眼天气，然后继续写代码。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  wttr              自动检测当前位置天气
  wttr 北京         查询北京天气
  wttr "New York"   查询纽约天气
  wttr 上海 -d 3    查询上海 3 天预报
  wttr --simple     极简模式，纯文本输出
        """,
    )
    parser.add_argument(
        "city",
        nargs="?",
        default=None,
        help="城市名（中/英文），省略则自动检测位置",
    )
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=3,
        choices=range(1, 4),
        help="预报天数（1-3，默认 3）",
        metavar="N",
    )
    parser.add_argument(
        "-s", "--simple",
        action="store_true",
        help="极简模式：输出纯文本，适合脚本集成",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="wttr-cli 0.1.0",
    )

    args = parser.parse_args()

    data = fetch_weather(args.city)

    if args.simple:
        print(render_simple(data))
    else:
        render_rich(data, days=args.days)


if __name__ == "__main__":
    main()