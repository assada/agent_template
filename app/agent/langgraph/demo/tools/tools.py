from collections.abc import Callable
from typing import Any

from .weather_tool import WeatherTool

weather_tool = WeatherTool()
TOOLS: list[Callable[..., Any]] = [weather_tool]
