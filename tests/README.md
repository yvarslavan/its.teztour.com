# Playwright Тесты для Flask Helpdesk - Модуль Main

Этот каталог содержит автоматизированные тесты Playwright для модуля `main` Flask Helpdesk приложения.

## Структура тестов

```
tests/
├── main.spec.js              # Основные тесты модуля main
├── main-test-pages.spec.js   # Тесты тестовых HTML страниц
└── README.md                 # Этот файл
```

## Предварительные требования

1. **Node.js** версии 16 или выше
2. **Python** с установленными зависимостями Flask приложения
3. **Flask приложение** должно быть запущено на `http://localhost:5000`

## Установка

1. Установите зависимости Node.js:
```bash
npm install
```

2. Установите браузеры для Playwright:
```bash
npm run install-browsers
```

## Запуск тестов

### Основные команды

```bash
# Запустить все тесты
npm test

# Запустить тесты с видимым браузером
npm run test:headed

# Запустить тесты в UI режиме
npm run test:ui

# Запустить тесты в режиме отладки
npm run test:debug

# Запустить только основные тесты модуля main
npm run test:main

# Запустить только тесты тестовых страниц
npm run test:test-pages

# Запустить все тесты с HTML отчетом
npm run test:all
```

### Просмотр отчетов

```bash
# Показать HTML отчет
npm run show-report
```

### Генерация кода

```bash
# Запустить Playwright Codegen для записи тестов
npm run codegen
```

## Конфигурация

Основная конфигурация находится в `playwright.config.js`:

- **Base URL**: `http://localhost:5000`
- **Браузеры**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Отчеты**: HTML, JSON, JUnit
- **Скриншоты**: Только при ошибках
- **Видео**: Сохраняется при ошибках
- **Трассировка**: При повторных попытках

## Структура тестов

### main.spec.js

Основные тесты модуля main включают:

- **UI тесты**: Проверка загрузки страниц, навигации, элементов интерфейса
- **API тесты**: Проверка API endpoints
- **Обработка ошибок**: Тестирование 404, 500 ошибок
- **Производительность**: Время загрузки, оптимизация
- **Доступность**: Структура заголовков, alt атрибуты

### main-test-pages.spec.js

Тесты для тестовых HTML страниц:

- **test_filters_api.html**: Тестирование API фильтров
- **simple_api_test.html**: Базовое тестирование API

## Тестовые страницы

### /test-filters-api

Тестовая страница для проверки API фильтров с функциями:
- Получение фильтров
- Применение фильтра
- Сброс фильтров
- Сохранение фильтра

### /simple-api-test

Простая тестовая страница для базового API с функциями:
- Проверка подключения к серверу
- Тестирование аутентификации
- Получение данных пользователя
- Проверка сессии
- Тестирование главной страницы
- Получение статистики
- Очистка кэша

## Отладка

### Локальная отладка

1. Запустите Flask приложение:
```bash
python app.py
```

2. В другом терминале запустите тесты:
```bash
npm run test:debug
```

### Просмотр трассировки

```bash
# Открыть трассировку в браузере
npx playwright show-trace trace.zip
```

### Логи

Тесты создают логи в следующих каталогах:
- `test-results/` - результаты тестов
- `playwright-report/` - HTML отчеты
- `screenshots/` - скриншоты ошибок
- `videos/` - видео записи

## Интеграция с CI/CD

### GitHub Actions

```yaml
name: Playwright Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-node@v3
      with:
        node-version: 16
    - run: npm ci
    - run: npm run install-browsers
    - run: npm test
    - uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
```

### GitLab CI

```yaml
playwright:
  image: mcr.microsoft.com/playwright:v1.40.0
  script:
    - npm ci
    - npx playwright install --with-deps
    - npm test
  artifacts:
    when: always
    paths:
      - playwright-report/
    reports:
      junit: test-results/results.xml
```

## Устранение неполадок

### Проблемы с подключением

1. Убедитесь, что Flask приложение запущено на `http://localhost:5000`
2. Проверьте, что порт 5000 не занят другими приложениями
3. Проверьте firewall настройки

### Проблемы с браузерами

```bash
# Переустановить браузеры
npx playwright install --force
```

### Проблемы с зависимостями

```bash
# Очистить кэш npm
npm cache clean --force

# Переустановить зависимости
rm -rf node_modules package-lock.json
npm install
```

## Добавление новых тестов

1. Создайте новый файл `.spec.js` в каталоге `tests/`
2. Используйте структуру существующих тестов
3. Добавьте описательные названия тестов на русском языке
4. Обновите этот README при необходимости

## Контакты

При возникновении проблем с тестами обращайтесь к команде разработки Flask Helpdesk.
