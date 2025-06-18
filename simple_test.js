// Простая проверка функции поиска
const testTask = {
    id: 12346,
    subject: "Настройка VPN соединения",
    description: "Требуется настроить VPN доступ для удаленного сотрудника. Проблемы с аутентификацией.",
    status_name: "В работе",
    priority_name: "Средний",
    project_name: "Сетевое администрирование",
    author_name: "Петров П.П.",
    email_to: "admin@company.com"
};

function searchInTaskData(searchTerm, taskData) {
    if (!searchTerm || searchTerm.trim() === '') {
        return true;
    }

    const searchTermLower = searchTerm.toLowerCase().trim();

    const searchableFields = [
        taskData.id ? String(taskData.id) : '',
        taskData.id ? `#${taskData.id}` : '',
        taskData.subject || '',
        taskData.description || '',
        taskData.project_name || '',
        taskData.status_name || '',
        taskData.priority_name || '',
        taskData.author_name || '',
        taskData.email_to || ''
    ];

    const combinedSearchText = searchableFields
        .filter(field => field && field.trim() !== '')
        .join(' ')
        .toLowerCase();

    console.log(`Поиск: "${searchTerm}"`);
    console.log(`Объединенный текст: "${combinedSearchText}"`);
    console.log(`Содержит термин: ${combinedSearchText.includes(searchTermLower)}`);

    let isMatch = combinedSearchText.includes(searchTermLower);

    // Дополнительно проверяем поиск по номеру задачи
    if (!isMatch && searchTermLower.startsWith('#')) {
        const numericSearch = searchTermLower.substring(1);
        const taskIdString = String(taskData.id || '');
        isMatch = taskIdString.includes(numericSearch);
    }

    // Проверяем поиск только по числу (без #)
    if (!isMatch && /^\d+$/.test(searchTermLower)) {
        const taskIdString = String(taskData.id || '');
        isMatch = taskIdString.includes(searchTermLower);
    }

    return isMatch;
}

console.log('=== ПРОСТОЙ ТЕСТ ПОИСКА ===\n');
console.log('Тестовая задача:', JSON.stringify(testTask, null, 2));
console.log('\n=== ТЕСТЫ ===');

const searchTerms = [
    "настройка",
    "аутентификация",
    "VPN",
    "Петров"
];

searchTerms.forEach(term => {
    console.log(`\n--- Поиск: "${term}" ---`);
    const result = searchInTaskData(term, testTask);
    console.log(`Результат: ${result ? 'НАЙДЕНО' : 'НЕ НАЙДЕНО'}\n`);
});
