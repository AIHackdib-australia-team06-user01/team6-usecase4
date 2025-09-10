# FastAPI Backend Service

This is a FastAPI-based backend service that provides an endpoint to receive a list of strings.

## Prerequisites

- Python 3.9+
- Python venv module (usually comes with Python installation)
- Docker (optional)

## Development Setup

It's recommended to use a virtual environment to keep dependencies isolated. Make sure to add `be-venv/` to your `.gitignore` file to avoid committing the virtual environment to version control.

## Project Structure

```
be/
├── main.py          # FastAPI application
├── requirements.txt # Python dependencies
└── Dockerfile       # Docker configuration
```

## API Endpoints

### POST /strings

Accepts a list of strings and returns them in the response.

**Request Body:**
```json
{
    "items": ["string1", "string2", "string3"]
}
```

**Response:**
```json
{
    "received_strings": ["string1", "string2", "string3"]
}
```

## Running the Application

### Local Development with Virtual Environment

1. Create a virtual environment:
```bash
python -m venv be-venv
```

2. Activate the virtual environment:
```bash
# On Linux/macOS
source be-venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server (you have two options):

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The `--reload` flag enables hot reloading during development - the server will automatically restart when you make code changes.

5. The API will be available at:
   - Conduct Assessment of Provided ISM Control: http://localhost:8000/conduct-assessment
   - API documentation: http://localhost:8000/docs

6. To deactivate the virtual environment when you're done:
   ```bash
   deactivate
   ```

### Using Docker

1. Build the Docker image:
```bash
docker build -t fastapi-app .
```

2. Run the container:
```bash
docker run -p 8000:8000 fastapi-app
```

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): http://localhost:8000/docs
