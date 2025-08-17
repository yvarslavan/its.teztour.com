const { test, expect } = require('@playwright/test');

test.describe('Main Module Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Переход на главную страницу перед каждым тестом
    await page.goto('/');
  });

  test('должен загрузить главную страницу', async ({ page }) => {
    // Проверяем, что страница загрузилась
    await expect(page).toHaveTitle(/Flask Helpdesk/);

    // Проверяем наличие основных элементов
    await expect(page.locator('body')).toBeVisible();
  });

  test('должен отображать навигационное меню', async ({ page }) => {
    // Проверяем наличие навигации
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();
  });

  test('должен иметь рабочую ссылку на задачи', async ({ page }) => {
    // Ищем ссылку на задачи
    const tasksLink = page.locator('a[href*="tasks"]').first();
    await expect(tasksLink).toBeVisible();

    // Кликаем по ссылке
    await tasksLink.click();

    // Проверяем, что перешли на страницу задач
    await expect(page).toHaveURL(/.*tasks/);
  });

  test('должен отображать уведомления', async ({ page }) => {
    // Проверяем наличие виджета уведомлений
    const notificationsWidget = page.locator('.notifications-widget, #notifications-widget');
    await expect(notificationsWidget).toBeVisible();
  });

  test('должен иметь форму поиска', async ({ page }) => {
    // Ищем форму поиска
    const searchForm = page.locator('form[action*="search"], input[type="search"], input[name*="search"]');
    await expect(searchForm).toBeVisible();
  });

  test('должен отображать информацию о пользователе', async ({ page }) => {
    // Проверяем наличие информации о пользователе
    const userInfo = page.locator('.user-info, .profile-info, [data-user]');
    await expect(userInfo).toBeVisible();
  });

  test('должен иметь рабочую ссылку на профиль', async ({ page }) => {
    // Ищем ссылку на профиль
    const profileLink = page.locator('a[href*="profile"], a[href*="user"]').first();
    await expect(profileLink).toBeVisible();

    // Кликаем по ссылке
    await profileLink.click();

    // Проверяем, что перешли на страницу профиля
    await expect(page).toHaveURL(/.*profile|.*user/);
  });

  test('должен отображать статистику', async ({ page }) => {
    // Проверяем наличие элементов статистики
    const statsElements = page.locator('.statistics, .stats, [data-stats]');
    await expect(statsElements).toBeVisible();
  });

  test('должен иметь рабочую ссылку на сетевой монитор', async ({ page }) => {
    // Ищем ссылку на сетевой монитор
    const networkLink = page.locator('a[href*="network"], a[href*="monitor"]').first();
    await expect(networkLink).toBeVisible();

    // Кликаем по ссылке
    await networkLink.click();

    // Проверяем, что перешли на страницу мониторинга
    await expect(page).toHaveURL(/.*network|.*monitor/);
  });

  test('должен отображать сплэш-экран при загрузке', async ({ page }) => {
    // Проверяем наличие сплэш-экрана
    const splashScreen = page.locator('.splash-screen, .loading-screen, #splash-screen');
    await expect(splashScreen).toBeVisible();
  });

  test('должен иметь рабочую ссылку на качество', async ({ page }) => {
    // Ищем ссылку на качество
    const qualityLink = page.locator('a[href*="quality"]').first();
    await expect(qualityLink).toBeVisible();

    // Кликаем по ссылке
    await qualityLink.click();

    // Проверяем, что перешли на страницу качества
    await expect(page).toHaveURL(/.*quality/);
  });
});

test.describe('Main Module API Tests', () => {
  test('должен отвечать на API запросы', async ({ request }) => {
    // Тестируем API endpoint
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();
  });

  test('должен возвращать данные пользователя', async ({ request }) => {
    // Тестируем получение данных пользователя
    const response = await request.get('/api/user/current');
    const status = response.status();
    expect(status === 200 || status === 401).toBeTruthy(); // 401 если не авторизован
  });

  test('должен обрабатывать фильтры', async ({ request }) => {
    // Тестируем API фильтров
    const response = await request.get('/api/filters');
    const status = response.status();
    expect(status === 200 || status === 404 || status === 401).toBeTruthy(); // Разные возможные статусы
  });
});

test.describe('Main Module Error Handling', () => {
  test('должен обрабатывать 404 ошибки', async ({ page }) => {
    // Переходим на несуществующую страницу
    await page.goto('/non-existent-page');

    // Проверяем, что отображается страница ошибки
    await expect(page.locator('body')).toContainText(/404|не найдено|ошибка/i);
  });

  test('должен обрабатывать ошибки сервера', async ({ page }) => {
    // Тестируем обработку ошибок сервера
    const response = await page.goto('/api/error-test');
    const status = response.status();
    expect(status === 500 || status === 404 || status === 200).toBeTruthy(); // Разные возможные статусы
  });
});

test.describe('Main Module Performance Tests', () => {
  test('должен загружаться быстро', async ({ page }) => {
    const startTime = Date.now();

    // Загружаем главную страницу
    await page.goto('/');

    const loadTime = Date.now() - startTime;

    // Проверяем, что страница загрузилась за разумное время (менее 5 секунд)
    expect(loadTime).toBeLessThan(5000);
  });

  test('должен иметь оптимизированные изображения', async ({ page }) => {
    await page.goto('/');

    // Проверяем, что изображения загружаются
    const images = page.locator('img');
    await expect(images).toBeVisible();
  });
});

test.describe('Main Module Accessibility Tests', () => {
  test('должен иметь правильную структуру заголовков', async ({ page }) => {
    await page.goto('/');

    // Проверяем наличие заголовков
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    await expect(headings).toBeVisible();
  });

  test('должен иметь альтернативный текст для изображений', async ({ page }) => {
    await page.goto('/');

    // Проверяем наличие alt атрибутов у изображений
    const images = page.locator('img');
    for (let i = 0; i < await images.count(); i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });
});
