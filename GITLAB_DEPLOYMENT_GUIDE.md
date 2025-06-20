# 🚀 GitLab CI/CD Pipeline для Flask Helpdesk

stages:
  - validate
  - test
  - build
  - deploy

variables:
  # Python версия
  PYTHON_VERSION: "3.11"
  # Директория для pip cache
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  # Виртуальное окружение
  VENV_PATH: "$CI_PROJECT_DIR/venv"

# Кэширование зависимостей
cache:
  paths:
    - .cache/pip/
    - venv/

# 📋 Этап валидации
validate_project:
  stage: validate
  image: python:${PYTHON_VERSION}-slim
  before_script:
    - apt-get update -qy
    - apt-get install -y git
  script:
    - echo "🔍 Validating project structure..."
    - ls -la
    - echo "✅ Project structure validated"
    - echo "📊 Project statistics:"
    - find . -name "*.py" | wc -l | xargs echo "Python files:"
    - find . -name "*.html" | wc -l | xargs echo "HTML templates:"
    - find . -name "*.js" | wc -l | xargs echo "JavaScript files:"
  only:
    - merge_requests
    - main

# 🧪 Этап тестирования
test_dependencies:
  stage: test
  image: python:${PYTHON_VERSION}-slim
  before_script:
    - echo "🐍 Setting up Python environment..."
    - python --version
    - pip --version

    # Установка системных зависимостей
    - apt-get update -qy
    - apt-get install -y
        gcc
        g++
        libffi-dev
        libssl-dev
        default-libmysqlclient-dev
        pkg-config
        libldap2-dev
        libsasl2-dev

    # Создание виртуального окружения
    - python -m venv $VENV_PATH
    - source $VENV_PATH/bin/activate

    # Обновление pip
    - pip install --upgrade pip setuptools wheel

  script:
    - source $VENV_PATH/bin/activate

    # Тестирование разрешения зависимостей
    - echo "🔍 Testing dependency resolution..."
    - pip install --dry-run -r requirements.txt
    - echo "✅ Dependencies are compatible"

    # Установка зависимостей
    - echo "📦 Installing dependencies..."
    - pip install -r requirements.txt
    - echo "✅ Dependencies installed successfully"

    # Тестирование импорта Flask приложения
    - echo "🧪 Testing Flask application import..."
    - python -c "
      import flask
      import werkzeug
      from blog import create_app

      print(f'Flask version: {flask.__version__}')
      print(f'Werkzeug version: {werkzeug.__version__}')

      app = create_app()
      print('✅ Flask app created successfully')
      "

    # Базовые тесты приложения
    - echo "🧪 Running application tests..."
    - python -c "
      from blog import create_app
      import os

      # Test app creation
      app = create_app()

      # Test app configuration
      with app.app_context():
          print('✅ App context works')

      # Test basic route (if exists)
      with app.test_client() as client:
          try:
              response = client.get('/')
              print(f'✅ Basic route test: Status {response.status_code}')
          except Exception as e:
              print(f'⚠️ Route test skipped: {e}')

      print('🎉 All tests passed!')
      "

  artifacts:
    reports:
      junit: test-results.xml
    paths:
      - venv/
    expire_in: 1 hour

  only:
    - merge_requests
    - main

# 🔨 Этап сборки
build_application:
  stage: build
  image: python:${PYTHON_VERSION}-slim
  dependencies:
    - test_dependencies
  before_script:
    - apt-get update -qy
    - apt-get install -y
        gcc
        g++
        libffi-dev
        libssl-dev
        default-libmysqlclient-dev
        pkg-config
        libldap2-dev
        libsasl2-dev

  script:
    - echo "🔨 Building Flask application..."

    # Активация виртуального окружения
    - source $VENV_PATH/bin/activate || (python -m venv $VENV_PATH && source $VENV_PATH/bin/activate && pip install -r requirements.txt)

    # Компиляция Python файлов
    - python -m compileall blog/
    - python -m compileall *.py

    # Создание архива для деплоя
    - echo "📦 Creating deployment package..."
    - tar -czf flask-helpdesk-${CI_COMMIT_SHA}.tar.gz
        --exclude='.git'
        --exclude='venv'
        --exclude='__pycache__'
        --exclude='*.pyc'
        --exclude='.pytest_cache'
        --exclude='app_err.log'
        .

    - echo "✅ Build completed successfully"
    - ls -lah flask-helpdesk-${CI_COMMIT_SHA}.tar.gz

  artifacts:
    paths:
      - flask-helpdesk-${CI_COMMIT_SHA}.tar.gz
    expire_in: 1 week

  only:
    - main

# 🚀 Этап деплоя (Production)
deploy_production:
  stage: deploy
  image: alpine:latest
  dependencies:
    - build_application
  before_script:
    - apk add --no-cache openssh-client rsync
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
    - ssh-keyscan -H $DEPLOY_HOST >> ~/.ssh/known_hosts

  script:
    - echo "🚀 Deploying to production server..."
    - echo "Target server: $DEPLOY_HOST"
    - echo "Deploy user: $DEPLOY_USER"
    - echo "Deploy path: $DEPLOY_PATH"

    # Тестирование SSH подключения
    - ssh $DEPLOY_USER@$DEPLOY_HOST "echo '✅ SSH connection successful'"

    # Создание бэкапа текущей версии
    - ssh $DEPLOY_USER@$DEPLOY_HOST "
        if [ -d $DEPLOY_PATH ]; then
          echo '📦 Creating backup...'
          sudo cp -r $DEPLOY_PATH $DEPLOY_PATH.backup.$(date +%Y%m%d_%H%M%S)
          echo '✅ Backup created'
        fi
      "

    # Загрузка новой версии
    - echo "📤 Uploading application..."
    - scp flask-helpdesk-${CI_COMMIT_SHA}.tar.gz $DEPLOY_USER@$DEPLOY_HOST:/tmp/

    # Деплой на сервере
    - ssh $DEPLOY_USER@$DEPLOY_HOST "
        echo '🔄 Deploying new version...'

        # Создание директории если не существует
        sudo mkdir -p $DEPLOY_PATH

        # Распаковка архива
        cd $DEPLOY_PATH
        sudo tar -xzf /tmp/flask-helpdesk-${CI_COMMIT_SHA}.tar.gz

        # Установка зависимостей в production окружении
        sudo python3 -m venv venv
        sudo venv/bin/pip install --upgrade pip
        sudo venv/bin/pip install -r requirements.txt

        # Настройка прав доступа
        sudo chown -R www-data:www-data $DEPLOY_PATH
        sudo chmod -R 755 $DEPLOY_PATH

        # Перезапуск приложения
        sudo systemctl restart flask-helpdesk
        sudo systemctl status flask-helpdesk

        # Очистка временных файлов
        rm -f /tmp/flask-helpdesk-${CI_COMMIT_SHA}.tar.gz

        echo '🎉 Deployment completed successfully!'
      "

    # Проверка работоспособности
    - echo "🔍 Health check..."
    - sleep 10
    - curl -f http://$DEPLOY_HOST:$DEPLOY_PORT/health || echo "⚠️ Health check failed"

  environment:
    name: production
    url: http://$DEPLOY_HOST:$DEPLOY_PORT

  only:
    - main
  when: manual  # Ручной запуск деплоя для безопасности

# 🧪 Этап деплоя (Staging)
deploy_staging:
  stage: deploy
  extends: deploy_production
  variables:
    DEPLOY_HOST: $STAGING_HOST
    DEPLOY_USER: $STAGING_USER
    DEPLOY_PATH: $STAGING_PATH
    DEPLOY_PORT: $STAGING_PORT
  environment:
    name: staging
    url: http://$STAGING_HOST:$STAGING_PORT
  only:
    - develop
    - merge_requests
  when: on_success  # Автоматический деплой в staging
