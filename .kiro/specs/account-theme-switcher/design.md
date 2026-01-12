# Design Document

## Overview

Дизайн системы переключения темы для профиля пользователя (account.html) с поддержкой светлой и темной темы. Система должна интегрироваться с существующим дизайном и обеспечивать плавные переходы между темами.

## Architecture

### Component Structure
```
Account Page Theme System
├── Theme Switcher Component (UI)
├── Theme Manager (JavaScript)
├── CSS Variables System (Light/Dark)
└── Local Storage Integration
```

### Theme Switcher Placement
- **Расположение**: В шапке профиля, рядом со статусом "Online"
- **Контейнер**: Добавляется в существующий `user-status-container`
- **Адаптивность**: Корректное отображение на всех размерах экранов

## Components and Interfaces

### 1. HTML Structure
```html
<div class="user-status-container">
    <div class="status-badge online">
        <div class="status-dot"></div>
        <span class="status-text">Online</span>
    </div>
    <div class="theme-switcher-container">
        <button id="theme-switcher" class="theme-switcher" title="Переключить тему">
            <i class="fas fa-sun"></i>
            <i class="fas fa-moon"></i>
        </button>
    </div>
</div>
```

### 2. CSS Architecture

#### Theme Variables Structure
```css
/* Base Variables (Dark Theme - Default) */
.account-page-wrapper {
    --primary-500: #00bcd4;
    --surface-0: #0a0f14;
    --surface-1: #111922;
    --text-primary: #ffffff;
    /* ... other dark theme variables */
}

/* Light Theme Override */
body:not(.dark-theme) .account-page-wrapper {
    --primary-500: #0ea5e9;
    --surface-0: #ffffff;
    --surface-1: #f8fafc;
    --text-primary: #1e293b;
    /* ... other light theme variables */
}
```

#### Theme Switcher Styles
- **Dark Theme**: Полупрозрачный белый фон с иконкой солнца
- **Light Theme**: Полупрозрачный темный фон с иконкой луны
- **Hover Effects**: Увеличение, изменение цвета, тень
- **Transitions**: Плавные анимации (300ms)

### 3. JavaScript Interface

#### AccountThemeManager Class
```javascript
class AccountThemeManager {
    constructor()
    init()
    loadTheme()
    saveTheme(theme)
    applyTheme(theme)
    toggleTheme()
    updateToggleIcon(theme)
}
```

## Data Models

### Theme State Model
```javascript
{
    currentTheme: 'dark' | 'light',
    storageKey: 'account-theme',
    defaultTheme: 'dark'
}
```

### CSS Variables Model
```css
Light Theme Variables:
- Background: Linear gradient #f8fafc → #e2e8f0
- Text: Dark colors (#1e293b, #475569)
- Surfaces: White and light grays
- Shadows: Subtle dark shadows

Dark Theme Variables:
- Background: Linear gradient #0a0f14 → #111922
- Text: Light colors (#ffffff, #e2e8f0)
- Surfaces: Dark blues and grays
- Shadows: Colored shadows with brand colors
```

## Error Handling

### JavaScript Error Handling
1. **localStorage недоступен**: Fallback к темной теме по умолчанию
2. **DOM элементы не найдены**: Graceful degradation без ошибок
3. **SweetAlert недоступен**: Уведомления отключаются без ошибок

### CSS Fallbacks
1. **CSS Variables не поддерживаются**: Fallback цвета в старых браузерах
2. **Backdrop-filter не поддерживается**: Альтернативные фоны
3. **CSS Grid не поддерживается**: Flexbox fallbacks

## Testing Strategy

### Visual Testing
1. **Theme Consistency**: Все элементы корректно меняют цвета
2. **Icon Logic**: Правильное отображение иконок солнца/луны
3. **Hover States**: Корректные hover эффекты в обеих темах
4. **Responsive Design**: Работа на всех размерах экранов

### Functional Testing
1. **Theme Switching**: Переключение работает корректно
2. **Persistence**: Тема сохраняется между сессиями
3. **Default State**: Темная тема по умолчанию
4. **Notifications**: Уведомления при переключении

### Browser Compatibility
1. **Modern Browsers**: Chrome, Firefox, Safari, Edge (последние версии)
2. **Mobile Browsers**: iOS Safari, Chrome Mobile
3. **Feature Detection**: Graceful degradation для старых браузеров

## Implementation Guidelines

### CSS Best Practices
1. **CSS-only Icon Logic**: Использование display: none/block без JavaScript
2. **Smooth Transitions**: Анимации для всех изменяемых свойств
3. **Consistent Naming**: Префикс `.account-page-wrapper` для изоляции стилей
4. **Mobile-First**: Адаптивные стили с mobile-first подходом

### JavaScript Best Practices
1. **Class-based Architecture**: Инкапсуляция логики в класс
2. **Event Delegation**: Эффективное управление событиями
3. **Error Handling**: Проверка существования элементов
4. **Performance**: Минимальные DOM манипуляции

### Integration Points
1. **Existing Styles**: Интеграция с текущими CSS переменными
2. **Layout Preservation**: Сохранение существующей структуры
3. **Component Isolation**: Стили не влияют на другие страницы
4. **Accessibility**: ARIA атрибуты и keyboard navigation

## Visual Design Specifications

### Color Palette

#### Light Theme
- **Primary**: #0ea5e9 (Sky Blue)
- **Background**: Linear gradient #f8fafc → #e2e8f0
- **Surface**: #ffffff, #f8fafc, #f1f5f9
- **Text**: #1e293b, #475569, #64748b
- **Borders**: rgba(148, 163, 184, 0.2-0.3)

#### Dark Theme (Current)
- **Primary**: #00bcd4 (Cyan)
- **Background**: Linear gradient #0a0f14 → #111922
- **Surface**: #0a0f14, #111922, #1a2332
- **Text**: #ffffff, #e2e8f0, #94a3b8
- **Borders**: rgba(100, 116, 139, 0.2-0.3)

### Typography
- **Font Family**: 'Inter', system fonts
- **Icon Font**: Font Awesome 5
- **Icon Sizes**: 16px for theme switcher icons

### Spacing & Layout
- **Switcher Size**: 40px × 40px (36px on mobile)
- **Icon Size**: 16px
- **Margin**: var(--spacing-lg) from status badge
- **Border Radius**: var(--radius-md)

### Animations
- **Transition Duration**: 300ms (var(--transition-normal))
- **Easing**: ease-in-out
- **Hover Transform**: translateY(-2px) scale(1.05)
- **Icon Transform**: scale(1.1) on hover