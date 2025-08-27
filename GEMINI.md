1# Gemini Project Context: Flask Helpdesk

This document provides context for the AI assistant to understand the Flask Helpdesk project.

## Project Overview

This is a comprehensive helpdesk and task management system built with Flask. It features a Kanban board, a robust notification system, and integrations with external systems like Redmine and Oracle ERP.

### Key Technologies

*   **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-SocketIO
*   **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
*   **Database:** SQLite (for local development), MySQL (for Redmine integration)
*   **Task Scheduling:** APScheduler
*   **Testing:**
    *   **E2E:** Playwright
    *   **Unit/Integration:** Pytest
*   **Integrations:**
    *   Redmine API for task synchronization.
    *   Oracle ERP for user authentication.
*   **Deployment:** The project is set up for deployment using Docker, Nginx, and Gunicorn.

### Directory Structure

*   `app.py`: The main entry point for running the development server.
*   `blog/`: The main Flask application package.
    *   `__init__.py`: Application factory (`create_app`).
    *   `models.py`: SQLAlchemy database models.
    *   `tasks/`, `users/`: Blueprints for different application modules.
    *   `notification_service.py`: Handles push and WebSocket notifications.
*   `requirements.txt`: Python dependencies.
*   `package.json`: Node.js dependencies (primarily for Playwright).
*   `tests/`: Contains Playwright E2E tests.
*   `docs/`: Project documentation.
*   `.env.development`, `.env.production`: Environment variable files for different configurations.
*   `playwright.config.js`: Configuration for Playwright tests.

## Building and Running

### Development

1.  **Set up Environment:**
    *   Create and activate a Python virtual environment.
    *   Install Python dependencies: `pip install -r requirements.txt`
    *   Install Node.js dependencies: `npm install`

2.  **Configure:**
    *   Copy `.env.development` to `.env` and fill in the necessary values for databases, Redmine, and other services.

3.  **Run Application:**
    *   Execute `python app.py` to start the Flask development server.
    *   The application will be available at `http://localhost:5000`.

### Testing

*   **Run all Playwright E2E tests:**
    ```bash
    npm test
    ```
*   **Run Python tests:**
    ```bash
    pytest tests/
    ```
*   **View Playwright report:**
    ```bash
    npm run show-report
    ```

## Development Conventions

*   **Code Style:**
    *   Python: PEP 8, formatted with Black. Use `flake8` for linting.
    *   JavaScript: Follows standard conventions, linting is not explicitly configured but can be added.
*   **Commits:** The `README.md` suggests using Conventional Commits, but this is not enforced.
*   **Branching:** A feature-branch workflow is recommended (e.g., `feature/my-new-feature`).
*   **Environment Variables:** All configuration should be done through environment variables loaded from `.env` files. Do not hardcode secrets or configuration in the code.
