/**
 * KanbanOnboarding.js - Компонент для онбординга канбан-доски
 * Показывает пошаговое руководство по использованию канбана
 */

class KanbanOnboarding {
    constructor() {
        this.isVisible = false;
        this.currentStep = 0;
        this.steps = [
            {
                title: 'Добро пожаловать в канбан-доску!',
                description: 'Здесь вы можете управлять задачами в удобном визуальном формате',
                icon: 'fas fa-columns'
            },
            {
                title: 'Перетаскивание задач',
                description: 'Зажмите карточку задачи и перетащите её в другую колонку для изменения статуса',
                icon: 'fas fa-mouse-pointer'
            },
            {
                title: 'Быстрые действия',
                description: 'Кликните на номер задачи (#123) для быстрого перехода к деталям',
                icon: 'fas fa-bolt'
            },
            {
                title: 'Цветовая индикация',
                description: 'Цветные бейджи показывают приоритет: красный - высокий, синий - нормальный, зеленый - низкий',
                icon: 'fas fa-palette'
            }
        ];
    }

    /**
     * Показывает онбординг если пользователь его еще не видел
     */
    showIfNeeded() {
        // Проверяем, видел ли пользователь онбординг
        const hasSeenOnboarding = localStorage.getItem('kanbanOnboardingSeen');

        if (!hasSeenOnboarding) {
            this.show();
        }
    }

    /**
     * Показывает онбординг
     */
    show() {
        this.isVisible = true;
        this.currentStep = 0;
        this.createOnboardingModal();
        this.showStep(0);
    }

    /**
     * Создает модальное окно онбординга
     */
    createOnboardingModal() {
        const modal = document.createElement('div');
        modal.className = 'kanban-onboarding-modal';
        modal.innerHTML = `
            <div class="onboarding-overlay"></div>
            <div class="onboarding-container">
                <div class="onboarding-header">
                    <div class="onboarding-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="onboarding-progress-fill"></div>
                        </div>
                        <span class="progress-text" id="onboarding-progress-text">1/${this.steps.length}</span>
                    </div>
                    <button class="onboarding-close-btn" id="onboarding-close-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="onboarding-content">
                    <div class="onboarding-icon" id="onboarding-icon">
                        <i class="fas fa-columns"></i>
                    </div>
                    <h3 class="onboarding-title" id="onboarding-title">Добро пожаловать в канбан-доску!</h3>
                    <p class="onboarding-description" id="onboarding-description">Здесь вы можете управлять задачами в удобном визуальном формате</p>
                </div>
                <div class="onboarding-actions">
                    <div class="onboarding-nav">
                        <button class="onboarding-btn secondary" id="onboarding-prev-btn" disabled>
                            <i class="fas fa-chevron-left"></i>
                            <span>Назад</span>
                        </button>
                        <button class="onboarding-btn primary" id="onboarding-next-btn">
                            <span>Далее</span>
                            <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.setupEventListeners();
    }

    /**
     * Настраивает обработчики событий
     */
    setupEventListeners() {
        const closeBtn = document.getElementById('onboarding-close-btn');
        const prevBtn = document.getElementById('onboarding-prev-btn');
        const nextBtn = document.getElementById('onboarding-next-btn');
        const overlay = document.querySelector('.onboarding-overlay');

        closeBtn.addEventListener('click', () => this.close());
        overlay.addEventListener('click', () => this.close());
        prevBtn.addEventListener('click', () => this.previousStep());
        nextBtn.addEventListener('click', () => this.nextStep());

        // Закрытие по ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.close();
            }
        });
    }

    /**
     * Показывает конкретный шаг
     */
    showStep(stepIndex) {
        const step = this.steps[stepIndex];

        document.getElementById('onboarding-icon').innerHTML = `<i class="${step.icon}"></i>`;
        document.getElementById('onboarding-title').textContent = step.title;
        document.getElementById('onboarding-description').textContent = step.description;

        // Обновляем прогресс
        const progress = ((stepIndex + 1) / this.steps.length) * 100;
        document.getElementById('onboarding-progress-fill').style.width = `${progress}%`;
        document.getElementById('onboarding-progress-text').textContent = `${stepIndex + 1}/${this.steps.length}`;

        // Обновляем кнопки
        const prevBtn = document.getElementById('onboarding-prev-btn');
        const nextBtn = document.getElementById('onboarding-next-btn');

        prevBtn.disabled = stepIndex === 0;
        nextBtn.innerHTML = stepIndex === this.steps.length - 1
            ? '<span>Завершить</span><i class="fas fa-check"></i>'
            : '<span>Далее</span><i class="fas fa-chevron-right"></i>';
    }

    /**
     * Следующий шаг
     */
    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.showStep(this.currentStep);
        } else {
            this.complete();
        }
    }

    /**
     * Предыдущий шаг
     */
    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    /**
     * Завершает онбординг
     */
    complete() {
        localStorage.setItem('kanbanOnboardingSeen', 'true');
        this.close();
    }

    /**
     * Закрывает онбординг
     */
    close() {
        this.isVisible = false;

        // Принудительно скрываем все всплывающие подсказки при закрытии онбординга
        this.forceHideAllTooltips();

        const modal = document.querySelector('.kanban-onboarding-modal');
        if (modal) {
            modal.querySelector('.onboarding-container').classList.add('fade-out');
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
            }, 300);
        }

        console.log('[KanbanOnboarding] 🎯 Онбординг закрыт, все подсказки принудительно скрыты');
    }

    /**
     * Принудительно скрывает все всплывающие подсказки
     */
    forceHideAllTooltips() {
        // Используем глобальную функцию если она доступна
        if (typeof window.hideAllKanbanTooltips === 'function') {
            window.hideAllKanbanTooltips();
            console.log('[KanbanOnboarding] 🎯 Принудительно скрыты все всплывающие подсказки при закрытии онбординга');
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

            console.log('[KanbanOnboarding] 🎯 Принудительно скрыты все всплывающие подсказки (альтернативный способ)');
        }
    }
}

// Экспортируем для использования в других модулях
window.KanbanOnboarding = KanbanOnboarding;

// Глобальная функция для сброса состояния онбординга (для тестирования)
window.resetKanbanOnboarding = function() {
    localStorage.removeItem('kanbanOnboardingSeen');
    console.log('[Global] 🔄 Состояние онбординга сброшено');
};

// Глобальная функция для принудительного показа онбординга
window.showKanbanOnboarding = function() {
    if (typeof window.KanbanOnboarding !== 'undefined') {
        const onboarding = new window.KanbanOnboarding();
        onboarding.show();
    }
};
