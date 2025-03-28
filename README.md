# Global TimeSync API

A high-performance API service for UTC to local time conversion with automatic DST handling.

## Features

- **Timezone Conversion**: Convert timestamps between UTC and any local timezone
- **DST Handling**: Automatic daylight saving time adjustments
- **Popular Timezones**: Quick access to commonly used timezones
- **High Performance**: Optimized for speed with response caching
- **Developer-friendly**: Simple REST endpoints with clear documentation
- **Interactive Dashboard**: Web interface for manual time conversions
- **Authentication**: Secure API access with JWT authentication

## Getting Started

### Prerequisites

- Python 3.9+
- Flask
- PostgreSQL database
- Additional dependencies in requirements.txt

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/global-timesync-api.git
cd global-timesync-api
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
export JWT_SECRET=your_secure_secret_key
export DATABASE_URL=postgresql://username:password@localhost/timesync
```

4. Run the application
```bash
python main.py
```

## API Endpoints

### Authentication

- **POST /api/auth/token** - Get access token
- **POST /api/auth/register** - Register new user
- **GET /api/auth/users/me** - Get current user details

### Time Conversion

- **POST /api/timesync/convert** - Convert between timezones
- **GET /api/timesync/convert** - Convert between timezones (GET method)
- **GET /api/timesync/timezones** - Get all available timezones
- **GET /api/timesync/timezone/{timezone}** - Get timezone details
- **GET /api/timesync/popular-timezones** - Get popular timezones

## Web Dashboard

Access the web dashboard at `/dashboard` to:
- Convert timestamps between timezones
- View world clocks for popular timezones
- Access conversion history

## Architecture

The Global TimeSync API is built with a focus on performance and reliability:

- **Web Framework**: Flask
- **Data Models**: SQLAlchemy/Pydantic
- **Authentication**: JWT with bcrypt password hashing
- **Caching**: In-memory cache for timezone data
- **Error Handling**: Comprehensive error handling with descriptive messages

## Development

### Project Structure

```
├── api/
│   ├── auth.py         # Authentication logic
│   ├── cache.py        # Caching implementation
│   ├── config.py       # Configuration settings
│   ├── models.py       # Data models
│   └── timesync.py     # Core timezone functionality
├── static/             # Static assets
├── templates/          # HTML templates
├── main.py             # Application entry point
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [pytz](https://pythonhosted.org/pytz/) for timezone database
- [Flask](https://flask.palletsprojects.com/) web framework
- Built by Mayansh Bangali (https://github.com/Mayanshh)