/**
 * ================================
 * MODERN SPLASH SCREEN CONTROLLER
 * ================================
 *
 * Управляет показом/скрытием Splash Screen
 * с адаптивными настройками и плавными переходами
 */

class ModernSplashScreen {
    constructor(options = {}) {
        // Настройки по умолчанию
        this.options = {
            // Время показа (в миллисекундах)
            displayTime: options.displayTime || 3500,

            // Минимальное время показа
            minDisplayTime: options.minDisplayTime || 2000,

            // Максимальное время показа
            maxDisplayTime: options.maxDisplayTime || 6000,

            // Селекторы элементов
            splashSelector: options.splashSelector || '.modern-splash-screen',
            bodySelector: options.bodySelector || 'body',

            // Callback функции
            onShow: options.onShow || null,
            onHide: options.onHide || null,
            onComplete: options.onComplete || null,

            // Настройки для отладки
            debug: options.debug || false,

            // Отключить для определенных страниц
            disableFor: options.disableFor || [],

            // Показывать только для первого визита
            showOnlyOnce: options.showOnlyOnce || false
        };

        // Состояние
        this.isVisible = false;
        this.startTime = null;
        this.splashElement = null;

        // Элементы управления
        this.progressBar = null;
        this.loadingText = null;

        // Инициализация
        this.init();
    }

    /**
     * Инициализация Splash Screen
     */
    init() {
        this.log('🚀 Инициализация Modern Splash Screen');

        // Проверяем, нужно ли показывать splash screen
        if (!this.shouldShow()) {
            this.log('❌ Splash Screen отключен для данной страницы/сессии');
            return;
        }

        // Ждем готовности DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setup();
            });
        } else {
            this.setup();
        }
    }

    /**
     * Проверка, нужно ли показывать Splash Screen
     */
    shouldShow() {
        // ГЛАВНАЯ ПРОВЕРКА: атрибут data-show-splash в body
        const body = document.body;
        const showSplash = body.dataset.showSplash;

        // Если атрибут установлен в 'false', не показываем splash screen
        if (showSplash === 'false') {
            this.log('🚫 Splash screen отключен через data-show-splash="false"');
            return false;
        }

        // Если атрибут не установлен в 'true', также не показываем
        if (showSplash !== 'true') {
            this.log('🚫 Splash screen не разрешен - data-show-splash не равен "true"');
            return false;
        }

        // Дополнительные проверки только если основная проверка пройдена

        // Проверяем настройки отключения для страниц
        const currentPath = window.location.pathname;
        if (this.options.disableFor.includes(currentPath)) {
            this.log(`🚫 Splash screen отключен для пути: ${currentPath}`);
            return false;
        }

        // Проверяем настройку показа только один раз
        if (this.options.showOnlyOnce) {
            const hasShownBefore = localStorage.getItem('splash_screen_shown');
            if (hasShownBefore) {
                this.log('🚫 Splash screen уже показывался ранее (showOnlyOnce = true)');
                return false;
            }
        }

        // Проверяем, не отключил ли пользователь splash screen
        const userDisabled = localStorage.getItem('splash_screen_disabled');
        if (userDisabled === 'true') {
            this.log('🚫 Splash screen отключен пользователем через localStorage');
            return false;
        }

        this.log('✅ Splash screen разрешен к показу');
        return true;
    }

        /**
     * Настройка элементов и запуск
     */
    setup() {
        // Находим splash screen элемент
        this.splashElement = document.querySelector(this.options.splashSelector);

        // Если элемент не найден, значит splash screen не должен отображаться на этой странице
        if (!this.splashElement) {
            this.log('🚫 Элемент splash screen не найден в DOM - завершаем инициализацию');
            return;
        }

        // Получаем ссылки на элементы управления
        this.progressBar = this.splashElement.querySelector('.splash-progress-bar');
        this.loadingText = this.splashElement.querySelector('.splash-loading-text');
        this.statusText = this.splashElement.querySelector('.splash-status-text');
        this.percentageNumber = this.splashElement.querySelector('.percentage-number');

        // Создаем фоновые частицы
        this.createBackgroundElements();

        // Инициализируем современные прогресс-индикаторы
        this.initModernProgress();

        // Показываем splash screen
        this.show();

        // Настраиваем автоматическое скрытие
        this.setupAutoHide();

        // Отмечаем, что splash screen был показан
        if (this.options.showOnlyOnce) {
            localStorage.setItem('splash_screen_shown', 'true');
        }
    }

    /**
     * Создание фоновых элементов (частицы, геометрия)
     */
    createBackgroundElements() {
        const background = this.splashElement.querySelector('.splash-background');
        if (!background) return;

        // Создаем плавающие частицы
        this.createParticles(background);

        // Создаем геометрические фигуры
        this.createGeometry(background);
    }

    /**
     * Создание плавающих частиц
     */
    createParticles(container) {
        const particleCount = this.isMobile() ? 3 : 5;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'splash-particle';

            // Случайные позиции и размеры
            const x = Math.random() * 100;
            const delay = Math.random() * 4;
            const size = 2 + Math.random() * 4;

            particle.style.left = `${x}%`;
            particle.style.animationDelay = `${delay}s`;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;

            container.appendChild(particle);
        }
    }

    /**
     * Создание геометрических фигур
     */
    createGeometry(container) {
        if (this.isMobile()) return; // Не показываем на мобильных

        const geometryCount = 3;

        for (let i = 0; i < geometryCount; i++) {
            const geometry = document.createElement('div');
            geometry.className = 'splash-geometry';
            container.appendChild(geometry);
        }
    }

    /**
     * Показ Splash Screen
     */
    show() {
        this.log('👁️ Показываем Splash Screen');

        this.isVisible = true;
        this.startTime = Date.now();

        // Добавляем класс для предотвращения скролла
        document.body.classList.add('splash-active');

        // Показываем элемент
        this.splashElement.style.display = 'flex';
        this.splashElement.classList.remove('hidden');

        // Callback
        if (this.options.onShow) {
            this.options.onShow();
        }

        // Обновляем прогресс
        this.updateProgress();
    }

    /**
     * Обновление прогресса загрузки
     */
    updateProgress() {
        if (!this.progressBar || !this.isVisible) return;

        const elapsed = Date.now() - this.startTime;
        const progress = Math.min((elapsed / this.options.displayTime) * 100, 100);

        this.progressBar.style.width = `${progress}%`;

        // Обновляем текст загрузки
        if (this.loadingText) {
            const messages = [
                'Загружаем интерфейс...',
                'Подготавливаем данные...',
                'Инициализируем систему...',
                'Почти готово...'
            ];

            const messageIndex = Math.floor(progress / 25);
            if (messages[messageIndex]) {
                this.loadingText.textContent = messages[messageIndex];
            }
        }

        // Продолжаем обновление, если не достигли 100%
        if (progress < 100) {
            requestAnimationFrame(() => this.updateProgress());
        }
    }

    /**
     * Настройка автоматического скрытия
     */
    setupAutoHide() {
        // Минимальное время показа
        setTimeout(() => {
            this.checkReadyToHide();
        }, this.options.minDisplayTime);

        // Максимальное время показа (принудительное скрытие)
        setTimeout(() => {
            this.log('⏰ Принудительное скрытие по таймауту');
            this.hide();
        }, this.options.maxDisplayTime);

        // Скрытие по клику (для тестирования)
        if (this.options.debug) {
            this.splashElement.addEventListener('click', () => {
                this.log('🖱️ Скрытие по клику (debug режим)');
                this.hide();
            });
        }
    }

    /**
     * Проверка готовности к скрытию
     */
    checkReadyToHide() {
        // Проверяем, прошло ли достаточно времени
        const elapsed = Date.now() - this.startTime;
        if (elapsed >= this.options.displayTime) {
            this.hide();
            return;
        }

        // Ждем еще немного
        const remaining = this.options.displayTime - elapsed;
        setTimeout(() => this.hide(), remaining);
    }

    /**
     * Скрытие Splash Screen
     */
    hide() {
        if (!this.isVisible) return;

        this.log('👋 Скрываем Splash Screen');

        this.isVisible = false;

        // Добавляем класс для анимации скрытия
        this.splashElement.classList.add('hidden');

        // Убираем блокировку скролла
        document.body.classList.remove('splash-active');

        // Callback
        if (this.options.onHide) {
            this.options.onHide();
        }

        // Полностью удаляем элемент после анимации
        setTimeout(() => {
            if (this.splashElement && this.splashElement.parentNode) {
                this.splashElement.style.display = 'none';

                // Callback завершения
                if (this.options.onComplete) {
                    this.options.onComplete();
                }

                this.log('✅ Splash Screen полностью скрыт');
            }
        }, 800); // Время анимации из CSS
    }

    /**
     * Проверка мобильного устройства
     */
    isMobile() {
        return window.innerWidth <= 768;
    }

    /**
     * Логирование (только в debug режиме)
     */
    log(message) {
        if (this.options.debug) {
            console.log(`[ModernSplashScreen] ${message}`);
        }
    }

    /**
     * Публичные методы управления
     */

    /**
     * Принудительное скрытие
     */
    forceHide() {
        this.hide();
    }

    /**
     * Отключение для текущей сессии
     */
    disable() {
        localStorage.setItem('splash_screen_disabled', 'true');
        this.hide();
    }

    /**
     * Включение (удаление флага отключения)
     */
    enable() {
        localStorage.removeItem('splash_screen_disabled');
        localStorage.removeItem('splash_screen_shown');
    }

    /**
     * Получение состояния
     */
    getState() {
        return {
            isVisible: this.isVisible,
            startTime: this.startTime,
            elapsed: this.startTime ? Date.now() - this.startTime : 0
        };
    }

    /**
     * Инициализация современных прогресс-индикаторов
     */
    initModernProgress() {
        try {
            this.log('🎯 Инициализация современных прогресс-индикаторов');

            // Анимация счетчика процентов
            this.animatePercentageCounter();

            // Обновление статусных сообщений
            this.animateStatusMessages();

            this.log('✅ Прогресс-индикаторы инициализированы');
        } catch (error) {
            this.log(`❌ Ошибка инициализации прогресс-индикаторов: ${error.message}`);
        }
    }

    /**
     * Анимация счетчика процентов
     */
    animatePercentageCounter() {
        if (!this.percentageNumber) return;

        let currentPercentage = 0;
        const targetPercentage = 100;
        const duration = 3000; // 3 секунды
        const incrementTime = 50; // Обновляем каждые 50ms
        const totalSteps = duration / incrementTime;
        const incrementValue = targetPercentage / totalSteps;

        const timer = setInterval(() => {
            currentPercentage += incrementValue;

            if (currentPercentage >= targetPercentage) {
                currentPercentage = targetPercentage;
                clearInterval(timer);
            }

            this.percentageNumber.textContent = Math.round(currentPercentage);
        }, incrementTime);
    }

    /**
     * Анимация статусных сообщений
     */
    animateStatusMessages() {
        if (!this.statusText) return;

        const messages = [
            'Инициализация системы...',
            'Загрузка компонентов...',
            'Проверка соединения...',
            'Подготовка интерфейса...',
            'Настройка параметров...',
            'Завершение загрузки...'
        ];

        let messageIndex = 0;
        const messageInterval = setInterval(() => {
            if (messageIndex < messages.length) {
                this.statusText.textContent = messages[messageIndex];
                messageIndex++;
            } else {
                clearInterval(messageInterval);
                this.statusText.textContent = 'Готово к работе!';
            }
        }, 500); // Меняем сообщение каждые 500ms
    }
}

/**
 * ================================
 * АВТОИНИЦИАЛИЗАЦИЯ
 * ================================
 */

// Глобальная переменная для доступа к экземпляру
window.modernSplashScreen = null;

// Автоматическая инициализация при загрузке страницы
(function() {
    // Проверяем настройки из data-атрибутов body
    const body = document.body;

    // ВАЖНО: Проверяем, разрешен ли splash screen на этой странице
    const showSplash = body.dataset.showSplash;

    console.log(`[SplashScreen] Автоинициализация: data-show-splash = "${showSplash}"`);

    // Если splash screen отключен, не инициализируем его вовсе
    if (showSplash === 'false') {
        console.log('[SplashScreen] 🚫 Splash screen отключен для данной страницы - инициализация прервана');
        return;
    }

    const splashConfig = {
        debug: body.dataset.splashDebug === 'true',
        displayTime: parseInt(body.dataset.splashTime) || 3500,
        showOnlyOnce: body.dataset.splashOnce === 'true',
        disableFor: body.dataset.splashDisable ? body.dataset.splashDisable.split(',') : []
    };

    console.log('[SplashScreen] 🚀 Инициализация с настройками:', splashConfig);

    // Создаем экземпляр
    window.modernSplashScreen = new ModernSplashScreen(splashConfig);

    // Добавляем в глобальный объект для удобства
    if (window.TEZ) {
        window.TEZ.splashScreen = window.modernSplashScreen;
    } else {
        window.TEZ = {
            splashScreen: window.modernSplashScreen
        };
    }
})();

/**
 * ================================
 * УТИЛИТЫ И ХЕЛПЕРЫ
 * ================================
 */

// Утилиты для тестирования splash screen
window.splashScreenUtils = {
    // Проверить текущие настройки страницы
    checkPageSettings: function() {
        const body = document.body;
        const settings = {
            showSplash: body.dataset.showSplash,
            splashTime: body.dataset.splashTime,
            splashOnce: body.dataset.splashOnce,
            splashDebug: body.dataset.splashDebug,
            currentPath: window.location.pathname,
            currentEndpoint: body.dataset.endpoint || 'неизвестно'
        };

        console.log('🔍 Настройки Splash Screen для текущей страницы:', settings);
        return settings;
    },

    // Принудительно показать splash screen для тестирования
    forceShow: function() {
        if (window.modernSplashScreen) {
            console.log('🧪 Принудительный показ splash screen...');
            window.modernSplashScreen.show();
        } else {
            console.log('❌ Экземпляр splash screen не найден');
        }
    },

    // Принудительно скрыть splash screen
    forceHide: function() {
        if (window.modernSplashScreen) {
            console.log('🧪 Принудительное скрытие splash screen...');
            window.modernSplashScreen.hide();
        } else {
            console.log('❌ Экземпляр splash screen не найден');
        }
    },

    // Сбросить все настройки localStorage
    resetSettings: function() {
        localStorage.removeItem('splash_screen_shown');
        localStorage.removeItem('splash_screen_disabled');
        console.log('🔄 Настройки splash screen сброшены');
    },

    // Тестирование современных индикаторов прогресса
    testProgressIndicators: function() {
        if (window.modernSplashScreen) {
            console.log('🧪 Тестирование индикаторов прогресса...');
            const instance = window.modernSplashScreen;
            if (instance.percentageNumber) {
                instance.animatePercentageCounter();
                console.log('✅ Анимация процентов запущена');
            }
            if (instance.statusText) {
                instance.animateStatusMessages();
                console.log('✅ Анимация статусов запущена');
            }
        } else {
            console.log('❌ Экземпляр splash screen не найден');
        }
    },

    // Информация о новых возможностях
    showNewFeatures: function() {
        console.log('🆕 Новые возможности Splash Screen:');
        console.log('  🎨 Современный glass morphism дизайн');
        console.log('  🌈 Яркий градиентный фон с текстурами');
        console.log('  💫 Увеличенный логотип с плавающей анимацией');
        console.log('  📊 Круговой прогресс-индикатор с процентами');
        console.log('  🎯 Линейный прогресс с этапами загрузки');
        console.log('  💬 Брендовые слоганы TEZ TOUR');
        console.log('  📱 Улучшенная адаптивность для всех устройств');
        console.log('  ✨ Анимированные тексты и спецэффекты');
    }
};

// Добавляем стили для блокировки скролла во время показа
const splashStyles = document.createElement('style');
splashStyles.textContent = `
    body.splash-active {
        overflow: hidden !important;
        height: 100vh !important;
    }

    /* Дополнительные утилиты */
    .splash-debug-info {
        position: fixed;
        top: 10px;
        left: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-size: 12px;
        z-index: 10000;
        font-family: monospace;
    }
`;
document.head.appendChild(splashStyles);

// Добавляем консольные команды для отладки
if (typeof window !== 'undefined') {
    window.splashDebug = {
        show: () => window.modernSplashScreen?.show(),
        hide: () => window.modernSplashScreen?.forceHide(),
        disable: () => window.modernSplashScreen?.disable(),
        enable: () => window.modernSplashScreen?.enable(),
        state: () => window.modernSplashScreen?.getState(),
        log: (enabled = true) => {
            if (window.modernSplashScreen) {
                window.modernSplashScreen.options.debug = enabled;
            }
        }
    };

    // Информация для разработчиков
    console.log(`
    🎨 Modern Splash Screen loaded!

    Debug commands:
    - splashDebug.show()     - показать splash screen
    - splashDebug.hide()     - скрыть splash screen
    - splashDebug.disable()  - отключить для сессии
    - splashDebug.enable()   - включить заново
    - splashDebug.state()    - получить состояние
    - splashDebug.log(true)  - включить логи
    `);
}

/**
 * ================================
 * СОБЫТИЯ И ИНТЕГРАЦИИ
 * ================================
 */

// Интеграция с существующими системами уведомлений
document.addEventListener('DOMContentLoaded', () => {
    // Совместимость с системой уведомлений
    if (typeof window.refreshNotificationBadge === 'function') {
        window.addEventListener('newNotification', (event) => {
            // Если splash screen активен, можем показать уведомление позже
            if (window.modernSplashScreen?.isVisible) {
                setTimeout(() => {
                    window.refreshNotificationBadge(event.detail.count);
                }, 1000);
            }
        });
    }
});

// Обработка изменения размера окна
window.addEventListener('resize', () => {
    if (window.modernSplashScreen?.isVisible) {
        // Можем обновить частицы или другие элементы при изменении размера
        // Пока оставляем пустым - CSS адаптивность справляется
    }
});
