# Contributing to Flask Helpdesk System

Thank you for your interest in contributing to the Flask Helpdesk System! This document provides guidelines and information for contributors.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Guidelines](#contributing-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Coding Standards](#coding-standards)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation](#documentation)
9. [Issue Reporting](#issue-reporting)
10. [Community](#community)

## 🤝 Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you agree to uphold these standards:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Show empathy towards other contributors

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git version control
- Basic knowledge of Flask and web development
- Understanding of database systems (SQLite, MySQL, Oracle)

### Development Environment

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/yourusername/flask-helpdesk.git
   cd flask-helpdesk
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Configure environment**
   ```bash
   cp .flaskenv.example .flaskenv
   cp config.ini.example config.ini
   # Edit configuration files with your settings
   ```

5. **Initialize database**
   ```bash
   python -c "from blog import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run tests**
   ```bash
   pytest
   ```

7. **Start development server**
   ```bash
   python app.py
   ```

## 🛠️ Development Setup

### Project Structure

```
flask-helpdesk/
├── app.py                 # Application entry point
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pytest.ini           # Test configuration
├── .flaskenv             # Flask environment variables
├── config.ini            # Application configuration
├── blog/                 # Main application package
│   ├── __init__.py       # Application factory
│   ├── models.py         # Database models
│   ├── settings.py       # Configuration classes
│   ├── tasks/            # Task management module
│   ├── user/             # User management module
│   ├── utils/            # Utility functions
│   └── templates/        # HTML templates
├── tests/                # Test suite
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

### Development Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Key development tools:
# - pytest: Testing framework
# - black: Code formatter
# - flake8: Linting
# - mypy: Type checking
# - pre-commit: Git hooks
```

### Git Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

3. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**
   - Go to GitHub and create a Pull Request
   - Fill out the PR template
   - Wait for review and feedback

## 📝 Contributing Guidelines

### Types of Contributions

- **Bug fixes**: Fix existing issues and problems
- **Features**: Add new functionality to the system
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **Refactoring**: Improve code structure without changing functionality

### Contribution Areas

#### Backend Development
- Flask route handlers and API endpoints
- Database models and migrations
- Business logic and services
- External system integrations
- Background tasks and scheduling

#### Frontend Development
- HTML templates and UI components
- JavaScript functionality
- CSS styling and responsive design
- Progressive Web App features
- Real-time features with WebSocket

#### DevOps and Infrastructure
- Docker configurations
- CI/CD pipeline improvements
- Deployment scripts
- Monitoring and logging
- Performance optimization

#### Documentation
- API documentation updates
- User guides and tutorials
- Code comments and docstrings
- README and setup instructions
- Architecture documentation

## 🔄 Pull Request Process

### Before Submitting

1. **Check existing issues**: Look for related issues or discussions
2. **Run tests**: Ensure all tests pass
3. **Update documentation**: Add or update relevant documentation
4. **Follow coding standards**: Use consistent code style
5. **Write descriptive commit messages**: Use conventional commit format

### PR Requirements

- [ ] Tests pass locally (`pytest`)
- [ ] Code follows style guidelines (`black`, `flake8`)
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional format
- [ ] PR description explains changes clearly
- [ ] Breaking changes are documented

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] Code comments updated
- [ ] API documentation updated
- [ ] README updated if needed

## Breaking Changes
List any breaking changes and migration steps.

## Screenshots (if applicable)
Add screenshots for UI changes.
```

### Review Process

1. **Automated checks**: CI/CD pipeline runs tests and checks
2. **Code review**: Maintainers review the code
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: PR approved by maintainers
5. **Merge**: PR merged into main branch

## 🎨 Coding Standards

### Python Code Style

```python
# Use Black for formatting
black blog/ tests/

# Use flake8 for linting
flake8 blog/ tests/

# Use mypy for type checking
mypy blog/
```

### Code Formatting

- **Line length**: Maximum 88 characters (Black default)
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Add type hints for function parameters and returns

### Example Code Style

```python
from typing import List, Optional, Dict, Any
from flask import request, jsonify
from blog.models import User, Task


def get_user_tasks(
    user_id: int,
    status_filter: Optional[List[str]] = None,
    limit: int = 25
) -> Dict[str, Any]:
    """
    Get tasks assigned to a user with optional filtering.
    
    Args:
        user_id: ID of the user to get tasks for
        status_filter: Optional list of status names to filter by
        limit: Maximum number of tasks to return
        
    Returns:
        Dictionary containing tasks and metadata
        
    Raises:
        ValueError: If user_id is invalid
        DatabaseError: If database query fails
    """
    if user_id <= 0:
        raise ValueError("User ID must be positive")
    
    # Implementation here
    return {
        "tasks": tasks,
        "total": total_count,
        "limit": limit
    }
```

### HTML/CSS Standards

- **Indentation**: 2 spaces for HTML/CSS
- **Bootstrap classes**: Use Bootstrap utilities when possible
- **Accessibility**: Include ARIA labels and semantic HTML
- **Responsive design**: Mobile-first approach

### JavaScript Standards

- **ES6+**: Use modern JavaScript features
- **Async/await**: Prefer over callbacks and promises
- **Error handling**: Always handle errors gracefully
- **Comments**: Document complex logic

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── conftest.py           # Test configuration and fixtures
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_services.py
├── integration/          # Integration tests
│   ├── test_api.py
│   ├── test_auth.py
│   └── test_tasks.py
└── e2e/                  # End-to-end tests
    ├── test_workflows.py
    └── test_ui.py
```

### Writing Tests

```python
import pytest
from blog import create_app, db
from blog.models import User, Task


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_user_creation(app):
    """Test user model creation."""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            password="hashed_password"
        )
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"


def test_api_get_tasks(client, auth_headers):
    """Test task API endpoint."""
    response = client.get(
        "/tasks/api/task/123",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
```

### Test Coverage

- **Minimum coverage**: 80% for new code
- **Critical paths**: 100% coverage for authentication and security
- **Integration tests**: Test API endpoints and workflows
- **Unit tests**: Test individual functions and classes

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=blog --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run tests matching pattern
pytest -k "test_user"

# Run tests with verbose output
pytest -v
```

## 📚 Documentation

### Documentation Types

1. **API Documentation**: Detailed endpoint documentation
2. **User Guides**: How-to guides for end users
3. **Developer Documentation**: Technical implementation details
4. **Code Documentation**: Inline comments and docstrings

### Documentation Standards

- **Markdown format**: Use Markdown for all documentation
- **Clear examples**: Include code examples and usage
- **Up-to-date**: Keep documentation current with code changes
- **Searchable**: Use clear headings and structure

### Docstring Format

```python
def update_task_status(task_id: int, status_id: int, comment: Optional[str] = None) -> Dict[str, Any]:
    """
    Update the status of a task in Redmine.
    
    This function updates a task's status and optionally adds a comment.
    It also triggers notifications to relevant users.
    
    Args:
        task_id: The ID of the task to update
        status_id: The new status ID to set
        comment: Optional comment to add with the status change
        
    Returns:
        Dictionary containing:
            - success (bool): Whether the update succeeded
            - task_id (int): The updated task ID
            - old_status (str): Previous status name
            - new_status (str): New status name
            
    Raises:
        RedmineAuthError: If authentication with Redmine fails
        RedmineNotFoundError: If the task doesn't exist
        ValueError: If task_id or status_id is invalid
        
    Example:
        >>> result = update_task_status(12345, 3, "Task completed")
        >>> print(result['success'])
        True
        >>> print(result['new_status'])
        'Resolved'
    """
```

## 🐛 Issue Reporting

### Before Creating an Issue

1. **Search existing issues**: Check if the issue already exists
2. **Check documentation**: Look for solutions in docs
3. **Test on latest version**: Ensure issue exists in current version
4. **Gather information**: Collect logs, screenshots, environment details

### Issue Template

```markdown
## Bug Description
Clear description of the bug and expected behavior.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.1]
- Flask version: [e.g., 2.3.3]
- Browser: [e.g., Chrome 96.0]

## Logs/Screenshots
Include relevant logs or screenshots.

## Additional Context
Any other relevant information.
```

### Feature Request Template

```markdown
## Feature Description
Clear description of the requested feature.

## Use Case
Explain why this feature would be useful.

## Proposed Solution
Describe how you think it should work.

## Alternatives Considered
Other approaches you've considered.

## Additional Context
Any other relevant information.
```

## 🏷️ Commit Message Format

Use [Conventional Commits](https://conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```bash
feat(auth): add OAuth2 integration
fix(tasks): resolve task status update bug
docs(api): update authentication documentation
test(models): add user model tests
refactor(utils): simplify cache management
```

## 🌟 Recognition

Contributors are recognized in the following ways:

- **Contributors list**: Added to project contributors
- **Changelog mentions**: Significant contributions mentioned in changelog
- **GitHub profile**: Contributions visible on GitHub profile
- **Community recognition**: Acknowledgment in community channels

## 📞 Getting Help

- **Documentation**: Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Issues**: Create an issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions
- **Email**: Contact maintainers at dev@company.com

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Flask Helpdesk System! 🎉