# Design Document

## Overview

Данный документ описывает техническое решение для исправления проблемы с отображением данных после переключения темы на странице "Мои заявки". Проблема заключается в конфликте между CSS стилями темы и JavaScript функциональностью, а также в неправильной последовательности инициализации компонентов.

## Architecture

### Текущая архитектура (проблемная)
```
Theme Switcher Click → CSS Class Toggle → DOM Re-render → JavaScript Context Lost
```

### Предлагаемая архитектура (исправленная)
```
Theme Switcher Click → CSS Class Toggle → Preserve JavaScript State → Re-initialize Components → Restore Data
```

## Components and Interfaces

### 1. Theme Manager Component
**Назначение:** Управление переключением темы с сохранением состояния приложения

**Интерфейс:**
```javascript
class ThemeManager {
    constructor()
    switchTheme(theme)
    saveTheme(theme)
    loadTheme()
    preserveApplicationState()
    restoreApplicationState()
}
```

### 2. Data State Manager
**Назначение:** Сохранение и восстановление состояния данных таблицы и карточек

**Интерфейс:**
```javascript
class DataStateManager {
    saveTableState()
    restoreTableState()
    saveStatsState()
    restoreStatsState()
    preserveFilters()
    restoreFilters()
}
```

### 3. Enhanced Issues Table Component
**Назначение:** Улучшенная таблица с поддержкой переключения темы

**Интерфейс:**
```javascript
class EnhancedIssuesTable {
    initialize()
    reinitialize()
    preserveState()
    restoreState()
    handleThemeChange()
}
```

## Data Models

### Theme State Model
```javascript
{
    currentTheme: 'light' | 'dark',
    timestamp: number,
    userPreference: boolean
}
```

### Table State Model
```javascript
{
    currentPage: number,
    pageLength: number,
    searchTerm: string,
    sortColumn: number,
    sortDirection: 'asc' | 'desc',
    statusFilter: string,
    data: Array<IssueData>
}
```

### Statistics State Model
```javascript
{
    totalIssues: number,
    openIssues: number,
    inProgressIssues: number,
    closedIssues: number,
    detailsByCategory: Object,
    expandedCards: Array<string>
}
```

## Error Handling

### 1. CSS Loading Errors
- Проверка загрузки CSS стилей темы
- Fallback к базовым стилям при ошибке
- Логирование ошибок загрузки стилей

### 2. JavaScript State Loss
- Автоматическое восстановление состояния из localStorage
- Повторная инициализация компонентов при потере контекста
- Graceful degradation при ошибках восстановления

### 3. Data Loading Errors
- Сохранение данных в sessionStorage как backup
- Повторный запрос данных при потере состояния
- Отображение индикатора загрузки при восстановлении

## Testing Strategy

### 1. Unit Tests
- Тестирование ThemeManager
- Тестирование DataStateManager
- Тестирование сохранения/восстановления состояния

### 2. Integration Tests
- Тестирование переключения темы с данными в таблице
- Тестирование сохранения фильтров при переключении
- Тестирование работы пагинации после смены темы

### 3. Manual Testing Scenarios
- Переключение темы на разных страницах таблицы
- Переключение темы с активными фильтрами
- Переключение темы с раскрытыми карточками статистики
- Переключение темы во время загрузки данных

## Implementation Plan

### Phase 1: Диагностика и анализ
1. Анализ текущего кода переключения темы
2. Выявление точных причин потери данных
3. Определение конфликтующих CSS правил
4. Анализ JavaScript ошибок в консоли

### Phase 2: Создание управляющих компонентов
1. Реализация ThemeManager
2. Реализация DataStateManager
3. Интеграция с существующим кодом
4. Тестирование базовой функциональности

### Phase 3: Улучшение таблицы и карточек
1. Модификация инициализации DataTables
2. Добавление обработчиков событий темы
3. Реализация сохранения состояния статистики
4. Тестирование всех сценариев

### Phase 4: Оптимизация и финализация
1. Оптимизация производительности
2. Добавление анимаций переходов
3. Финальное тестирование
4. Документирование изменений

## Technical Specifications

### CSS Improvements
```css
/* Плавные переходы между темами */
.issues-page-container {
    transition: background-color 0.3s ease, color 0.3s ease;
}

/* Предотвращение мерцания при переключении */
.theme-transition {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Сохранение видимости элементов */
.preserve-visibility {
    opacity: 1 !important;
    visibility: visible !important;
}
```

### JavaScript Architecture
```javascript
// Глобальный объект для управления состоянием
window.IssuesPageState = {
    themeManager: null,
    dataStateManager: null,
    issuesTable: null,
    
    initialize() {
        this.themeManager = new ThemeManager();
        this.dataStateManager = new DataStateManager();
        this.setupEventListeners();
    },
    
    handleThemeSwitch(newTheme) {
        // Сохраняем текущее состояние
        this.dataStateManager.saveCurrentState();
        
        // Переключаем тему
        this.themeManager.switchTheme(newTheme);
        
        // Восстанавливаем состояние
        setTimeout(() => {
            this.dataStateManager.restoreCurrentState();
        }, 100);
    }
};
```

### LocalStorage Schema
```javascript
// Схема хранения настроек темы
{
    "helpdesk_theme": {
        "current": "dark",
        "timestamp": 1694808000000,
        "autoSwitch": false
    }
}

// Схема хранения состояния таблицы
{
    "helpdesk_table_state": {
        "page": 2,
        "length": 10,
        "search": "bug",
        "order": [[1, "desc"]],
        "filters": {
            "status": "Открыта"
        }
    }
}
```

## Performance Considerations

### 1. Минимизация перерисовки DOM
- Использование CSS transitions вместо JavaScript анимаций
- Batch обновления DOM элементов
- Отложенная инициализация тяжелых компонентов

### 2. Оптимизация хранения состояния
- Дебаунсинг сохранения состояния
- Сжатие данных в localStorage
- Очистка устаревших данных

### 3. Ленивая загрузка ресурсов
- Предзагрузка CSS стилей темы
- Кеширование данных таблицы
- Оптимизация размера JavaScript бандла

## Security Considerations

### 1. XSS Protection
- Санитизация данных перед сохранением в localStorage
- Валидация восстанавливаемых данных
- Защита от инъекций через настройки темы

### 2. Data Privacy
- Не сохранение чувствительных данных в localStorage
- Автоочистка временных данных
- Соблюдение GDPR при хранении предпочтений