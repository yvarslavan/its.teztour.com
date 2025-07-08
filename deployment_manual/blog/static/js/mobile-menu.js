/**
 * Modern Mobile Menu System
 * Полнофункциональное мобильное меню с анимациями и поддержкой подменю
 */

'use strict';

class MobileMenuManager {
    constructor() {
        this.state = {
            isOpen: false,
            isAnimating: false
        };

        this.init();
    }

    init() {
        try {
            // Основные элементы
            this.toggle = document.getElementById('mobile-menu-toggle');
            this.menu = document.getElementById('mobile-menu');
            this.overlay = document.getElementById('mobile-menu-overlay');
            this.closeBtn = document.getElementById('mobile-menu-close');

            if (!this.toggle || !this.menu || !this.overlay) {
                console.warn('MobileMenu: Не все элементы найдены');
                return;
            }

            this.bindEvents();
            this.handleResize();

            console.log('✅ MobileMenu: Инициализация завершена');
        } catch (error) {
            console.error('❌ MobileMenu: Ошибка инициализации:', error);
        }
    }

    bindEvents() {
        // Открытие меню
        this.toggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleMenu();
        });

        // Закрытие по кнопке
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeMenu());
        }

        // Закрытие по overlay
        this.overlay.addEventListener('click', () => this.closeMenu());

        // Закрытие по ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.state.isOpen) {
                this.closeMenu();
            }
        });

        // Обработка изменения размера окна
        window.addEventListener('resize', () => this.handleResize());

        // Обработка подменю
        const submenuToggles = document.querySelectorAll('.mobile-nav-link.submenu-toggle');
        submenuToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                const parentItem = toggle.closest('.mobile-nav-item');
                this.toggleSubmenu(parentItem);
            });
        });

        // Закрытие меню при клике на обычные ссылки
        const navLinks = document.querySelectorAll('.mobile-nav-link:not(.submenu-toggle), .mobile-submenu-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                setTimeout(() => this.closeMenu(), 100);
            });
        });
    }

    toggleMenu() {
        if (this.state.isAnimating) return;

        if (this.state.isOpen) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    openMenu() {
        if (this.state.isAnimating || this.state.isOpen) return;

        this.state.isAnimating = true;
        this.state.isOpen = true;

        // Анимация гамбургера в крестик
        this.toggle.classList.add('active');

        // Показываем overlay и меню
        this.overlay.classList.add('active');
        this.menu.classList.add('active');

        // Блокируем скролл body
        document.body.style.overflow = 'hidden';

        setTimeout(() => {
            this.state.isAnimating = false;
        }, 400);

        console.log('📱 MobileMenu: Меню открыто');
    }

    closeMenu() {
        if (this.state.isAnimating || !this.state.isOpen) return;

        this.state.isAnimating = true;
        this.state.isOpen = false;

        // Анимация крестика в гамбургер
        this.toggle.classList.remove('active');

        // Скрываем меню и overlay
        this.menu.classList.remove('active');
        this.overlay.classList.remove('active');

        // Закрываем все подменю
        this.closeAllSubmenus();

        // Восстанавливаем скролл body
        document.body.style.overflow = '';

        setTimeout(() => {
            this.state.isAnimating = false;
        }, 400);

        console.log('📱 MobileMenu: Меню закрыто');
    }

    toggleSubmenu(parentItem) {
        if (!parentItem) return;

        const isActive = parentItem.classList.contains('active');

        if (isActive) {
            parentItem.classList.remove('active');
        } else {
            // Закрываем другие подменю
            document.querySelectorAll('.mobile-nav-item.has-submenu.active').forEach(item => {
                if (item !== parentItem) {
                    item.classList.remove('active');
                }
            });

            parentItem.classList.add('active');
        }
    }

    closeAllSubmenus() {
        document.querySelectorAll('.mobile-nav-item.has-submenu.active').forEach(item => {
            item.classList.remove('active');
        });
    }

    handleResize() {
        const isMobile = window.innerWidth <= 968;

        if (!isMobile && this.state.isOpen) {
            this.closeMenu();
        }
    }

    // Публичные методы
    open() { this.openMenu(); }
    close() { this.closeMenu(); }
    toggle() { this.toggleMenu(); }

    get isMenuOpen() { return this.state.isOpen; }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.mobileMenuManager = new MobileMenuManager();

        // Глобальные функции для совместимости
        window.openMobileMenu = () => window.mobileMenuManager?.open();
        window.closeMobileMenu = () => window.mobileMenuManager?.close();
        window.toggleMobileMenu = () => window.mobileMenuManager?.toggle();

        console.log('🚀 MobileMenu: Система готова');
    } catch (error) {
        console.error('❌ MobileMenu: Критическая ошибка:', error);
    }
});

// Резервная инициализация
setTimeout(() => {
    if (!window.mobileMenuManager) {
        console.log('🔄 MobileMenu: Резервная инициализация...');
        window.mobileMenuManager = new MobileMenuManager();
    }
}, 100);
