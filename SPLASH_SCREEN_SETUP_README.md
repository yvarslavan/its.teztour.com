# Настройка Splash Screen 🎨

## Как работает система

Splash screen теперь показывается **только** на страницах входа (`/login`) и регистрации (`/register`), а не на всех страницах сайта.

## Логика отображения

### В layout.html:
```jinja2
{% if request.endpoint == 'users.login' or request.endpoint == 'users.register' %}
  <!-- Splash screen отображается -->
  <div class="modern-splash-screen">
    <!-- содержимое -->
  </div>
{% endif %}
```

### Атрибуты body:
- `data-show-splash="true"` - на страницах login/register
- `data-show-splash="false"` - на всех остальных страницах

## Персонализация сообщений

Splash screen показывает разные сообщения в зависимости от страницы:

- **Login**: "добро пожаловать обратно" / "Подготавливаем вход в систему..."
- **Register**: "добро пожаловать в систему" / "Подготавливаем регистрацию..."

## Тестирование

### 1. Проверка настроек текущей страницы
```javascript
splashScreenUtils.checkPageSettings()
```

### 2. Принудительный показ (для тестирования)
```javascript
splashScreenUtils.forceShow()
```

### 3. Принудительное скрытие
```javascript
splashScreenUtils.forceHide()
```

### 4. Сброс настроек localStorage
```javascript
splashScreenUtils.resetSettings()
```

## Ожидаемое поведение

### ✅ Splash screen ДОЛЖЕН показываться:
- При переходе на `/login`
- При переходе на `/register`
- При прямом переходе по URL на эти страницы

### ❌ Splash screen НЕ ДОЛЖЕН показываться:
- На главной странице
- В личном кабинете
- При переходах по меню
- На любых других страницах кроме login/register

## Отладка проблем

### Проблема: Splash screen не показывается на login/register
1. Проверьте консоль на ошибки
2. Выполните `splashScreenUtils.checkPageSettings()`
3. Убедитесь что `showSplash: "true"`

### Проблема: Splash screen показывается везде
1. Проверьте логику в `layout.html` (условие `{% if request.endpoint == ... %}`)
2. Убедитесь что на других страницах `data-show-splash="false"`

### Проблема: Splash screen не исчезает
1. Выполните `splashScreenUtils.forceHide()`
2. Проверьте настройки времени показа
3. Перезагрузите страницу

## Настройки времени

- **Время показа**: 3.5 секунды (3500ms)
- **Минимальное время**: 2 секунды
- **Максимальное время**: 6 секунд

## Файлы для редактирования

- **HTML**: `blog/templates/layout.html` - условия отображения
- **JavaScript**: `blog/static/js/modern_splash_screen.js` - логика работы
- **CSS**: `blog/static/css/modern_splash_screen.css` - стили
