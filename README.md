# team6-usecase4
team6 usecase4


## Installation 

- optional, install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
```bash
uv venv 
source .venv/bin/activate
uv pip install -U .
```

## Running with Docker Compose

You can run both the backend and frontend together using Docker Compose. This will build and start both services in containers.

1. Build and start the services:
   ```bash
   docker compose up --build -d
   ```
   - The backend (FastAPI) will be available at http://localhost:8000
   - The frontend (Vue) will be available at http://localhost

2. To stop the services:
   ```bash
   docker compose down
   ```

Make sure Docker is installed and running on your system.