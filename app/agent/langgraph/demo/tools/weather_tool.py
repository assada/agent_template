from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from app.agent.models import CustomUIMessage


class WeatherInput(BaseModel):
    city: str = Field(description="The city to get weather for")


class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = "Get weather information for a given city"
    args_schema: type[BaseModel] = WeatherInput

    async def _arun(self, city: str, **kwargs) -> str:
        writer = get_stream_writer()
        if writer is not None:
            writer(
                CustomUIMessage(
                    type="ui",
                    component="file_upload",
                    id="doc-upload",
                    params={
                        "label": "Upload weather data",
                        "accept": ["application/json"],
                        "placeholder": f"Upload a JSON file with weather data for the {city} city.",
                    },
                )
            )

        import random

        weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "partly cloudy"]
        temperature = random.randint(-5, 35)
        condition = random.choice(weather_conditions)

        return f"The weather in {city} is {condition} and {temperature}°C!"

    def _run(self, city: str, **kwargs) -> str:
        import random

        weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "partly cloudy"]
        temperature = random.randint(-5, 35)
        condition = random.choice(weather_conditions)

        return f"The weather in {city} is {condition} and {temperature}°C!"