# Global TimeSync API

A high-performance API service for UTC to local time conversion with automatic DST handling.

## Features

- **Time Zone Conversion**: Convert UTC timestamps to any target time zone with proper DST handling
- **Comprehensive Time Zone Database**: Support for all standard IANA time zones
- **High Performance**: Built with performance in mind, including robust caching
- **Easy Integration**: Simple REST API for seamless integration into any application
- **User Authentication**: Secure JWT-based authentication system
- **Interactive Dashboard**: Web-based dashboard for manual time conversions
- **Detailed Time Zone Information**: Get offset, DST status, and current time for any zone

## Quick Start

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables (see `.env.example`)
4. Run the application:
   ```
   python main.py
   ```
5. Access the dashboard at `http://localhost:5000/`
6. API documentation available at `http://localhost:5000/api`

## API Endpoints

### Authentication

- `POST /login`: Obtain JWT access token
- `POST /register`: Register a new user
- `GET /users/me`: Get current user information

### Time Zone Operations

- `GET /timezones`: List all available time zones
- `GET /timezones/popular`: Get popular time zones
- `GET /timezones/{timezone}`: Get detailed information about a specific time zone
- `POST /convert`: Convert a UTC timestamp to a target time zone
- `GET /convert`: Convert a UTC timestamp (query parameters)

## Dashboard

The dashboard provides a user-friendly interface for:

- Converting timestamps between time zones
- Viewing a world clock of popular time zones
- Accessing your conversion history
- Managing favorite time zones

## Development

### Prerequisites

- Python 3.9+
- Flask
- PostgreSQL (optional for production)

### Environment Variables

Create a `.env` file based on `.env.example` with the following variables:

- `JWT_SECRET`: Secret key for JWT token generation
- `DATABASE_URL`: PostgreSQL connection string (optional)
- `FLASK_ENV`: Set to 'development' or 'production'
- `FLASK_APP`: Set to 'main.py'

### Running Tests

```
pytest tests/
```

## Deployment

### Deploy to Render (Recommended)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork this repository to your GitHub account
2. Click the "Deploy to Render" button above
3. Follow the prompts to deploy the application

For detailed instructions, see [deployment_guide.md](deployment_guide.md).

## License

MIT

## Author

Developed by Mayansh Bangali - [GitHub Profile](https://github.com/Mayanshh)