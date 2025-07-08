/**
 * Force Cache Refresh Script
 * Принудительное обновление кэша для применения изменений CSS
 */

(function() {
    // Функция для добавления timestamp к URL
    function addTimestamp(url) {
        const timestamp = new Date().getTime();
        const separator = url.includes('?') ? '&' : '?';
        return `${url}${separator}v=${timestamp}`;
    }

    // Обновляем все CSS файлы
    function refreshCSS() {
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && (href.includes('modern_header_redesign.css') ||
                        href.includes('modern_header_extended.css') ||
                        href.includes('.css'))) {
                // Создаем новый элемент link
                const newLink = document.createElement('link');
                newLink.rel = 'stylesheet';
                newLink.href = addTimestamp(href.split('?')[0]);

                // Заменяем старый link новым
                link.parentNode.replaceChild(newLink, link);

                console.log(`Обновлен CSS: ${newLink.href}`);
            }
        });
    }

    // Очищаем localStorage и sessionStorage
    function clearStorage() {
        try {
            localStorage.clear();
            sessionStorage.clear();
            console.log('Storage очищен');
        } catch (e) {
            console.error('Ошибка при очистке storage:', e);
        }
    }

    // Принудительная перезагрузка страницы
    function forceReload() {
        // Очищаем кэш
        clearStorage();

        // Добавляем meta tag для отключения кэша
        const metaNoCache = document.createElement('meta');
        metaNoCache.httpEquiv = 'Cache-Control';
        metaNoCache.content = 'no-cache, no-store, must-revalidate';
        document.head.appendChild(metaNoCache);

        const metaPragma = document.createElement('meta');
        metaPragma.httpEquiv = 'Pragma';
        metaPragma.content = 'no-cache';
        document.head.appendChild(metaPragma);

        const metaExpires = document.createElement('meta');
        metaExpires.httpEquiv = 'Expires';
        metaExpires.content = '0';
        document.head.appendChild(metaExpires);

        console.log('Кэш-контроль установлен');
    }

    // Выполняем при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        console.log('=== Force Cache Refresh активирован ===');
        forceReload();
        refreshCSS();

        // Добавляем кнопку для ручного обновления CSS
        const refreshButton = document.createElement('button');
        refreshButton.innerHTML = '🔄 Обновить CSS';
        refreshButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            padding: 10px 15px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
        refreshButton.onclick = function() {
            refreshCSS();
            setTimeout(() => {
                window.location.reload(true);
            }, 100);
        };
        document.body.appendChild(refreshButton);
    });

    // Автоматическое обновление CSS каждые 5 секунд (для разработки)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        setInterval(refreshCSS, 5000);
    }
})();
