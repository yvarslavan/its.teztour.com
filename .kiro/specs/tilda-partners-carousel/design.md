# Design Document

## Overview

Данный документ описывает техническое решение для создания современного адаптивного компонента бегущей строки партнеров для Тильды. Компонент будет использовать современные CSS технологии, оптимизированные анимации и адаптивный дизайн.

## Architecture

### Компонентная архитектура
```
Tilda HTML Block
├── Hidden Image Container (источник логотипа)
├── Main Partners Section
│   ├── Decorative Background Elements
│   ├── Partners Container
│   │   ├── Logos Track (анимированная область)
│   │   └── Title Section
│   └── CSS Animations & Transitions
└── JavaScript Controller
```

## Components and Interfaces

### 1. Main Container Component
**Назначение:** Основной контейнер с градиентным фоном и декоративными элементами

**Структура:**
```html
<div class="tilda-partners-modern">
  <div class="partners-bg-decoration"></div>
  <div class="partners-content-wrapper">
    <!-- Контент -->
  </div>
</div>
```

### 2. Logos Carousel Component
**Назначение:** Бегущая строка с логотипами и плавными анимациями

**Структура:**
```html
<div class="logos-carousel-container">
  <div class="logos-track" id="logosTrack">
    <!-- Динамически создаваемые логотипы -->
  </div>
</div>
```

### 3. JavaScript Controller
**Назначение:** Управление инициализацией, созданием логотипов и адаптивностью

**Интерфейс:**
```javascript
class TildaPartnersController {
    constructor()
    init()
    createLogos()
    handleResize()
    observeVisibility()
}
```

## Design System

### Цветовая палитра
```css
:root {
  --partners-primary: #667eea;
  --partners-secondary: #764ba2;
  --partners-accent: #f093fb;
  --partners-light: #f8fafc;
  --partners-white: #ffffff;
  --partners-shadow: rgba(0, 0, 0, 0.1);
  --partners-glow: rgba(102, 126, 234, 0.3);
}
```

### Типографика
```css
.partners-title {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-weight: 700;
  line-height: 1.2;
}
```

### Адаптивные брейкпоинты
```css
/* Desktop: 1200px+ */
/* Tablet: 768px - 1199px */
/* Mobile: 320px - 767px */
```

## Technical Specifications

### CSS Architecture
```css
/* Современный подход с CSS Grid и Flexbox */
.tilda-partners-modern {
  display: grid;
  place-items: center;
  min-height: 400px;
  background: linear-gradient(135deg, var(--partners-light) 0%, #e2e8f0 100%);
  position: relative;
  overflow: hidden;
}

/* Оптимизированные анимации */
.logos-track {
  display: flex;
  animation: smoothSlide var(--animation-duration, 30s) linear infinite;
  will-change: transform;
}

@keyframes smoothSlide {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-50%, 0, 0); }
}
```

### JavaScript Architecture
```javascript
// Современный ES6+ подход
class TildaPartnersController {
  constructor(containerId = 'rec1313636551') {
    this.containerId = containerId;
    this.logosTrack = null;
    this.observer = null;
    this.isVisible = false;
    
    this.init();
  }

  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    this.createLogos();
    this.setupIntersectionObserver();
    this.handleResize();
  }
}
```

## Responsive Design Strategy

### Mobile-First подход
```css
/* Базовые стили для мобильных */
.logo-item {
  height: 40px;
  margin: 0 15px;
}

/* Планшеты */
@media (min-width: 768px) {
  .logo-item {
    height: 60px;
    margin: 0 25px;
  }
}

/* Десктоп */
@media (min-width: 1200px) {
  .logo-item {
    height: 80px;
    margin: 0 35px;
  }
}
```

### Адаптивная скорость анимации
```css
.logos-track {
  animation-duration: 20s; /* Мобильные */
}

@media (min-width: 768px) {
  .logos-track {
    animation-duration: 25s; /* Планшеты */
  }
}

@media (min-width: 1200px) {
  .logos-track {
    animation-duration: 30s; /* Десктоп */
  }
}
```

## Performance Optimizations

### 1. CSS Optimizations
```css
/* Использование transform вместо изменения позиции */
.logo-item {
  transform: translateZ(0); /* Включение аппаратного ускорения */
  backface-visibility: hidden;
}

/* Оптимизация анимаций */
@media (prefers-reduced-motion: reduce) {
  .logos-track {
    animation: none;
  }
}
```

### 2. JavaScript Optimizations
```javascript
// Дебаунсинг для resize событий
const debouncedResize = debounce(() => {
  this.handleResize();
}, 250);

// Intersection Observer для видимости
const observerOptions = {
  threshold: 0.1,
  rootMargin: '50px'
};
```

## Accessibility Features

### 1. Семантическая разметка
```html
<section class="tilda-partners-modern" role="region" aria-label="Наши партнеры">
  <h2 class="partners-title">Наши партнеры</h2>
  <div class="logos-carousel" role="img" aria-label="Логотипы партнеров">
    <!-- Логотипы -->
  </div>
</section>
```

### 2. Поддержка клавиатурной навигации
```css
.logo-item:focus {
  outline: 2px solid var(--partners-primary);
  outline-offset: 4px;
}
```

## Browser Compatibility

### Поддерживаемые браузеры
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Fallbacks
```css
/* Fallback для backdrop-filter */
.logos-carousel-container {
  background: rgba(255, 255, 255, 0.9);
}

@supports (backdrop-filter: blur(10px)) {
  .logos-carousel-container {
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.7);
  }
}
```

## Integration with Tilda

### 1. Стилевая изоляция
```css
/* Префиксы для избежания конфликтов */
.tilda-partners-modern * {
  box-sizing: border-box;
}

.tilda-partners-modern {
  /* Сброс стилей Тильды */
  font-family: inherit;
  line-height: inherit;
}
```

### 2. Динамическая инициализация
```javascript
// Автоматическое определение ID блока
const blockId = document.currentScript?.parentElement?.id || 'rec1313636551';
new TildaPartnersController(blockId);
```

## Testing Strategy

### 1. Адаптивное тестирование
- Тестирование на различных размерах экрана
- Проверка производительности анимаций
- Валидация в различных браузерах

### 2. Интеграционное тестирование
- Тестирование в среде Тильды
- Проверка совместимости со стилями Тильды
- Валидация работы с различными темами Тильды