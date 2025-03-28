from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import pytz

class TimeZone(BaseModel):
    name: str
    country_code: Optional[str] = None
    offset: str
    current_time: str
    is_dst: bool

class TimeConversionRequest(BaseModel):
    timestamp: str
    source_timezone: Optional[str] = "UTC"
    target_timezone: str

    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Invalid timestamp format. Use ISO 8601 format (e.g., '2023-05-01T12:00:00Z')")

    @validator('source_timezone', 'target_timezone')
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v

class TimeConversionResponse(BaseModel):
    original_timestamp: str
    converted_timestamp: str
    source_timezone: str
    target_timezone: str
    offset: str
    is_dst: bool

class UserProfile(BaseModel):
    username: str
    email: str
    favorite_timezones: List[str] = []
    recent_conversions: List[TimeConversionResponse] = []
