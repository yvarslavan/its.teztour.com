const { test, expect } = require('@playwright/test');

test.describe('Main Module Test Pages', () => {
  test('должен загрузить тестовую страницу фильтров API', async ({ page }) => {
    // Переходим на тестовую страницу фильтров
    await page.goto('/test-filters-api');

    // Проверяем, что страница загрузилась
    await expect(page).toHaveTitle(/Тест API фильтров/);

    // Проверяем наличие основных элементов
    await expect(page.locator('h1')).toContainText('Тестирование API фильтров');

    // Проверяем наличие кнопок тестирования
    const testButtons = page.locator('.test-button');
    await expect(testButtons).toHaveCount(4);

    // Проверяем наличие секций результатов
    const resultSections = page.locator('.test-section');
    await expect(resultSections).toHaveCount(4);
  });

  test('должен загрузить простую тестовую страницу API', async ({ page }) => {
    // Переходим на простую тестовую страницу
    await page.goto('/simple-api-test');

    // Проверяем, что страница загрузилась
    await expect(page).toHaveTitle(/Простой тест API/);

    // Проверяем наличие основных элементов
    await expect(page.locator('h1')).toContainText('Простое тестирование API');

    // Проверяем наличие карточек тестирования
    const testCards = page.locator('.test-card');
    await expect(testCards).toHaveCount(7);

    // Проверяем наличие кнопок тестирования
    const testButtons = page.locator('.test-button');
    await expect(testButtons).toHaveCount(7);
  });

  test('должен выполнить тест получения фильтров', async ({ page }) => {
    await page.goto('/test-filters-api');

    // Кликаем по кнопке "Получить фильтры"
    await page.locator('button:has-text("Получить фильтры")').click();

    // Ждем появления результата
    await page.waitForSelector('#filters-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#filters-result');
    await expect(result).toBeVisible();

    // Проверяем, что результат содержит информацию
    const resultText = await result.textContent();
    expect(resultText).toBeTruthy();
  });

  test('должен выполнить тест применения фильтра', async ({ page }) => {
    await page.goto('/test-filters-api');

    // Кликаем по кнопке "Применить фильтр"
    await page.locator('button:has-text("Применить фильтр")').click();

    // Ждем появления результата
    await page.waitForSelector('#apply-filter-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#apply-filter-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест сброса фильтров', async ({ page }) => {
    await page.goto('/test-filters-api');

    // Кликаем по кнопке "Сбросить фильтры"
    await page.locator('button:has-text("Сбросить фильтры")').click();

    // Ждем появления результата
    await page.waitForSelector('#reset-filters-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#reset-filters-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест сохранения фильтра', async ({ page }) => {
    await page.goto('/test-filters-api');

    // Кликаем по кнопке "Сохранить фильтр"
    await page.locator('button:has-text("Сохранить фильтр")').click();

    // Ждем появления результата
    await page.waitForSelector('#save-filter-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#save-filter-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест подключения к серверу', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Кликаем по кнопке "Проверить подключение"
    await page.locator('button:has-text("Проверить подключение")').click();

    // Ждем появления результата
    await page.waitForSelector('#connection-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#connection-result');
    await expect(result).toBeVisible();

    // Проверяем, что результат содержит информацию о подключении
    const resultText = await result.textContent();
    expect(resultText).toContain('Сервер');
  });

  test('должен выполнить тест аутентификации', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Кликаем по кнопке "Проверить аутентификацию"
    await page.locator('button:has-text("Проверить аутентификацию")').click();

    // Ждем появления результата
    await page.waitForSelector('#auth-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#auth-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест получения данных пользователя', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Кликаем по кнопке "Получить данные пользователя"
    await page.locator('button:has-text("Получить данные пользователя")').click();

    // Ждем появления результата
    await page.waitForSelector('#user-data-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#user-data-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест сессии', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Кликаем по кнопке "Проверить сессию"
    await page.locator('button:has-text("Проверить сессию")').click();

    // Ждем появления результата
    await page.waitForSelector('#session-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#session-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест главной страницы', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Кликаем по кнопке "Проверить главную страницу"
    await page.locator('button:has-text("Проверить главную страницу")').click();

    // Ждем появления результата
    await page.waitForSelector('#home-page-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#home-page-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест статистики', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Кликаем по кнопке "Получить статистику"
    await page.locator('button:has-text("Получить статистику")').click();

    // Ждем появления результата
    await page.waitForSelector('#statistics-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#statistics-result');
    await expect(result).toBeVisible();
  });

  test('должен выполнить тест очистки кэша', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Кликаем по кнопке "Очистить кэш"
    await page.locator('button:has-text("Очистить кэш")').click();

    // Ждем появления результата
    await page.waitForSelector('#cache-result', { timeout: 10000 });

    // Проверяем, что результат отобразился
    const result = page.locator('#cache-result');
    await expect(result).toBeVisible();
  });

  test('должен отображать индикаторы статуса', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Проверяем наличие индикаторов статуса
    const statusIndicators = page.locator('.status-indicator');
    await expect(statusIndicators).toBeVisible();
  });

  test('должен иметь правильные стили для результатов', async ({ page }) => {
    await page.goto('/simple-api-test');

    // Проверяем наличие стилей для результатов
    const resultBoxes = page.locator('.result-box');
    await expect(resultBoxes).toBeVisible();

    // Проверяем, что у кнопок есть правильные стили
    const testButtons = page.locator('.test-button');
    await expect(testButtons).toBeVisible();
  });

  test('должен обрабатывать ошибки API корректно', async ({ page }) => {
    await page.goto('/test-filters-api');

    // Выполняем тест, который может вызвать ошибку
    await page.locator('button:has-text("Получить фильтры")').click();

    // Ждем появления результата
    await page.waitForSelector('#filters-result', { timeout: 10000 });

    // Проверяем, что результат отобразился (даже если это ошибка)
    const result = page.locator('#filters-result');
    await expect(result).toBeVisible();

    // Проверяем, что результат содержит информацию
    const resultText = await result.textContent();
    expect(resultText).toBeTruthy();
  });
});
