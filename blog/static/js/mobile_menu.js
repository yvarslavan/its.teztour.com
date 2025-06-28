/**
 * Modern Mobile Menu System
 * Полнофункциональное мобильное меню с анимациями и поддержкой подменю
 * Кроссбраузерная поддержка: Chrome, Firefox, Safari, Edge
 *
 * @version 1.0.0
 * @author TEZ Navigator Team
 */

'use strict';

class MobileMenuManager {
    constructor() {
        this.config = {
            animationDuration: 400,
            debounceDelay: 250,
            breakpoint: 968,
            enableAccessibility: true,
            enableAnalytics: false
        };

        this.state = {
            isOpen: false,
            isAnimating: false,
            isMobile: false,
            activeSubmenu: null
        };

        this.elements = {};
        this.eventListeners = [];

        this.init();
    }

    /**
     * Инициализация мобильного меню
     */
    init() {
        try {
            this.cacheElements();
            this.checkRequiredElements();
            this.bindEvents();
            this.setupAccessibility();
            this.handleInitialResize();

            this.log('✅ MobileMenu: Инициализация завершена успешно');
        } catch (error) {
            this.error('❌ MobileMenu: Ошибка инициализации:', error);
        }
    }

    /**
     * Кеширование DOM элементов
     */
    cacheElements() {
        this.elements = {
            toggle: document.getElementById('mobile-menu-toggle'),
            menu: document.getElementById('mobile-menu'),
            overlay: document.getElementById('mobile-menu-overlay'),
            closeBtn: document.getElementById('mobile-menu-close'),
            submenuToggles: document.querySelectorAll('.mobile-nav-link.submenu-toggle'),
            navLinks: document.querySelectorAll('.mobile-nav-link:not(.submenu-toggle), .mobile-submenu-link'),
            body: document.body,
            html: document.documentElement
        };
    }

    /**
     * Проверка наличия обязательных элементов
     */
    checkRequiredElements() {
        const required = ['toggle', 'menu', 'overlay'];
        const missing = required.filter(key => !this.elements[key]);

        if (missing.length > 0) {
            throw new Error(`Отсутствуют обязательные элементы: ${missing.join(', ')}`);
        }
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Основные события меню
        this.addEventListener(this.elements.toggle, 'click', this.handleToggleClick.bind(this));

        if (this.elements.closeBtn) {
            this.addEventListener(this.elements.closeBtn, 'click', this.closeMenu.bind(this));
        }

        this.addEventListener(this.elements.overlay, 'click', this.closeMenu.bind(this));

        // События клавиатуры
        this.addEventListener(document, 'keydown', this.handleKeyDown.bind(this));

        // События изменения размера окна
        this.addEventListener(window, 'resize', this.debounce(this.handleResize.bind(this), this.config.debounceDelay));

        // События подменю
        this.bindSubmenuEvents();

        // События навигационных ссылок
        this.bindNavigationEvents();

        // Предотвращение скролла при открытом меню
        this.addEventListener(this.elements.menu, 'touchmove', this.handleTouchMove.bind(this));

        // События фокуса для accessibility
        if (this.config.enableAccessibility) {
            this.bindAccessibilityEvents();
        }
    }

    /**
     * Привязка событий подменю
     */
    bindSubmenuEvents() {
        this.elements.submenuToggles.forEach(toggle => {
            this.addEventListener(toggle, 'click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                const parentItem = toggle.closest('.mobile-nav-item');
                this.toggleSubmenu(parentItem);
            });
        });
    }

    /**
     * Привязка событий навигационных ссылок
     */
    bindNavigationEvents() {
        this.elements.navLinks.forEach(link => {
            this.addEventListener(link, 'click', () => {
                // Небольшая задержка для плавного перехода
                setTimeout(() => this.closeMenu(), 100);
            });
        });
    }

    /**
     * Привязка событий для accessibility
     */
    bindAccessibilityEvents() {
        // Обработка tab навигации
        this.addEventListener(this.elements.menu, 'keydown', this.handleMenuKeyDown.bind(this));

        // Фокус ловушка
        const focusableElements = this.elements.menu.querySelectorAll(
            'a, button, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length > 0) {
            this.elements.firstFocusable = focusableElements[0];
            this.elements.lastFocusable = focusableElements[focusableElements.length - 1];
        }
    }

    /**
     * Обработчик клика по toggle кнопке
     */
    handleToggleClick(e) {
        e.preventDefault();
        e.stopPropagation();
        this.toggleMenu();
    }

    /**
     * Обработчик нажатий клавиш
     */
    handleKeyDown(e) {
        if (e.key === 'Escape' && this.state.isOpen) {
            this.closeMenu();
        }
    }

    /**
     * Обработчик нажатий клавиш в меню (для accessibility)
     */
    handleMenuKeyDown(e) {
        if (!this.state.isOpen) return;

        switch (e.key) {
            case 'Tab':
                this.handleTabNavigation(e);
                break;
            case 'Escape':
                this.closeMenu();
                this.elements.toggle.focus();
                break;
        }
    }

    /**
     * Обработка Tab навигации для фокус ловушки
     */
    handleTabNavigation(e) {
        if (!this.elements.firstFocusable || !this.elements.lastFocusable) return;

        if (e.shiftKey) {
            // Shift + Tab
            if (document.activeElement === this.elements.firstFocusable) {
                e.preventDefault();
                this.elements.lastFocusable.focus();
            }
        } else {
            // Tab
            if (document.activeElement === this.elements.lastFocusable) {
                e.preventDefault();
                this.elements.firstFocusable.focus();
            }
        }
    }

    /**
     * Обработчик изменения размера окна
     */
    handleResize() {
        const wasMobile = this.state.isMobile;
        this.state.isMobile = window.innerWidth <= this.config.breakpoint;

        // Закрываем меню при переходе на десктоп
        if (wasMobile && !this.state.isMobile && this.state.isOpen) {
            this.closeMenu();
        }

        this.log(`📱 Режим: ${this.state.isMobile ? 'мобильный' : 'десктоп'}`);
    }

    /**
     * Первоначальная обработка размера
     */
    handleInitialResize() {
        this.handleResize();
    }

    /**
     * Обработчик touch события для предотвращения скролла body
     */
    handleTouchMove(e) {
        e.stopPropagation();
    }

    /**
     * Переключение состояния меню
     */
    toggleMenu() {
        if (this.state.isAnimating) {
            this.log('⏳ Анимация в процессе, игнорируем toggle');
            return;
        }

        if (this.state.isOpen) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    /**
     * Открытие меню
     */
    openMenu() {
        if (this.state.isAnimating || this.state.isOpen) {
            return;
        }

        this.state.isAnimating = true;
        this.state.isOpen = true;

        // Добавляем классы для анимации
        this.elements.toggle.classList.add('active');
        this.elements.overlay.classList.add('active');
        this.elements.menu.classList.add('active');

        // Блокируем скролл body
        this.lockBodyScroll();

        // Устанавливаем aria атрибуты
        this.setupMenuAccessibility(true);

        // Фокус на меню для accessibility
        setTimeout(() => {
            if (this.config.enableAccessibility && this.elements.firstFocusable) {
                this.elements.firstFocusable.focus();
            }
            this.state.isAnimating = false;
        }, this.config.animationDuration);

        this.log('📱 MobileMenu: Меню открыто');
        this.trackEvent('menu_opened');
    }

    /**
     * Закрытие меню
     */
    closeMenu() {
        if (this.state.isAnimating || !this.state.isOpen) {
            return;
        }

        this.state.isAnimating = true;
        this.state.isOpen = false;

        // Убираем классы для анимации
        this.elements.toggle.classList.remove('active');
        this.elements.menu.classList.remove('active');
        this.elements.overlay.classList.remove('active');

        // Закрываем все подменю
        this.closeAllSubmenus();

        // Разблокируем скролл body
        this.unlockBodyScroll();

        // Устанавливаем aria атрибуты
        this.setupMenuAccessibility(false);

        setTimeout(() => {
            this.state.isAnimating = false;
        }, this.config.animationDuration);

        this.log('📱 MobileMenu: Меню закрыто');
        this.trackEvent('menu_closed');
    }

    /**
     * Переключение подменю
     */
    toggleSubmenu(parentItem) {
        if (!parentItem) return;

        const isActive = parentItem.classList.contains('active');
        const submenuId = parentItem.dataset.submenu || 'unknown';

        if (isActive) {
            parentItem.classList.remove('active');
            this.state.activeSubmenu = null;
            this.log(`📂 Подменю ${submenuId} закрыто`);
        } else {
            // Закрываем другие подменю
            this.closeAllSubmenus();

            parentItem.classList.add('active');
            this.state.activeSubmenu = submenuId;
            this.log(`📂 Подменю ${submenuId} открыто`);
        }

        this.trackEvent('submenu_toggled', { submenu: submenuId, action: isActive ? 'closed' : 'opened' });
    }

    /**
     * Закрытие всех подменю
     */
    closeAllSubmenus() {
        document.querySelectorAll('.mobile-nav-item.has-submenu.active').forEach(item => {
            item.classList.remove('active');
        });
        this.state.activeSubmenu = null;
    }

    /**
     * Блокировка скролла body
     */
    lockBodyScroll() {
        // Сохраняем текущую позицию скролла
        this.scrollPosition = window.pageYOffset;

        this.elements.body.style.overflow = 'hidden';
        this.elements.body.style.position = 'fixed';
        this.elements.body.style.top = `-${this.scrollPosition}px`;
        this.elements.body.style.width = '100%';

        this.elements.html.style.overflow = 'hidden';
    }

    /**
     * Разблокировка скролла body
     */
    unlockBodyScroll() {
        this.elements.body.style.overflow = '';
        this.elements.body.style.position = '';
        this.elements.body.style.top = '';
        this.elements.body.style.width = '';

        this.elements.html.style.overflow = '';

        // Восстанавливаем позицию скролла
        if (this.scrollPosition !== undefined) {
            window.scrollTo(0, this.scrollPosition);
        }
    }

    /**
     * Настройка accessibility атрибутов
     */
    setupAccessibility() {
        if (!this.config.enableAccessibility) return;

        // Устанавливаем aria атрибуты
        this.elements.toggle.setAttribute('aria-expanded', 'false');
        this.elements.toggle.setAttribute('aria-controls', 'mobile-menu');
        this.elements.toggle.setAttribute('aria-label', 'Открыть мобильное меню');

        this.elements.menu.setAttribute('role', 'navigation');
        this.elements.menu.setAttribute('aria-label', 'Мобильное меню');
        this.elements.menu.setAttribute('aria-hidden', 'true');

        if (this.elements.closeBtn) {
            this.elements.closeBtn.setAttribute('aria-label', 'Закрыть мобильное меню');
        }
    }

    /**
     * Обновление accessibility атрибутов при открытии/закрытии
     */
    setupMenuAccessibility(isOpen) {
        if (!this.config.enableAccessibility) return;

        this.elements.toggle.setAttribute('aria-expanded', isOpen.toString());
        this.elements.toggle.setAttribute('aria-label', isOpen ? 'Закрыть мобильное меню' : 'Открыть мобильное меню');
        this.elements.menu.setAttribute('aria-hidden', (!isOpen).toString());
    }

    /**
     * Добавление event listener с автоматическим отслеживанием
     */
    addEventListener(element, event, handler, options = {}) {
        if (!element) return;

        element.addEventListener(event, handler, options);
        this.eventListeners.push({ element, event, handler, options });
    }

    /**
     * Debounce функция для оптимизации производительности
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Логирование событий
     */
    log(message, ...args) {
        if (console && console.log) {
            console.log(message, ...args);
        }
    }

    /**
     * Логирование ошибок
     */
    error(message, ...args) {
        if (console && console.error) {
            console.error(message, ...args);
        }
    }

    /**
     * Отслеживание событий для аналитики
     */
    trackEvent(eventName, data = {}) {
        if (!this.config.enableAnalytics) return;

        // Интеграция с Google Analytics, если доступна
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                event_category: 'mobile_menu',
                ...data
            });
        }

        this.log(`📊 Analytics: ${eventName}`, data);
    }

    /**
     * Публичные методы для внешнего управления
     */
    open() {
        this.openMenu();
    }

    close() {
        this.closeMenu();
    }

    toggle() {
        this.toggleMenu();
    }

    /**
     * Геттеры для состояния
     */
    get isMenuOpen() {
        return this.state.isOpen;
    }

    get isAnimating() {
        return this.state.isAnimating;
    }

    get isMobile() {
        return this.state.isMobile;
    }

    /**
     * Уничтожение инстанса и очистка ресурсов
     */
    destroy() {
        // Удаляем все event listeners
        this.eventListeners.forEach(({ element, event, handler, options }) => {
            element.removeEventListener(event, handler, options);
        });

        // Закрываем меню, если открыто
        if (this.state.isOpen) {
            this.closeMenu();
        }

        // Очищаем ссылки
        this.elements = {};
        this.eventListeners = [];

        this.log('🗑️ MobileMenu: Инстанс уничтожен');
    }
}

/**
 * Глобальные функции для совместимости и удобства использования
 */
let mobileMenuInstance = null;

function initializeMobileMenu() {
    try {
        if (mobileMenuInstance) {
            mobileMenuInstance.destroy();
        }

        mobileMenuInstance = new MobileMenuManager();

        // Глобальные функции
        window.mobileMenuManager = mobileMenuInstance;
        window.openMobileMenu = () => mobileMenuInstance?.open();
        window.closeMobileMenu = () => mobileMenuInstance?.close();
        window.toggleMobileMenu = () => mobileMenuInstance?.toggle();

        console.log('🚀 MobileMenu: Система готова к использованию');
    } catch (error) {
        console.error('❌ MobileMenu: Критическая ошибка:', error);
    }
}

/**
 * Инициализация при загрузке DOM
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeMobileMenu);
} else {
    // DOM уже загружен
    initializeMobileMenu();
}

/**
 * Резервная инициализация для повышенной надежности
 */
setTimeout(() => {
    if (!window.mobileMenuManager) {
        console.log('🔄 MobileMenu: Резервная инициализация...');
        initializeMobileMenu();
    }
}, 100);

/**
 * Экспорт для модульных систем
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileMenuManager;
}

if (typeof window !== 'undefined') {
    window.MobileMenuManager = MobileMenuManager;
}
