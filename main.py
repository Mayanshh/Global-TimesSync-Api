import os
import logging
import pytz
from datetime import datetime, timedelta, timezone
from dateutil import parser
import jwt
from passlib.context import CryptContext
from flask import Flask, render_template, request, jsonify, send_from_directory, Blueprint

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("JWT_SECRET", "insecure_default_secret_key_for_development")

# Initialize password context for authentication
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Secret and configuration
SECRET_KEY = os.environ.get("JWT_SECRET", "insecure_default_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mock user database (would be replaced with a real database in production)
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "user@example.com",
        "hashed_password": pwd_context.hash("password123"),
        "disabled": False,
    }
}

# Create a simple in-memory cache
class TimeCache:
    def __init__(self):
        self.cache = {}
        logger.debug("Initialized TimeCache")
        
    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if entry["expiry"] > datetime.now():
                return entry["value"]
            else:
                del self.cache[key]
        return None
        
    def set(self, key, value, ttl=3600):
        self.cache[key] = {
            "value": value,
            "expiry": datetime.now() + timedelta(seconds=ttl)
        }
        
    def clear(self):
        self.cache.clear()

# Initialize cache
time_cache = TimeCache()

# Auth helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username):
    if username in db:
        user_dict = db[username]
        return user_dict
    return None

def authenticate_user(db, username, password):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data, expires_delta=None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

# Create API blueprints
timesync_bp = Blueprint('timesync', __name__, url_prefix='/api/timesync')
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# TimeSync Routes
@timesync_bp.route('/convert', methods=['POST', 'GET'])
def convert_time_route():
    try:
        if request.method == 'GET':
            utc_timestamp = request.args.get('utc_timestamp')
            target_timezone = request.args.get('target_timezone')
        else:
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

@timesync_bp.route('/timezones', methods=['GET'])
def get_timezones_route():
    return jsonify(pytz.all_timezones)

@timesync_bp.route('/timezones/<timezone>', methods=['GET'])
def get_timezone_info_route(timezone):
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

@timesync_bp.route('/popular', methods=['GET'])
@timesync_bp.route('/popular-timezones', methods=['GET'])
def get_popular_timezones_route():
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

# Auth Routes
@auth_bp.route('/token', methods=['POST'])
def login_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400
            
        user = authenticate_user(fake_users_db, username, password)
        if not user:
            return jsonify({"error": "Incorrect username or password"}), 401
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        
        return jsonify({"access_token": access_token, "token_type": "bearer"})
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@auth_bp.route('/register', methods=['POST'])
def register_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        if not username or not email or not password:
            return jsonify({"error": "Missing required fields"}), 400
            
        if username in fake_users_db:
            return jsonify({"error": "Username already registered"}), 400
            
        # Create a new user with hashed password
        hashed_password = get_password_hash(password)
        
        # In a real application, you would save this to a database
        fake_users_db[username] = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "disabled": False,
        }
        
        return jsonify({
            "username": username,
            "email": email,
            "full_name": full_name,
            "disabled": False
        })
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@auth_bp.route('/users/me', methods=['GET'])
def current_user_route():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
            
        token = auth_header.split(' ')[1]
        
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid token"}), 401
            
        username = payload.get("sub")
        user = get_user(fake_users_db, username)
        if not user:
            return jsonify({"error": "User not found"}), 401
            
        if user["disabled"]:
            return jsonify({"error": "Inactive user"}), 400
            
        return jsonify({
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "disabled": user["disabled"]
        })
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500

# Register blueprints
app.register_blueprint(timesync_bp)
app.register_blueprint(auth_bp)

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Home route
@app.route('/')
def home():
    return render_template('index.html', request=request)

# Dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', request=request)

# API documentation route
@app.route('/api-docs')
def api_docs():
    return render_template('api.html', request=request)

# Protected route example
@app.route('/protected')
def protected_route():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload:
            return jsonify({"status": "success", "data": payload})
        return jsonify({"status": "error", "detail": "Invalid token"}), 401
    return jsonify({"status": "error", "detail": "Invalid authorization header"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
