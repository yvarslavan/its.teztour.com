/**
 * Issues Style Loading Manager
 * Управление спиннером загрузки в стиле блока "Мои заявки"
 */

class IssuesStyleLoadingManager {
    constructor() {
        this.spinner = document.getElementById('loading-spinner');
        this.isShowing = false;
        this.hideTimeout = null;

        // Инициализация при загрузке страницы
        this.init();
    }

    init() {
        // Убеждаемся, что спиннер скрыт при инициализации
        if (this.spinner) {
            this.spinner.classList.remove('show');
            this.spinner.style.display = 'none';
        }

        // Слушаем события DataTables
        this.setupDataTablesListeners();

        // Слушаем кастомные события
        this.setupCustomEventListeners();
    }

    setupDataTablesListeners() {
        // Слушаем события обработки данных DataTables
        $(document).on('processing.dt', (e, settings, processing) => {
            if (processing) {
                this.show();
            } else {
                this.hide();
            }
        });

        // Слушаем события перед отправкой AJAX запроса
        $(document).on('preXhr.dt', () => {
            this.show();
        });

        // Слушаем события после получения данных
        $(document).on('xhr.dt', () => {
            this.hide();
        });
    }

    setupCustomEventListeners() {
        // Слушаем кастомные события показа/скрытия спиннера
        document.addEventListener('showLoadingSpinner', () => {
            this.show();
        });

        document.addEventListener('hideLoadingSpinner', () => {
            this.hide();
        });
    }

    show() {
        if (!this.spinner || this.isShowing) return;

        // Отменяем таймаут скрытия, если он есть
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }

        this.isShowing = true;
        this.spinner.style.display = 'flex';

        // Добавляем класс с небольшой задержкой для анимации
        requestAnimationFrame(() => {
            this.spinner.classList.add('show');
        });

        console.log('[LoadingManager] Спиннер показан');
    }

    hide() {
        if (!this.spinner || !this.isShowing) return;

        // Используем таймаут для предотвращения мерцания при быстрых операциях
        this.hideTimeout = setTimeout(() => {
            this.isShowing = false;
            this.spinner.classList.remove('show');

            // Скрываем элемент после завершения анимации
            setTimeout(() => {
                if (!this.isShowing) {
                    this.spinner.style.display = 'none';
                }
            }, 300);

            console.log('[LoadingManager] Спиннер скрыт');
        }, 100);
    }

    // Принудительное скрытие спиннера
    forceHide() {
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }

        this.isShowing = false;
        if (this.spinner) {
            this.spinner.classList.remove('show');
            this.spinner.style.display = 'none';
        }

        console.log('[LoadingManager] Спиннер принудительно скрыт');
    }
}

// Инициализация менеджера при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    window.loadingManager = new IssuesStyleLoadingManager();

    // Принудительно скрываем спиннер через 10 секунд на случай зависания
    setTimeout(() => {
        if (window.loadingManager) {
            window.loadingManager.forceHide();
        }
    }, 10000);
});

// Экспорт функций для обратной совместимости
window.showLoadingSpinner = function() {
    if (window.loadingManager) {
        window.loadingManager.show();
    }
};

window.hideLoadingSpinner = function() {
    if (window.loadingManager) {
        window.loadingManager.hide();
    }
};
