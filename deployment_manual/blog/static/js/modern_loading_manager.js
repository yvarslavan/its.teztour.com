/**
 * Modern Loading Manager
 * Управление современным спиннером загрузки
 * Version: 2.0
 * Date: 2024
 */

(function() {
    'use strict';

    // Глобальный объект для управления загрузкой
    window.ModernLoadingManager = {
        spinner: null,
        progressFill: null,
        progressPercent: null,
        progressStatus: null,
        loadingStep: null,
        isVisible: false,
        hideTimeout: null,
        progressInterval: null,
        currentProgress: 0,

        // Инициализация
        init: function() {
            this.spinner = document.getElementById('loading-spinner');
            if (!this.spinner) {
                console.warn('[ModernLoadingManager] Спиннер загрузки не найден');
                return;
            }

            this.progressFill = this.spinner.querySelector('.progress-fill');
            this.progressPercent = this.spinner.querySelector('.progress-percent');
            this.progressStatus = this.spinner.querySelector('.progress-status');
            this.loadingStep = this.spinner.querySelector('.loading-step');

            console.log('[ModernLoadingManager] Инициализация завершена');

            // Автоматически скрываем спиннер после загрузки страницы
            this.setupAutoHide();
        },

        // Показать спиннер
        show: function(message = 'Подключение к Redmine', status = 'Инициализация') {
            if (this.isVisible) return;

            console.log('[ModernLoadingManager] Показываем спиннер загрузки');

            // Отменяем таймер скрытия если он был запущен
            if (this.hideTimeout) {
                clearTimeout(this.hideTimeout);
                this.hideTimeout = null;
            }

            // Сбрасываем прогресс
            this.currentProgress = 0;
            this.updateProgress(0);

            // Обновляем текст
            if (this.loadingStep) {
                this.loadingStep.textContent = message;
            }
            if (this.progressStatus) {
                this.progressStatus.textContent = status;
            }

            // Показываем спиннер
            if (this.spinner) {
                this.spinner.classList.remove('hidden');
                this.isVisible = true;
            }

            // Запускаем анимацию прогресса
            this.startProgressAnimation();
        },

        // Скрыть спиннер
        hide: function(immediate = false) {
            if (!this.isVisible) return;

            console.log('[ModernLoadingManager] Скрываем спиннер загрузки');

            // Останавливаем анимацию прогресса
            this.stopProgressAnimation();

            if (immediate) {
                this.hideSpinner();
            } else {
                // Завершаем прогресс до 100%
                this.updateProgress(100);
                if (this.progressStatus) {
                    this.progressStatus.textContent = 'Загрузка завершена';
                }

                // Скрываем с задержкой для плавной анимации
                this.hideTimeout = setTimeout(() => {
                    this.hideSpinner();
                }, 500);
            }
        },

        // Непосредственное скрытие спиннера
        hideSpinner: function() {
            if (this.spinner) {
                this.spinner.classList.add('hidden');
                this.isVisible = false;
            }
        },

        // Обновить прогресс
        updateProgress: function(percent) {
            this.currentProgress = Math.min(100, Math.max(0, percent));

            if (this.progressFill) {
                this.progressFill.style.width = this.currentProgress + '%';
            }
            if (this.progressPercent) {
                this.progressPercent.textContent = Math.round(this.currentProgress) + '%';
            }
        },

        // Обновить статус
        updateStatus: function(status) {
            if (this.progressStatus) {
                this.progressStatus.textContent = status;
            }
        },

        // Обновить сообщение
        updateMessage: function(message) {
            if (this.loadingStep) {
                this.loadingStep.textContent = message;
            }
        },

        // Запустить анимацию прогресса
        startProgressAnimation: function() {
            this.stopProgressAnimation();

            let targetProgress = 70;
            const increment = 2;

            this.progressInterval = setInterval(() => {
                if (this.currentProgress < targetProgress) {
                    this.updateProgress(this.currentProgress + increment);
                } else if (targetProgress < 90) {
                    // Медленно увеличиваем до 90%
                    targetProgress = 90;
                    this.updateProgress(this.currentProgress + 0.5);
                }

                // Обновляем статус в зависимости от прогресса
                if (this.currentProgress < 30) {
                    this.updateStatus('Подключение к серверу');
                } else if (this.currentProgress < 60) {
                    this.updateStatus('Загрузка данных');
                } else if (this.currentProgress < 90) {
                    this.updateStatus('Обработка информации');
                }
            }, 100);
        },

        // Остановить анимацию прогресса
        stopProgressAnimation: function() {
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
                this.progressInterval = null;
            }
        },

        // Настройка автоматического скрытия
        setupAutoHide: function() {
            // Скрываем спиннер когда DOM полностью загружен
            if (document.readyState === 'complete') {
                setTimeout(() => this.hide(), 1000);
            } else {
                window.addEventListener('load', () => {
                    setTimeout(() => this.hide(), 1000);
                });
            }

            // Скрываем спиннер когда DataTables инициализирован
            $(document).on('datatables-initialized', () => {
                console.log('[ModernLoadingManager] DataTables инициализирован, скрываем спиннер');
                this.hide();
            });

            // Скрываем спиннер при первой успешной загрузке данных
            $(document).on('ajax.dt', (e, settings, json) => {
                if (json && json.data && json.data.length >= 0) {
                    console.log('[ModernLoadingManager] Данные загружены, скрываем спиннер');
                    this.hide();
                }
            });
        }
    };

    // Инициализация при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.ModernLoadingManager.init();
        });
    } else {
        window.ModernLoadingManager.init();
    }

    // Глобальные функции для обратной совместимости
    window.showLoadingSpinner = function(message, status) {
        window.ModernLoadingManager.show(message, status);
    };

    window.hideLoadingSpinner = function(immediate) {
        window.ModernLoadingManager.hide(immediate);
    };

})();
