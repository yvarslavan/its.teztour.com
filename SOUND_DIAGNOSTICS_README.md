# Диагностика проблем со звуком уведомлений 🔊

## Быстрые команды для диагностики

Откройте консоль разработчика (F12) и выполните следующие команды:

### 1. Проверка общего состояния системы
```javascript
window.modernNotificationsWidget.getDiagnostics()
```

### 2. Тестирование звука
```javascript
window.modernNotificationsWidget.testSound()
```

### 3. Сброс "увиденных" уведомлений (для тестирования)
```javascript
window.modernNotificationsWidget.resetSeenNotifications()
```

### 4. Показать виджет (если скрыт)
```javascript
window.modernNotificationsWidget.showWidget()
```

## Частые проблемы и решения

### 🔇 Звук отключен пользователем
**Проблема:** `soundDisabled: true` в диагностике
**Решение:**
```javascript
localStorage.removeItem('notificationSoundDisabled')
```

### 🚫 Браузер блокирует автовоспроизведение
**Проблема:** `audioBlocked: true` в диагностике
**Решение:**
1. Кликните в любом месте страницы
2. Или выполните: `sessionStorage.removeItem('audioBlocked')`

### 📱 Виджет закрыт
**Проблема:** `widgetClosed: true` в диагностике
**Решение:**
```javascript
localStorage.setItem('notificationsWidgetClosed', 'false')
window.modernNotificationsWidget.showWidget()
```

### 🔄 Уведомления считаются "уже просмотренными"
**Проблема:** Много ID в `seenNotifications`
**Решение:** Используйте `resetSeenNotifications()`

## Логи для анализа

В консоли ищите сообщения с префиксами:
- `[ModernWidget]` - виджет уведомлений
- `[Polling]` - система опроса уведомлений
- `[Global]` - глобальные функции звука

### Полезные логи:
- `🔊 Воспроизводим звук` - звук должен играть
- `🔇 Звук заблокирован браузером` - нужно кликнуть на странице
- `✅ Звук воспроизведен успешно` - всё работает
- `⚠️ Ошибка воспроизведения` - проблема с аудио файлом

## Продвинутая диагностика

### Проверка существования звукового файла
```javascript
fetch('/static/sounds/notification.mp3')
  .then(r => console.log('Звуковой файл:', r.ok ? 'найден' : 'отсутствует'))
  .catch(e => console.log('Ошибка загрузки файла:', e))
```

### Принудительное воспроизведение
```javascript
const audio = new Audio('/static/sounds/notification.mp3');
audio.volume = 0.5;
audio.play().then(() => console.log('✅ Успех')).catch(e => console.log('❌ Ошибка:', e.name))
```

## Проблемы конкретных браузеров

### Chrome/Edge
- Требует взаимодействие пользователя перед первым звуком
- Может блокировать на неактивных вкладках

### Firefox
- Более лояльная политика автовоспроизведения
- Проверьте настройки браузера `about:preferences#privacy`

### Safari
- Самые строгие ограничения
- Возможны проблемы с громкостью

## Если ничего не помогает

1. Перезагрузите страницу
2. Очистите localStorage: `localStorage.clear()`
3. Проверьте настройки браузера для данного сайта
4. Попробуйте в режиме инкогнито
