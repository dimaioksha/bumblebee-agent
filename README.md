# Bumblebee — voice assistant

This project is a smart voice assistant that uses various libraries and interacts with Google Calendar and saves information about your events.

## Prerequisites

- Docker
- Docker Compose

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/dimaioksha/llm-agent-example
   cd llm-agent-example
   ```

2. Create a `.env` file in the root directory and add your environment variables:

   ```env
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_custom_search_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_google_search_engine_id
   CALENDAR_ID=your_calendar_id
   ```

3. Build and run the Docker containers:

   ```bash
   docker-compose up --build
   ```

4. Access the application:

   - The `starter.py` service will be running on `http://localhost:8000`.
   - The `agent.py` service will be running on `http://localhost:8001`.

## Notes

- Ensure that your `keys.json` file is correctly configured and placed in the root directory of the project.
- Modify the `Dockerfile` and `docker-compose.yml` as needed to fit your specific project requirements. 