const tests = require('./test_search_functions.js');

console.log('=== ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ ФУНКЦИЙ РАСШИРЕННОГО ПОИСКА ===\n');

// Запускаем функциональные тесты
const results = tests.runSearchTests();

console.log('\n=== АНАЛИЗ ПРОВАЛИВШИХСЯ ТЕСТОВ ===');
if (results.failed > 0) {
    console.log('Проведем детальный анализ...\n');

    // Перебираем все тесты для детального анализа
    tests.searchTests.forEach((test, index) => {
        const actualResults = tests.testDataForSearch
            .filter(task => tests.searchInTaskData(test.searchTerm, task))
            .map(task => task.id);

        const expectedResults = test.expectedResults.sort();
        const actualResultsSorted = actualResults.sort();
        const isMatch = JSON.stringify(expectedResults) === JSON.stringify(actualResultsSorted);

        if (!isMatch) {
            console.log(`❌ ПРОВАЛЕН - Тест ${index + 1}: ${test.name}`);
            console.log(`   Поисковый запрос: "${test.searchTerm}"`);
            console.log(`   Ожидалось: [${expectedResults.join(', ')}]`);
            console.log(`   Получено: [${actualResultsSorted.join(', ')}]`);
            console.log(`   Описание: ${test.description}\n`);
        }
    });
}

console.log('\n=== ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ===');
tests.runPerformanceTests();

console.log('\n=== ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===');
console.log('Всего тестов:', results.total);
console.log('Успешных:', results.passed);
console.log('Неудачных:', results.failed);
console.log('Процент успеха:', results.successRate + '%');

if (results.failed === 0) {
    console.log('\n🎉 Все тесты пройдены успешно! Функционал готов к использованию.');
} else {
    console.log(`\n⚠️ Обнаружено ${results.failed} проблем. Требуется доработка.`);
}
