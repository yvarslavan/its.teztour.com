/**
 * Отладочный скрипт для принудительного отображения спиннера загрузки
 * Версия: 1.2
 * Дата: 26.12.2023
 */



// Функция для проверки состояния спиннера
function debugSpinner() {
    // Проверяем наличие элемента спиннера
    const spinner = document.getElementById('loading-spinner');


    if (spinner) {



        // Проверяем наличие фильтров
        const statusFilter = document.getElementById('status-filter');
        const projectFilter = document.getElementById('project-filter');
        const priorityFilter = document.getElementById('priority-filter');





        // Проверяем наличие кнопок очистки
        const clearStatusBtn = document.getElementById('clear-status-filter');
        const clearProjectBtn = document.getElementById('clear-project-filter');
        const clearPriorityBtn = document.getElementById('clear-priority-filter');





        // Проверяем загруженные CSS файлы
        const styleSheets = Array.from(document.styleSheets);


        // Проверяем наличие CSS файла спиннера
        const spinnerCssLoaded = styleSheets.some(sheet =>
            sheet.href && sheet.href.includes('modern_spinner_and_filters.css'));

    }
}

// Функция для принудительного применения стилей к спиннеру
function forceShowSpinner() {


    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        // Применяем стили напрямую
        spinner.style.display = 'flex';
        spinner.style.visibility = 'visible';
        spinner.style.opacity = '1';
        spinner.style.zIndex = '9999';
        spinner.style.position = 'fixed';
        spinner.style.top = '0';
        spinner.style.left = '0';
        spinner.style.width = '100%';
        spinner.style.height = '100%';
        spinner.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
        spinner.style.justifyContent = 'center';
        spinner.style.alignItems = 'center';
    } else {
        // Если элемент не найден, создаем новый


        const newSpinner = document.createElement('div');
        newSpinner.id = 'modern-spinner';
        newSpinner.className = 'modern-spinner-overlay';
        newSpinner.innerHTML = `
            <div class="modern-spinner-content">
                <div class="modern-spinner-icon">
                    <i class="fas fa-cog fa-spin"></i>
                </div>
                <h3>Загрузка данных...</h3>
                <p>Пожалуйста, подождите</p>
            </div>
        `;

        // Применяем стили напрямую
        newSpinner.style.display = 'flex';
        newSpinner.style.visibility = 'visible';
        newSpinner.style.opacity = '1';
        newSpinner.style.zIndex = '9999';
        newSpinner.style.position = 'fixed';
        newSpinner.style.top = '0';
        newSpinner.style.left = '0';
        newSpinner.style.width = '100%';
        newSpinner.style.height = '100%';
        newSpinner.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
        newSpinner.style.justifyContent = 'center';
        newSpinner.style.alignItems = 'center';

        document.body.appendChild(newSpinner);
    }
}

// Функция для принудительного применения стилей к кнопкам фильтров
function forceStyleFilterButtons() {


    const clearButtons = [
        document.getElementById('clear-status-filter'),
        document.getElementById('clear-project-filter'),
        document.getElementById('clear-priority-filter')
    ];

    clearButtons.forEach(button => {
        if (button) {
            button.style.display = 'flex';
            button.style.alignItems = 'center';
            button.style.justifyContent = 'center';
            button.style.width = '32px';
            button.style.height = '32px';
            button.style.borderRadius = '50%';
            button.style.backgroundColor = '#f0f0f0';
            button.style.border = 'none';
            button.style.cursor = 'pointer';
            button.style.position = 'absolute';
            button.style.right = '10px';
            button.style.top = '50%';
            button.style.transform = 'translateY(-50%)';
            button.style.zIndex = '5';
            button.style.color = '#666';
            button.style.transition = 'all 0.2s ease';
        }
    });
}

// Запускаем диагностику при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    debugSpinner();

    // Запускаем принудительное применение стилей через 1 секунду
    setTimeout(function() {
        forceShowSpinner();
        forceStyleFilterButtons();
    }, 1000);
});

// Экспортируем функции для использования из консоли
window.debugSpinner = debugSpinner;
window.forceShowSpinner = forceShowSpinner;
window.forceStyleFilterButtons = forceStyleFilterButtons;
