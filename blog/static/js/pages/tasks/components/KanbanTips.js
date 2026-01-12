/**
 * KanbanTips.js - Компонент для отображения подсказок в канбан-доске
 * Показывает полезные советы и информацию о возможностях
 */

class KanbanTips {
    constructor() {
        this.tips = [
            {
                id: 'drag-drop',
                title: '🖱️ Перетаскивание задач',
                content: 'Зажмите мышью карточку задачи и перетащите её в другую колонку для изменения статуса',
                icon: 'fas fa-mouse-pointer',
                type: 'info'
            },
            {
                id: 'quick-actions',
                title: '⚡ Быстрые действия',
                content: 'Кликните на номер задачи (#123) для быстрого перехода к деталям',
                icon: 'fas fa-bolt',
                type: 'tip'
            },
            {
                id: 'priority-colors',
                title: '🎨 Цветовая индикация',
                content: 'Цветные бейджи показывают приоритет: красный - высокий, синий - нормальный, зеленый - низкий',
                icon: 'fas fa-palette',
                type: 'info'
            },
            {
                id: 'collapse-columns',
                title: '🔒 Сворачивание колонок',
                content: 'Кликните на заголовок колонки, чтобы свернуть/развернуть её содержимое',
                icon: 'fas fa-chevron-down',
                type: 'tip'
            },
            {
                id: 'mobile-friendly',
                title: '📱 Адаптивность',
                content: 'Доска автоматически адаптируется под размер экрана. На мобильных устройствах колонки располагаются вертикально',
                icon: 'fas fa-mobile-alt',
                type: 'info'
            }
        ];

        this.currentTipIndex = 0;
        this.isVisible = false;
        this.autoRotate = true;
        this.rotationInterval = null;

        // Автоматически очищаем дубликаты при создании экземпляра
        this.removeDuplicateBanners();
    }

    /**
     * Показывает баннер с подсказками
     */
    show() {
        // Проверяем, не существует ли уже баннер
        const existingBanner = document.getElementById('kanban-tips-banner');
        if (existingBanner) {
            console.log('[KanbanTips] ⚠️ Баннер уже существует, не создаем дубликат');
            return;
        }

        this.isVisible = true;
        this.currentTipIndex = 0;
        this.createTipsBanner();
        this.showCurrentTip();
        this.startAutoRotation();
    }

    /**
     * Создает баннер с подсказками
     */
    createTipsBanner() {
        const banner = document.createElement('div');
        banner.id = 'kanban-tips-banner';
        banner.className = 'kanban-tips-banner';
        banner.innerHTML = `
            <div class="tips-header">
                <div class="tips-icon">
                    <i class="fas fa-lightbulb"></i>
                </div>
                <div class="tips-content">
                    <h4 class="tips-title" id="tips-title">Полезные советы</h4>
                    <p class="tips-description" id="tips-description">Узнайте о возможностях канбан-доски</p>
                </div>
                <div class="tips-controls">
                    <button class="tips-nav-btn" id="tips-prev-btn" title="Предыдущий совет">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <div class="tips-indicators" id="tips-indicators"></div>
                    <button class="tips-nav-btn" id="tips-next-btn" title="Следующий совет">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                    <button class="tips-close-btn" id="tips-close-btn" title="Закрыть">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="tips-footer">
                <div class="tips-hide-option">
                    <input type="checkbox" id="hide-tips-forever" class="tips-checkbox">
                    <label for="hide-tips-forever" class="tips-checkbox-label">
                        <span class="checkbox-text">Не показывать больше</span>
                    </label>
                </div>
            </div>
            <div class="tips-progress">
                <div class="progress-bar">
                    <div class="progress-fill" id="tips-progress-fill"></div>
                </div>
            </div>
        `;

        // Добавляем баннер в канбан-доску
        const kanbanBoard = document.getElementById('kanban-board');
        if (kanbanBoard) {
            kanbanBoard.insertBefore(banner, kanbanBoard.firstChild);
        }

        this.setupEventListeners();
        this.createIndicators();
    }

    /**
     * Настраивает обработчики событий
     */
    setupEventListeners() {
        const prevBtn = document.getElementById('tips-prev-btn');
        const nextBtn = document.getElementById('tips-next-btn');
        const closeBtn = document.getElementById('tips-close-btn');
        const hideForeverCheckbox = document.getElementById('hide-tips-forever');

        prevBtn.addEventListener('click', () => this.previousTip());
        nextBtn.addEventListener('click', () => this.nextTip());
        closeBtn.addEventListener('click', () => this.handleClose());

        // Обработчик для чекбокса "Не показывать больше"
        hideForeverCheckbox?.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.handleHideForever();
            }
        });

        // Останавливаем автоповорот при взаимодействии
        const banner = document.getElementById('kanban-tips-banner');
        banner.addEventListener('mouseenter', () => this.pauseAutoRotation());
        banner.addEventListener('mouseleave', () => this.resumeAutoRotation());
    }

    /**
     * Создает индикаторы для навигации
     */
    createIndicators() {
        const indicatorsContainer = document.getElementById('tips-indicators');

        this.tips.forEach((tip, index) => {
            const indicator = document.createElement('button');
            indicator.className = 'tip-indicator';
            indicator.dataset.index = index;
            indicator.addEventListener('click', () => this.showTip(index));
            indicatorsContainer.appendChild(indicator);
        });
    }

    /**
     * Показывает текущую подсказку
     */
    showCurrentTip() {
        const tip = this.tips[this.currentTipIndex];

        document.getElementById('tips-title').textContent = tip.title;
        document.getElementById('tips-description').textContent = tip.content;

        // Обновляем индикаторы
        this.updateIndicators();

        // Обновляем прогресс
        const progress = ((this.currentTipIndex + 1) / this.tips.length) * 100;
        document.getElementById('tips-progress-fill').style.width = `${progress}%`;

        // Добавляем анимацию
        const banner = document.getElementById('kanban-tips-banner');
        banner.classList.add('tip-changed');
        setTimeout(() => {
            banner.classList.remove('tip-changed');
        }, 300);
    }

    /**
     * Обновляет индикаторы
     */
    updateIndicators() {
        const indicators = document.querySelectorAll('.tip-indicator');
        indicators.forEach((indicator, index) => {
            if (index === this.currentTipIndex) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    /**
     * Показывает конкретную подсказку
     */
    showTip(index) {
        if (index >= 0 && index < this.tips.length) {
            this.currentTipIndex = index;
            this.showCurrentTip();
        }
    }

    /**
     * Следующая подсказка
     */
    nextTip() {
        this.currentTipIndex = (this.currentTipIndex + 1) % this.tips.length;
        this.showCurrentTip();
    }

    /**
     * Предыдущая подсказка
     */
    previousTip() {
        this.currentTipIndex = this.currentTipIndex === 0 ? this.tips.length - 1 : this.currentTipIndex - 1;
        this.showCurrentTip();
    }

    /**
     * Запускает автоповорот подсказок
     */
    startAutoRotation() {
        if (!this.autoRotate) return;

        this.rotationInterval = setInterval(() => {
            this.nextTip();
        }, 5000); // Смена каждые 5 секунд
    }

    /**
     * Останавливает автоповорот
     */
    pauseAutoRotation() {
        if (this.rotationInterval) {
            clearInterval(this.rotationInterval);
            this.rotationInterval = null;
        }
    }

    /**
     * Возобновляет автоповорот
     */
    resumeAutoRotation() {
        if (this.autoRotate) {
            this.startAutoRotation();
        }
    }

    /**
     * Удаляет все дубликаты баннеров
     */
    removeDuplicateBanners() {
        const banners = document.querySelectorAll('#kanban-tips-banner');
        if (banners.length > 1) {
            console.log(`[KanbanTips] 🧹 Найдено ${banners.length} дубликатов баннеров, удаляем лишние`);

            // Оставляем только первый баннер, остальные удаляем
            for (let i = 1; i < banners.length; i++) {
                banners[i].remove();
            }
        }
    }

    /**
     * Скрывает баннер
     */
    hide() {
        // Удаляем все дубликаты перед скрытием
        this.removeDuplicateBanners();

        const banner = document.getElementById('kanban-tips-banner');
        if (banner) {
            banner.classList.add('fade-out');
            setTimeout(() => {
                if (banner.parentNode) {
                    banner.parentNode.removeChild(banner);
                }
            }, 300);
        }

        // Принудительно скрываем все всплывающие подсказки при закрытии панели онбординга
        this.forceHideAllTooltips();

        this.pauseAutoRotation();
        this.isVisible = false;
    }

    /**
     * Принудительно скрывает все всплывающие подсказки
     */
    forceHideAllTooltips() {
        // Используем глобальную функцию если она доступна
        if (typeof window.hideAllKanbanTooltips === 'function') {
            window.hideAllKanbanTooltips();
            console.log('[KanbanTips] 🎯 Принудительно скрыты все всплывающие подсказки при закрытии онбординга');
        } else {
            // Принудительно удаляем все подсказки
            const tooltips = document.querySelectorAll('.kanban-tooltip');
            tooltips.forEach(tooltip => {
                tooltip.style.opacity = '0';
                tooltip.style.transform = 'translateY(10px) scale(0.95)';
                tooltip.classList.remove('show');
                tooltip.remove();
            });

            // Удаляем контейнер
            const container = document.getElementById('kanban-tooltip-container');
            if (container) {
                container.remove();
            }

            console.log('[KanbanTips] 🎯 Принудительно скрыты все всплывающие подсказки (альтернативный способ)');
        }
    }

    /**
     * Показывает баннер если канбан активен и пользователь не отключил подсказки
     */
    showIfKanbanActive() {
        // Проверяем настройку пользователя из шаблона
        const showKanbanTips = window.showKanbanTips !== undefined ? window.showKanbanTips : true;

        if (!showKanbanTips) {
            console.log('[KanbanTips] 🚫 Баннер отключен пользователем, не показываем');
            return;
        }

        const kanbanBoard = document.getElementById('kanban-board');
        const isKanbanVisible = kanbanBoard && kanbanBoard.style.display !== 'none';

        // Проверяем, не существует ли уже баннер
        const existingBanner = document.getElementById('kanban-tips-banner');
        if (existingBanner) {
            console.log('[KanbanTips] ⚠️ Баннер уже существует, не показываем дубликат');
            return;
        }

        if (isKanbanVisible && !this.isVisible) {
            // Небольшая задержка для полной загрузки канбана
            setTimeout(() => {
                // Дополнительная проверка перед показом
                const banner = document.getElementById('kanban-tips-banner');
                if (!banner) {
                    this.show();
                } else {
                    console.log('[KanbanTips] ⚠️ Баннер появился во время задержки, не показываем');
                }
            }, 1000);
        }
    }

    /**
     * Обработчик закрытия баннера (обычное закрытие)
     */
    handleClose() {
        this.hide();
    }

    /**
     * Обработчик скрытия баннера навсегда
     */
    handleHideForever() {
        console.log('[KanbanTips] 💾 Сохраняем настройку скрытия баннера навсегда');

        // Отправляем запрос на сервер для сохранения настройки
        fetch('/api/user/kanban-tips-preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content')
            },
            body: JSON.stringify({
                show_kanban_tips: false
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('[KanbanTips] ✅ Настройка сохранена успешно');
                // Показываем уведомление пользователю
                if (typeof showNotification === 'function') {
                    showNotification('Настройка сохранена. Баннер больше не будет показываться.', 'success');
                }
            } else {
                console.error('[KanbanTips] ❌ Ошибка сохранения настройки:', data.error);
                // Снимаем галочку в случае ошибки
                const checkbox = document.getElementById('hide-tips-forever');
                if (checkbox) checkbox.checked = false;
            }
        })
        .catch(error => {
            console.error('[KanbanTips] ❌ Ошибка запроса:', error);
            // Снимаем галочку в случае ошибки
            const checkbox = document.getElementById('hide-tips-forever');
            if (checkbox) checkbox.checked = false;
        });

        // Скрываем баннер
        this.hide();

        // Отключаем все tooltips навсегда
        if (typeof window.disableAllKanbanTooltips === 'function') {
            window.disableAllKanbanTooltips();
        }
    }
}

// Экспортируем для использования в других модулях
window.KanbanTips = KanbanTips;

// Глобальная функция для очистки дубликатов баннеров
window.cleanupDuplicateBanners = function() {
    const banners = document.querySelectorAll('#kanban-tips-banner');
    if (banners.length > 1) {
        console.log(`[Global] 🧹 Найдено ${banners.length} дубликатов баннеров, удаляем лишние`);

        // Оставляем только первый баннер, остальные удаляем
        for (let i = 1; i < banners.length; i++) {
            banners[i].remove();
        }

        console.log('[Global] ✅ Дубликаты баннеров удалены');
    } else if (banners.length === 1) {
        console.log('[Global] ✅ Дубликатов баннеров не найдено');
    } else {
        console.log('[Global] ℹ️ Баннеры не найдены');
    }
};

// Глобальная функция для принудительного скрытия всех баннеров
window.hideAllKanbanBanners = function() {
    const banners = document.querySelectorAll('#kanban-tips-banner');
    banners.forEach(banner => {
        banner.classList.add('fade-out');
        setTimeout(() => {
            if (banner.parentNode) {
                banner.parentNode.removeChild(banner);
            }
        }, 300);
    });

    console.log(`[Global] 🧹 Скрыто ${banners.length} баннеров`);
};
