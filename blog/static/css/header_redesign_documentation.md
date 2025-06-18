# Документация по редизайну заголовка "Мои задачи в Redmine"

## Обзор

Современный редизайн заголовка страницы задач с улучшенной визуальной иерархией, адаптивностью и множеством вариантов кастомизации.

## Основные особенности

### 1. Визуальные улучшения
- **Градиентный фон** с анимированным декоративным паттерном
- **Анимированная иконка** с эффектом пульсации и hover-анимацией
- **Градиентный текст заголовка** для современного вида
- **Современные кнопки** с различными эффектами hover и active состояний

### 2. Адаптивный дизайн
- **Десктоп (>1024px)**: Полноразмерный вид с горизонтальным расположением
- **Планшеты (768-1024px)**: Уменьшенные размеры элементов
- **Мобильные (<768px)**: Вертикальное расположение, кнопки на всю ширину
- **Маленькие экраны (<480px)**: Минимальные размеры, без декоративных элементов

### 3. Цветовые схемы

#### Схема 1: Корпоративный синий (по умолчанию)
```css
--primary-color: #2563eb;
--primary-hover: #1d4ed8;
--primary-light: #dbeafe;
--primary-dark: #1e40af;
```

#### Схема 2: Корпоративный фиолетовый
```html
<header class="page-header theme-purple">
```

## Варианты использования

### 1. Базовый вариант
```html
<header class="page-header">
  <div class="header-content">
    <div class="header-main">
      <div class="header-icon">
        <i class="fas fa-tasks"></i>
      </div>
      <div class="header-text">
        <h1 class="page-title">Мои задачи в Redmine</h1>
        <p class="page-subtitle">Управление и мониторинг ваших задач в Redmine</p>
      </div>
    </div>
    <div class="header-actions">
      <a href="#" class="action-button secondary">
        <i class="fas fa-external-link-alt"></i>
        <span>Перейти в Redmine</span>
      </a>
      <a href="#" class="action-button primary">
        <i class="fas fa-ticket-alt"></i>
        <span>Мои заявки</span>
      </a>
    </div>
  </div>
</header>
```

### 2. Вариант со статистикой
```html
<header class="page-header">
  <div class="header-content">
    <div class="header-main">
      <div class="header-icon">
        <i class="fas fa-tasks"></i>
      </div>
      <div class="header-text">
        <h1 class="page-title">Мои задачи в Redmine</h1>
        <p class="page-subtitle">Управление и мониторинг ваших задач в Redmine</p>
        <div class="header-stats">
          <span class="stat-item">
            <i class="fas fa-clock"></i>
            <span class="stat-value">12</span>
            <span class="stat-label">активных</span>
          </span>
          <span class="stat-item">
            <i class="fas fa-check-circle"></i>
            <span class="stat-value">48</span>
            <span class="stat-label">выполнено</span>
          </span>
        </div>
      </div>
    </div>
    <div class="header-actions">
      <!-- Кнопки -->
    </div>
  </div>
</header>
```

### 3. Компактный вариант
```html
<header class="page-header compact">
  <!-- Содержимое -->
</header>
```

### 4. Sticky заголовок
```html
<header class="page-header sticky">
  <!-- Содержимое -->
</header>
```

## Варианты кнопок

### 1. Стандартные кнопки
```html
<a href="#" class="action-button primary">Первичная</a>
<a href="#" class="action-button secondary">Вторичная</a>
```

### 2. Кнопки с градиентной рамкой
```html
<a href="#" class="action-button gradient-border">Градиент</a>
```

### 3. Неоновые кнопки
```html
<a href="#" class="action-button neon">Неон</a>
```

### 4. Минималистичные кнопки
```html
<a href="#" class="action-button minimal">Минимал</a>
```

### 5. Кнопка с индикатором
```html
<a href="#" class="action-button primary">
  <i class="fas fa-bell"></i>
  <span>Уведомления</span>
  <span class="icon-badge">3</span>
</a>
```

### 6. Кнопка загрузки
```html
<a href="#" class="action-button primary loading">
  <span>Загрузка...</span>
</a>
```

## Интеграция

### 1. Подключение стилей
```html
<link rel="stylesheet" href="modern_header_redesign.css">
<link rel="stylesheet" href="modern_header_extended.css">
```

### 2. Переопределение цветов
```css
.page-header {
  --primary-color: #your-color;
  --primary-hover: #your-hover-color;
  --primary-light: #your-light-color;
  --primary-dark: #your-dark-color;
}
```

### 3. JavaScript интеграция для sticky заголовка
```javascript
window.addEventListener('scroll', () => {
  const header = document.querySelector('.page-header.sticky');
  if (window.scrollY > 100) {
    header.classList.add('scrolled');
  } else {
    header.classList.remove('scrolled');
  }
});
```

## Доступность

- Все интерактивные элементы имеют `aria-label`
- Поддержка клавиатурной навигации
- Высококонтрастный режим
- Поддержка режима reduced motion
- Семантическая HTML структура

## Производительность

- CSS переменные для легкой кастомизации без дублирования кода
- Оптимизированные анимации с использованием `transform` и `opacity`
- Lazy-loading для декоративных элементов
- Минимальное использование JavaScript

## Поддержка браузеров

- Chrome/Edge: последние 2 версии
- Firefox: последние 2 версии
- Safari: последние 2 версии
- Мобильные браузеры: iOS Safari 12+, Chrome Android

## Примечания

1. Для корректной работы требуется Font Awesome 5.x
2. Градиентный текст может не отображаться в старых браузерах (будет использован fallback)
3. Анимации автоматически отключаются при `prefers-reduced-motion: reduce`
4. Темная тема автоматически применяется при `prefers-color-scheme: dark`
