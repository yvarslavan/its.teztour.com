/**
 * Theme Manager для страницы "Мои задачи в Redmine"
 * Управляет переключением между светлой и темной темами
 */

class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'dark'; // Темная тема по умолчанию
        this.themeSwitcher = null;
        this.init();
    }

    /**
     * Инициализация менеджера тем
     */
    init() {
        console.log('🎨 Инициализация ThemeManager');

        // Применяем сохраненную тему или темную по умолчанию
        this.applyTheme(this.currentTheme);

        // Инициализируем переключатель темы
        this.initThemeSwitcher();

        // Обновляем иконки переключателя после инициализации
        this.updateSwitcherIcons(this.currentTheme);

        // Слушаем изменения системной темы
        this.watchSystemTheme();

        console.log(`🎨 Тема установлена: ${this.currentTheme}`);
    }

    /**
     * Получить сохраненную тему из localStorage
     */
    getStoredTheme() {
        try {
            return localStorage.getItem('preferred-theme');
        } catch (e) {
            console.warn('Не удалось получить сохраненную тему:', e);
            return null;
        }
    }

    /**
     * Получить системную тему
     */
    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    /**
     * Сохранить тему в localStorage
     */
    saveTheme(theme) {
        try {
            localStorage.setItem('preferred-theme', theme);
        } catch (e) {
            console.warn('Не удалось сохранить тему:', e);
        }
    }

    /**
     * Применить тему к документу
     */
    applyTheme(theme) {
        const body = document.body;
        const html = document.documentElement;

        // Удаляем предыдущие классы тем
        body.classList.remove('light-theme', 'dark-theme');
        html.classList.remove('light-theme', 'dark-theme');

        // Добавляем новый класс темы
        body.classList.add(`${theme}-theme`);
        html.classList.add(`${theme}-theme`);

        // Обновляем текущую тему
        this.currentTheme = theme;

        // Сохраняем в localStorage
        this.saveTheme(theme);

        // Обновляем иконки переключателя
        this.updateSwitcherIcons(theme);

        // Уведомляем другие компоненты об изменении темы
        this.notifyThemeChange(theme);

        console.log(`🎨 Тема применена: ${theme}`);
    }

    /**
     * Инициализировать переключатель темы
     */
    initThemeSwitcher() {
        this.themeSwitcher = document.getElementById('theme-switcher');

        if (!this.themeSwitcher) {
            console.warn('Переключатель темы не найден');
            return;
        }

        // Добавляем обработчик клика
        this.themeSwitcher.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Добавляем обработчик клавиатуры для доступности
        this.themeSwitcher.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleTheme();
            }
        });

        // Устанавливаем атрибуты доступности
        this.themeSwitcher.setAttribute('role', 'button');
        this.themeSwitcher.setAttribute('tabindex', '0');
        this.themeSwitcher.setAttribute('aria-label', 'Переключить тему');

        console.log('🎨 Переключатель темы инициализирован');
    }

    /**
     * Переключить тему
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);

        // Анимация переключения
        this.animateThemeSwitch();

        console.log(`🎨 Тема переключена: ${this.currentTheme} → ${newTheme}`);
    }

    /**
     * Обновить иконки переключателя
     */
    updateSwitcherIcons(theme) {
        if (!this.themeSwitcher) return;

        const lightIcon = this.themeSwitcher.querySelector('.theme-icon-light');
        const darkIcon = this.themeSwitcher.querySelector('.theme-icon-dark');

        if (lightIcon && darkIcon) {
            if (theme === 'light') {
                // В светлой теме показываем иконку луны (для переключения на темную)
                lightIcon.style.display = 'none';
                lightIcon.style.opacity = '0';
                lightIcon.style.visibility = 'hidden';
                darkIcon.style.display = 'block';
                darkIcon.style.opacity = '1';
                darkIcon.style.visibility = 'visible';
                darkIcon.style.color = '#ffffff';
                this.themeSwitcher.setAttribute('aria-label', 'Переключить на темную тему');
            } else {
                // В темной теме показываем иконку солнца (для переключения на светлую)
                lightIcon.style.display = 'block';
                lightIcon.style.opacity = '1';
                lightIcon.style.visibility = 'visible';
                lightIcon.style.color = '#fbbf24';
                darkIcon.style.display = 'none';
                darkIcon.style.opacity = '0';
                darkIcon.style.visibility = 'hidden';
                this.themeSwitcher.setAttribute('aria-label', 'Переключить на светлую тему');
            }
        }
    }

    /**
     * Анимация переключения темы
     */
    animateThemeSwitch() {
        if (!this.themeSwitcher) return;

        // Добавляем класс анимации
        this.themeSwitcher.classList.add('theme-switching');

        // Убираем класс через короткое время
        setTimeout(() => {
            this.themeSwitcher.classList.remove('theme-switching');
        }, 300);
    }

    /**
     * Следить за изменениями системной темы
     */
    watchSystemTheme() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

            mediaQuery.addEventListener('change', (e) => {
                // Применяем системную тему только если пользователь не выбрал свою
                const storedTheme = this.getStoredTheme();
                if (!storedTheme) {
                    const systemTheme = e.matches ? 'dark' : 'light';
                    this.applyTheme(systemTheme);
                    console.log(`🎨 Применена системная тема: ${systemTheme}`);
                }
            });
        }
    }

    /**
     * Уведомить другие компоненты об изменении темы
     */
    notifyThemeChange(theme) {
        // Создаем кастомное событие
        const event = new CustomEvent('themeChanged', {
            detail: { theme: theme }
        });

        // Отправляем событие
        document.dispatchEvent(event);
    }

    /**
     * Получить текущую тему
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Установить конкретную тему
     */
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.applyTheme(theme);
        } else {
            console.warn('Неподдерживаемая тема:', theme);
        }
    }

    /**
     * Сбросить тему к системной
     */
    resetToSystemTheme() {
        const systemTheme = this.getSystemTheme();
        this.applyTheme(systemTheme);
        localStorage.removeItem('preferred-theme');
        console.log(`🎨 Тема сброшена к системной: ${systemTheme}`);
    }
}

// Создаем глобальный экземпляр
window.themeManager = new ThemeManager();

// Экспортируем для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

// Добавляем CSS для анимации переключения
const style = document.createElement('style');
style.textContent = `
    .theme-switcher.theme-switching {
        transform: rotate(180deg) scale(1.1);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .theme-switcher:focus {
        outline: 2px solid var(--primary-500, #3b82f6);
        outline-offset: 2px;
    }

    /* Плавный переход между темами */
    * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
`;
document.head.appendChild(style);

console.log('🎨 ThemeManager загружен и готов к работе');
