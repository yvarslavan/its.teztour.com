/**
 * @file: theme-switcher.js
 * @description: Управление переключением между светлой и темной темой
 * @dependencies: localStorage API
 * @created: 2024-01-19
 */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = 'dark'; // По умолчанию темная тема
        this.init();
    }

    init() {
        // Загружаем сохраненную тему из localStorage
        this.loadSavedTheme();
        
        // Применяем тему к body
        this.applyTheme();
        
        // Инициализируем обработчики событий
        this.initEventListeners();
        
        console.log('🎨 ThemeSwitcher инициализирован, текущая тема:', this.currentTheme);
    }

    loadSavedTheme() {
        const savedTheme = localStorage.getItem('preferred-theme');
        if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
            this.currentTheme = savedTheme;
        }
    }

    applyTheme() {
        const body = document.body;
        
        if (this.currentTheme === 'light') {
            body.classList.add('light-theme');
        } else {
            body.classList.remove('light-theme');
        }
        
        // Обновляем иконки переключателя
        this.updateSwitcherIcons();
    }

    updateSwitcherIcons() {
        const lightIcons = document.querySelectorAll('.theme-icon-light');
        const darkIcons = document.querySelectorAll('.theme-icon-dark');
        
        if (this.currentTheme === 'light') {
            // Показываем иконку луны (для переключения на темную тему)
            lightIcons.forEach(icon => {
                icon.style.display = 'none';
                icon.style.opacity = '0';
                icon.style.visibility = 'hidden';
            });
            darkIcons.forEach(icon => {
                icon.style.display = 'block';
                icon.style.opacity = '1';
                icon.style.visibility = 'visible';
            });
        } else {
            // Показываем иконку солнца (для переключения на светлую тему)
            lightIcons.forEach(icon => {
                icon.style.display = 'block';
                icon.style.opacity = '1';
                icon.style.visibility = 'visible';
            });
            darkIcons.forEach(icon => {
                icon.style.display = 'none';
                icon.style.opacity = '0';
                icon.style.visibility = 'hidden';
            });
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        
        // Сохраняем выбор в localStorage
        localStorage.setItem('preferred-theme', this.currentTheme);
        
        // Применяем новую тему
        this.applyTheme();
        
        // Показываем уведомление
        this.showNotification();
        
        console.log('🎨 Тема переключена на:', this.currentTheme);
    }

    showNotification() {
        const themeName = this.currentTheme === 'light' ? 'светлую' : 'темную';
        
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-palette"></i>
                <span>Переключено на ${themeName} тему</span>
            </div>
        `;
        
        // Добавляем стили для уведомления
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--surface-card);
            color: var(--text-primary);
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: var(--shadow-2);
            border: 1px solid var(--border-light);
            z-index: 10000;
            opacity: 0;
            transform: translateX(100px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        `;
        
        // Добавляем на страницу
        document.body.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Удаляем через 3 секунды
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    initEventListeners() {
        // Обработчик для переключателя темы
        const themeSwitcher = document.getElementById('theme-switcher');
        if (themeSwitcher) {
            themeSwitcher.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleTheme();
            });
        }

        // Обработчик для клавиатурного доступа
        if (themeSwitcher) {
            themeSwitcher.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }

        // Слушаем изменения в localStorage (для синхронизации между вкладками)
        window.addEventListener('storage', (e) => {
            if (e.key === 'preferred-theme' && e.newValue) {
                this.currentTheme = e.newValue;
                this.applyTheme();
            }
        });
    }

    // Публичный метод для получения текущей темы
    getCurrentTheme() {
        return this.currentTheme;
    }

    // Публичный метод для установки темы программно
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.currentTheme = theme;
            localStorage.setItem('preferred-theme', theme);
            this.applyTheme();
        }
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    // Создаем глобальный экземпляр переключателя темы
    window.themeSwitcher = new ThemeSwitcher();
});

// Экспортируем класс для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeSwitcher;
}