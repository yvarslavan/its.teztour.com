/**
 * tasks_counter_manager.js - v1.0
 * Менеджер для управления индикатором количества задач
 */

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('[TasksCounter] 🔧 Инициализация менеджера индикатора задач');

    // Создаем глобальный объект для управления индикатором
    window.TasksCounterManager = {
        // Элементы DOM
        indicator: null,
        counterValue: null,
        counterLabel: null,
        loadingElement: null,

        // Состояние
        isVisible: false,
        isLoading: false,
        currentCount: 0,

        // Инициализация
        initialize: function() {
            // Находим элементы DOM
            this.indicator = document.getElementById('tasksCounterIndicator');

            if (!this.indicator) {
                console.error('[TasksCounter] ❌ Основной элемент индикатора не найден (#tasksCounterIndicator)');
                return false;
            }

            this.counterValue = this.indicator.querySelector('.counter-value');
            this.counterLabel = this.indicator.querySelector('.counter-label');
            this.loadingElement = this.indicator.querySelector('.counter-loading');

            if (!this.counterValue || !this.counterLabel || !this.loadingElement) {
                console.error('[TasksCounter] ❌ Не удалось инициализировать - элементы не найдены');
                return false;
            }

            console.log('[TasksCounter] ✅ Индикатор успешно инициализирован');
            return true;
        },

        // Показать индикатор
        show: function(count, suffix = 'задач найдено') {
            if (!this.indicator) {
                if (!this.initialize()) return;
            }

            this.currentCount = count || 0;
            this.counterValue.textContent = this.currentCount;
            this.counterLabel.textContent = suffix;

            // Удаляем все классы состояний
            this.indicator.classList.remove('loading', 'success', 'warning', 'error');

            // Показываем индикатор
            this.indicator.classList.add('show');
            this.isVisible = true;

            console.log(`[TasksCounter] ✅ Индикатор показан: ${this.currentCount} ${suffix}`);
        },

        // Скрыть индикатор
        hide: function() {
            if (!this.indicator) return;

            this.indicator.classList.remove('show');
            this.isVisible = false;

            console.log('[TasksCounter] ✅ Индикатор скрыт');
        },

        // Показать состояние загрузки
        showLoading: function(message = 'Загрузка...') {
            if (!this.indicator) {
                if (!this.initialize()) return;
            }

            // Удаляем все классы состояний и добавляем loading
            this.indicator.classList.remove('success', 'warning', 'error');
            this.indicator.classList.add('show', 'loading');

            // Обновляем текст загрузки
            const loadingText = this.loadingElement.querySelector('.loading-text');
            if (loadingText) {
                loadingText.textContent = message;
            }

            this.isVisible = true;
            this.isLoading = true;

            console.log(`[TasksCounter] ⏳ Показано состояние загрузки: "${message}"`);
        },

        // Скрыть состояние загрузки
        hideLoading: function() {
            if (!this.indicator) return;

            this.indicator.classList.remove('loading');
            this.isLoading = false;

            console.log('[TasksCounter] ✅ Состояние загрузки скрыто');
        },

        // Обновить счетчик
        updateCount: function(count, suffix = 'задач найдено') {
            if (!this.indicator) {
                if (!this.initialize()) return;
            }

            this.currentCount = count || 0;

            // Если индикатор уже видим, анимируем изменение счетчика
            if (this.isVisible) {
                // Анимация счетчика
                this.animateCounter(this.currentCount);
            } else {
                // Просто обновляем значение
                this.counterValue.textContent = this.currentCount;
            }

            this.counterLabel.textContent = suffix;

            // Определяем класс состояния в зависимости от количества
            if (this.currentCount === 0) {
                this.indicator.classList.add('warning');
                this.indicator.classList.remove('success', 'error');
            } else {
                this.indicator.classList.add('success');
                this.indicator.classList.remove('warning', 'error');
            }

            console.log(`[TasksCounter] 🔢 Счетчик обновлен: ${this.currentCount} ${suffix}`);
        },

        // Анимация изменения счетчика
        animateCounter: function(newValue) {
            if (!this.counterValue) return;

            const oldValue = parseInt(this.counterValue.textContent) || 0;
            const diff = newValue - oldValue;

            if (diff === 0) return;

            // Добавляем класс для анимации пульсации
            this.indicator.classList.add('pulse');

            // Устанавливаем новое значение
            this.counterValue.textContent = newValue;

            // Удаляем класс пульсации через 2 секунды
            setTimeout(() => {
                this.indicator.classList.remove('pulse');
            }, 2000);
        },

        // Показать ошибку
        showError: function(message = 'Произошла ошибка') {
            if (!this.indicator) {
                if (!this.initialize()) return;
            }

            // Удаляем все классы состояний и добавляем error
            this.indicator.classList.remove('success', 'warning', 'loading');
            this.indicator.classList.add('show', 'error');

            this.counterValue.textContent = '!';
            this.counterLabel.textContent = message;

            this.isVisible = true;

            console.log(`[TasksCounter] ❌ Показана ошибка: "${message}"`);
        }
    };

    // Инициализируем менеджер
    window.TasksCounterManager.initialize();
});
