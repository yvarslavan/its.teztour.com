/**
 * Debounce utility - ограничивает частоту выполнения функции
 * @param {Function} func - функция для выполнения
 * @param {number} wait - задержка в миллисекундах
 * @param {boolean} immediate - выполнить немедленно при первом вызове
 * @returns {Function} debounced функция
 */
function debounce(func, wait, immediate = false) {
    let timeout;

    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(this, args);
        };

        const callNow = immediate && !timeout;

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);

        if (callNow) func.apply(this, args);
    };
}

/**
 * Throttle utility - ограничивает выполнение функции до одного раза в указанный период
 * @param {Function} func - функция для выполнения
 * @param {number} limit - период в миллисекундах
 * @returns {Function} throttled функция
 */
function throttle(func, limit) {
    let inThrottle;

    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Экспорт для ES6 модулей и глобального использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { debounce, throttle };
} else if (typeof window !== 'undefined') {
    window.debounce = debounce;
    window.throttle = throttle;
}
