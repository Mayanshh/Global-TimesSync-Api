from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, validator
from typing import Optional, List, Dict
import pytz
from datetime import datetime, timezone
from dateutil import parser
import logging
from .cache import TimeCache
from .auth import get_current_user, User
from flask import request, jsonify, g

# Initialize router
router = APIRouter()

# Initialize cache
time_cache = TimeCache()

# Initialize logger
logger = logging.getLogger(__name__)

# Request models
class ConversionRequest(BaseModel):
    utc_timestamp: str
    target_timezone: str

    @validator('utc_timestamp')
    def validate_timestamp(cls, v):
        try:
            parser.parse(v)
            return v
        except Exception:
            raise ValueError("Invalid timestamp format. Use ISO 8601 format (e.g., '2023-05-01T12:00:00Z')")

    @validator('target_timezone')
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v

# Response models
class ConversionResponse(BaseModel):
    utc_timestamp: str
    local_timestamp: str
    timezone: str
    offset: str
    is_dst: bool

class TimezoneInfo(BaseModel):
    name: str
    country_code: Optional[str] = None
    current_time: str
    offset: str
    is_dst: bool

# Timezone operations
@router.get("/timezones", response_model=List[str])
async def get_all_timezones():
    """
    Get a list of all available time zones.
    """
    return pytz.all_timezones

@router.get("/timezone/{timezone}", response_model=TimezoneInfo)
async def get_timezone_info(timezone: str):
    """
    Get detailed information about a specific timezone.
    """
    if timezone not in pytz.all_timezones:
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {timezone}")
    
    # Try to get from cache first
    cached_info = time_cache.get(f"timezone_info:{timezone}")
    if cached_info:
        return cached_info
    
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        # Get country code if available
        country_code = None
        for code, timezones in pytz.country_timezones.items():
            if timezone in timezones:
                country_code = code
                break
        
        # Calculate offset in hours and minutes
        offset_seconds = now.utcoffset().total_seconds()
        offset_hours = int(offset_seconds // 3600)
        offset_minutes = int((offset_seconds % 3600) // 60)
        offset_str = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
        
        result = {
            "name": timezone,
            "country_code": country_code,
            "current_time": now.isoformat(),
            "offset": offset_str,
            "is_dst": now.dst().total_seconds() > 0
        }
        
        # Store in cache for 5 minutes
        time_cache.set(f"timezone_info:{timezone}", result, 300)
        
        return result
    except Exception as e:
        logger.error(f"Error getting timezone info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing timezone info: {str(e)}")

@router.get("/popular-timezones", response_model=List[TimezoneInfo])
async def get_popular_timezones():
    """
    Get information for popular time zones.
    """
    popular_zones = [
        "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Europe/Berlin",
        "Asia/Tokyo", "Asia/Shanghai", "Asia/Dubai",
        "Australia/Sydney", "Pacific/Auckland"
    ]
    
    results = []
    for zone in popular_zones:
        try:
            info = await get_timezone_info(zone)
            results.append(info)
        except Exception as e:
            logger.error(f"Error getting info for {zone}: {str(e)}")
    
    return results

@router.post("/convert", response_model=ConversionResponse)
async def convert_time(request: ConversionRequest, current_user: User = Depends(get_current_user)):
    """
    Convert a UTC timestamp to a target timezone with DST handling.
    """
    # Generate cache key based on request
    cache_key = f"convert:{request.utc_timestamp}:{request.target_timezone}"
    
    # Try to get from cache first
    cached_result = time_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        # Parse the UTC timestamp
        utc_time = parser.parse(request.utc_timestamp)
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        
        # Convert to target timezone
        target_tz = pytz.timezone(request.target_timezone)
        local_time = utc_time.astimezone(target_tz)
        
        # Get DST information
        is_dst = local_time.dst().total_seconds() > 0
        
        # Calculate offset
        offset_seconds = local_time.utcoffset().total_seconds()
        offset_hours = int(offset_seconds // 3600)
        offset_minutes = int((offset_seconds % 3600) // 60)
        offset_str = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
        
        result = {
            "utc_timestamp": utc_time.isoformat(),
            "local_timestamp": local_time.isoformat(),
            "timezone": request.target_timezone,
            "offset": offset_str,
            "is_dst": is_dst
        }
        
        # Store in cache for 1 hour (since timezone rules don't change frequently)
        time_cache.set(cache_key, result, 3600)
        
        return result
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error converting time: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting time: {str(e)}")

@router.get("/convert", response_model=ConversionResponse)
async def convert_time_get(
    utc_timestamp: str = Query(..., description="UTC timestamp in ISO 8601 format"),
    target_timezone: str = Query(..., description="Target timezone (e.g., 'America/New_York')"),
    current_user: User = Depends(get_current_user)
):
    """
    Convert a UTC timestamp to a target timezone with DST handling (GET method).
    """
    request = ConversionRequest(utc_timestamp=utc_timestamp, target_timezone=target_timezone)
    return await convert_time(request, current_user)

@router.get("/now/{timezone}", response_model=Dict)
async def get_current_time(timezone: str):
    """
    Get the current time in the specified timezone.
    """
    if timezone not in pytz.all_timezones:
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {timezone}")
    
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        # Get UTC time
        utc_now = datetime.now(timezone.utc)
        
        # Calculate offset
        offset_seconds = now.utcoffset().total_seconds()
        offset_hours = int(offset_seconds // 3600)
        offset_minutes = int((offset_seconds % 3600) // 60)
        offset_str = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
        
        return {
            "timezone": timezone,
            "local_time": now.isoformat(),
            "utc_time": utc_now.isoformat(),
            "offset": offset_str,
            "is_dst": now.dst().total_seconds() > 0
        }
    except Exception as e:
        logger.error(f"Error getting current time: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting current time: {str(e)}")

# Flask-compatible functions
def convert_flask_time():
    """
    Flask-compatible function to convert UTC time to a target timezone.
    """
    try:
        data = request.get_json()
        utc_timestamp = data.get('utc_timestamp')
        target_timezone = data.get('target_timezone')
        
        if not utc_timestamp or not target_timezone:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Validate timestamp
        try:
            parser.parse(utc_timestamp)
        except Exception:
            return jsonify({"error": "Invalid timestamp format. Use ISO 8601 format (e.g., '2023-05-01T12:00:00Z')"}), 400
            
        # Validate timezone
        if target_timezone not in pytz.all_timezones:
            return jsonify({"error": f"Invalid timezone: {target_timezone}"}), 400
            
        # Generate cache key
        cache_key = f"convert:{utc_timestamp}:{target_timezone}"
        
        # Try to get from cache first
        cached_result = time_cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)
            
        # Parse the UTC timestamp
        utc_time = parser.parse(utc_timestamp)
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=timezone.utc)
            
        # Convert to target timezone
        target_tz = pytz.timezone(target_timezone)
        local_time = utc_time.astimezone(target_tz)
            
        # Get DST information
        is_dst = local_time.dst().total_seconds() > 0
            
        # Calculate offset
        offset_seconds = local_time.utcoffset().total_seconds()
        offset_hours = int(offset_seconds // 3600)
        offset_minutes = int((offset_seconds % 3600) // 60)
        offset_str = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
            
        result = {
            "utc_timestamp": utc_time.isoformat(),
            "local_timestamp": local_time.isoformat(),
            "timezone": target_timezone,
            "offset": offset_str,
            "is_dst": is_dst
        }
            
        # Store in cache for 1 hour
        time_cache.set(cache_key, result, 3600)
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error converting time: {str(e)}")
        return jsonify({"error": f"Error converting time: {str(e)}"}), 500

def get_all_timezones_flask():
    """
    Flask-compatible function to get all available timezones.
    """
    return jsonify(pytz.all_timezones)

def get_timezone_info_flask(timezone):
    """
    Flask-compatible function to get timezone information.
    """
    if timezone not in pytz.all_timezones:
        return jsonify({"error": f"Invalid timezone: {timezone}"}), 400
        
    # Try to get from cache first
    cached_info = time_cache.get(f"timezone_info:{timezone}")
    if cached_info:
        return jsonify(cached_info)
        
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
            
        # Get country code if available
        country_code = None
        for code, timezones in pytz.country_timezones.items():
            if timezone in timezones:
                country_code = code
                break
            
        # Calculate offset in hours and minutes
        offset_seconds = now.utcoffset().total_seconds()
        offset_hours = int(offset_seconds // 3600)
        offset_minutes = int((offset_seconds % 3600) // 60)
        offset_str = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
            
        result = {
            "name": timezone,
            "country_code": country_code,
            "current_time": now.isoformat(),
            "offset": offset_str,
            "is_dst": now.dst().total_seconds() > 0
        }
            
        # Store in cache for 5 minutes
        time_cache.set(f"timezone_info:{timezone}", result, 300)
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting timezone info: {str(e)}")
        return jsonify({"error": f"Error processing timezone info: {str(e)}"}), 500

def get_popular_timezones_flask():
    """
    Flask-compatible function to get popular timezones.
    """
    popular_zones = [
        "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Europe/Berlin",
        "Asia/Tokyo", "Asia/Shanghai", "Asia/Dubai",
        "Australia/Sydney", "Pacific/Auckland"
    ]
        
    results = []
    for zone in popular_zones:
        try:
            # Try to get from cache first
            cached_info = time_cache.get(f"timezone_info:{zone}")
            if cached_info:
                results.append(cached_info)
                continue
                
            tz = pytz.timezone(zone)
            now = datetime.now(tz)
                
            # Get country code if available
            country_code = None
            for code, timezones in pytz.country_timezones.items():
                if zone in timezones:
                    country_code = code
                    break
                
            # Calculate offset in hours and minutes
            offset_seconds = now.utcoffset().total_seconds()
            offset_hours = int(offset_seconds // 3600)
            offset_minutes = int((offset_seconds % 3600) // 60)
            offset_str = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
                
            result = {
                "name": zone,
                "country_code": country_code,
                "current_time": now.isoformat(),
                "offset": offset_str,
                "is_dst": now.dst().total_seconds() > 0
            }
                
            # Store in cache for 5 minutes
            time_cache.set(f"timezone_info:{zone}", result, 300)
            results.append(result)
        except Exception as e:
            logger.error(f"Error getting info for {zone}: {str(e)}")
        
    return jsonify(results)
