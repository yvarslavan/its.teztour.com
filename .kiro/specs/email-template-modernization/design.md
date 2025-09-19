# Design Document

## Overview

Данный документ описывает дизайн модернизированного email шаблона для системы уведомлений TEZ TOUR. Новый дизайн использует современные веб-технологии и визуальные элементы для создания профессионального и привлекательного внешнего вида.

## Architecture

### Общая структура
- **Контейнерная архитектура**: Использование вложенных таблиц для максимальной совместимости с email клиентами
- **Модульный подход**: Разделение на логические блоки (шапка, контент, футер)
- **Адаптивность**: Фиксированная ширина 700px для оптимального отображения

### Технические решения
- **HTML Tables**: Использование таблиц вместо div для совместимости с Outlook
- **Inline CSS**: Все стили встроены для избежания проблем с внешними стилями
- **Градиенты**: CSS градиенты с fallback цветами для старых клиентов

## Components and Interfaces

### 1. Header Component (Шапка)
```html
<tr>
    <td style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);">
        <!-- Логотип в стеклянном контейнере -->
        <!-- Контактная информация -->
    </td>
</tr>
```

**Особенности:**
- Градиентный фон с темно-синими оттенками
- Логотип в полупрозрачном "стеклянном" контейнере
- Контактная информация справа с белым текстом

### 2. Accent Line Component (Акцентная полоса)
```html
<tr>
    <td>
        <div style="background: linear-gradient(90deg, #e94560 0%, #ff6b6b 50%, #e94560 100%);"></div>
    </td>
</tr>
```

**Особенности:**
- Тонкая красная полоса для визуального разделения
- Градиент от темно-красного к светло-красному

### 3. Content Container (Основной контент)
```html
<tr>
    <td style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border-left: 4px solid #3498db;">
        <!-- Информационные блоки -->
    </td>
</tr>
```

**Особенности:**
- Светлый градиентный фон
- Синяя левая граница для акцента
- Современная типографика

### 4. Information Blocks (Информационные блоки)

#### Блок регистрации заявки
```html
<div style="background: rgba(52, 152, 219, 0.1); border-left: 3px solid #3498db;">
    <!-- Информация о номере заявки -->
</div>
```

#### Предупреждающий блок
```html
<div style="background: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107;">
    <!-- Автоматическое сообщение -->
</div>
```

#### Информационный блок
```html
<div style="background: rgba(40, 167, 69, 0.1); border-left: 4px solid #28a745;">
    <!-- Ссылка на портал -->
</div>
```

### 5. Footer Component (Футер)
```html
<tr>
    <td style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);">
        <!-- Логотип и информация о компании -->
    </td>
</tr>
```

## Data Models

### Email Template Variables
```javascript
{
    issueID: "string",      // Номер заявки
    subject: "string",      // Тема заявки
    status: "string",       // Статус заявки
    created_on: "string",   // Дата создания
    description: "string"   // Описание заявки
}
```

### Color Scheme
```css
:root {
    --primary-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    --content-gradient: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    --accent-gradient: linear-gradient(90deg, #e94560 0%, #ff6b6b 50%, #e94560 100%);
    --info-blue: rgba(52, 152, 219, 0.1);
    --warning-yellow: rgba(255, 193, 7, 0.1);
    --success-green: rgba(40, 167, 69, 0.1);
}
```

## Error Handling

### Email Client Compatibility
- **Outlook**: Использование таблиц и inline стилей
- **Gmail**: Поддержка современных CSS свойств
- **Apple Mail**: Полная поддержка градиентов и эффектов
- **Fallback**: Базовые цвета для клиентов без поддержки градиентов

### Responsive Considerations
- Фиксированная ширина 700px для настольных клиентов
- Адаптивные отступы для мобильных устройств
- Масштабируемые изображения

## Testing Strategy

### Cross-Client Testing
1. **Desktop Clients**: Outlook 2016+, Apple Mail, Thunderbird
2. **Web Clients**: Gmail, Outlook.com, Yahoo Mail
3. **Mobile Clients**: iOS Mail, Android Gmail

### Validation Tests
1. **HTML Validation**: Проверка корректности HTML структуры
2. **CSS Validation**: Проверка поддержки CSS свойств
3. **Variable Substitution**: Тестирование подстановки переменных
4. **Link Functionality**: Проверка работоспособности всех ссылок

### Performance Considerations
- Оптимизация размера изображений
- Минимизация CSS кода
- Использование web-safe шрифтов с fallback

## Implementation Notes

### Migration Strategy
1. Создание нового шаблона с сохранением всех переменных
2. Тестирование в изолированной среде
3. Постепенное внедрение с мониторингом
4. Откат к старому шаблону в случае проблем

### Maintenance
- Документирование всех изменений
- Версионирование шаблонов
- Регулярное тестирование в новых версиях email клиентов