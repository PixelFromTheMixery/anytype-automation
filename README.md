# Anytype Automation

A FastAPI-based automation service for managing tasks and workflows in Anytype, integrated with Pushover for notifications.

## Overview

This project provides API endpoints and scheduled jobs to automate various aspects of Anytype task management, including:

- Daily task rollovers (resetting overdue tasks)
- Recurrent task maintenance checks
- Task collection management based on projects
- Pushover notifications for task alerts and ritual reminders
- Search functionality within Anytype objects

## Features

### API Endpoints

- **Anytype Endpoints** (`/anytype`):
  - `GET /daily_rollover`: Update overdue tasks and reset due dates
  - `POST /list_views`: Fetch automation list views
  - `GET /recurrent_check`: Perform task maintenance
  - `POST /search`: Search for objects in Anytype
  - `GET /other_anytype`: Miscellaneous automation endpoint
  - `GET /test_anytype`: Test endpoint

- **Pushover Endpoints** (`/pushover`):
  - `GET /test_pushover`: Test notification creation
  - `GET /regular_task_alert`: Send task status notifications

- **General Endpoints** (`/general`):
  - `GET /health`: Health check endpoint
  - `GET /`: Root endpoint

### Scheduled Jobs

The application includes automated scheduling using APScheduler:

- **Recurrent Check**: Runs every 30 minutes from 7 AM to 9 PM
- **Daily Rollover**: Runs daily at 11 PM
- **Task Notifications**: Runs at 6 AM, 10 AM, 2 PM, and 6 PM
- **Ritual Notifications**: Commented out jobs for morning/evening rituals and planning logs

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd anytype-automation
   ```

2. Install dependencies:
   ```bash
   pip install -r reqs.txt
   ```

3. Configure the application:
   - Update `utils/config.yaml` with your Anytype spaces, collections, and API details
   - Set up environment variables for Pushover API keys and Anytype credentials

4. Run the application:
   - For production with scheduling: `python main.py`
   - For local development: `python main_local.py`

## Configuration

The `utils/config.yaml` file contains:

- Anytype API URL and user ID
- Space IDs for main and archive spaces
- Collection IDs for different project categories
- Query and view IDs for automation
- Template IDs for rituals and reflections

## Dependencies

Key dependencies include:
- FastAPI: Web framework
- APScheduler: Job scheduling
- Requests: HTTP client for API calls
- Pydantic: Data validation
- Python-dateutil: Date manipulation

## Usage

### Running the Server

```bash
# With scheduling (production)
uvicorn main:app --host 0.0.0.0 --port 8000

# Local development
uvicorn main_local:app --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Health Check

```bash
curl http://localhost:8000/general/health
```

## Project Structure

```
anytype-automation/
├── main.py                 # Main FastAPI app with scheduling
├── main_local.py           # Local development version
├── reqs.txt                # Python dependencies
├── README.md               # This file
├── middlewares/            # Custom middleware
│   ├── auth_middleware.py
│   └── exception_middleware.py
├── models/                 # Data models
│   └── health.py
├── routers/                # API route handlers
│   ├── anytype_router.py
│   ├── general_router.py
│   └── pushover_router.py
├── services/               # Business logic
│   ├── anytype_service.py
│   ├── health_service.py
│   └── pushover_service.py
├── tests/                  # Test files
│   └── test_anytype_services.py
└── utils/                  # Utilities and configuration
    ├── anytype.py
    ├── api_tools.py
    ├── config.py
    ├── config.yaml
    ├── docs.py
    ├── exception.py
    ├── logger.py
    ├── pushover.py
    └── schedule.py
```

## Contributing

Currently maintained by Pixel from the Mixery.