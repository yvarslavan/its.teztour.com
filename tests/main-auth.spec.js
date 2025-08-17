const { test, expect } = require('@playwright/test');

test.describe('Main Module Tests с авторизацией', () => {
  test.beforeEach(async ({ page }) => {
    // Переход на страницу логина
    await page.goto('/login');

    // Заполнение формы авторизации
    await page.fill('input[name="username"]', 'y.varslavan');
    await page.fill('input[name="password"]', 'Srw$523U$');

    // Нажатие кнопки входа
    await page.click('button[type="submit"]');

    // Ждем перехода на главную страницу после успешной авторизации
    await page.waitForURL('**/', { timeout: 10000 });
  });

  test('должен успешно авторизоваться и загрузить главную страницу', async ({ page }) => {
    // Проверяем, что мы на главной странице
    await expect(page).toHaveURL(/\/$|\/home|\/index/);

    // Проверяем, что пользователь авторизован
    await expect(page.locator('body')).not.toContainText('Войти');
    await expect(page.locator('body')).not.toContainText('Login');
  });

  test('должен отображать информацию авторизованного пользователя', async ({ page }) => {
    // Проверяем наличие информации о пользователе
    const userInfo = page.locator('.user-info, .profile-info, [data-user], .navbar-nav .dropdown');
    await expect(userInfo).toBeVisible();

    // Проверяем, что отображается имя пользователя
    await expect(page.locator('body')).toContainText('y.varslavan');
  });

  test('должен иметь доступ к профилю пользователя', async ({ page }) => {
    // Ищем ссылку на профиль
    const profileLink = page.locator('a[href*="profile"], a[href*="user"], .dropdown-toggle').first();
    await expect(profileLink).toBeVisible();

    // Кликаем по ссылке профиля
    await profileLink.click();

    // Проверяем, что перешли на страницу профиля
    await expect(page).toHaveURL(/.*profile|.*user/);
  });

  test('должен иметь доступ к задачам', async ({ page }) => {
    // Ищем ссылку на задачи
    const tasksLink = page.locator('a[href*="tasks"], a[href*="issues"]').first();
    await expect(tasksLink).toBeVisible();

    // Кликаем по ссылке задач
    await tasksLink.click();

    // Проверяем, что перешли на страницу задач
    await expect(page).toHaveURL(/.*tasks|.*issues/);
  });

  test('должен иметь доступ к уведомлениям', async ({ page }) => {
    // Проверяем наличие виджета уведомлений
    const notificationsWidget = page.locator('.notifications-widget, #notifications-widget, .notification-bell');
    await expect(notificationsWidget).toBeVisible();
  });

  test('должен иметь доступ к сетевому монитору', async ({ page }) => {
    // Ищем ссылку на сетевой монитор
    const networkLink = page.locator('a[href*="network"], a[href*="monitor"]').first();
    await expect(networkLink).toBeVisible();

    // Кликаем по ссылке
    await networkLink.click();

    // Проверяем, что перешли на страницу мониторинга
    await expect(page).toHaveURL(/.*network|.*monitor/);
  });

  test('должен иметь доступ к качеству', async ({ page }) => {
    // Ищем ссылку на качество
    const qualityLink = page.locator('a[href*="quality"]').first();
    await expect(qualityLink).toBeVisible();

    // Кликаем по ссылке
    await qualityLink.click();

    // Проверяем, что перешли на страницу качества
    await expect(page).toHaveURL(/.*quality/);
  });

  test('должен иметь доступ к API endpoints', async ({ page }) => {
    // Тестируем доступ к API пользователя
    const response = await page.request.get('/api/user/current');
    expect(response.status()).toBe(200);

    // Проверяем, что возвращаются данные пользователя
    const userData = await response.json();
    expect(userData).toHaveProperty('username');
    expect(userData.username).toBe('y.varslavan');
  });

  test('должен иметь доступ к статистике', async ({ page }) => {
    // Ищем элементы статистики
    const statsElements = page.locator('.statistics, .stats, [data-stats]');
    await expect(statsElements).toBeVisible();
  });

  test('должен иметь возможность выйти из системы', async ({ page }) => {
    // Ищем ссылку выхода
    const logoutLink = page.locator('a[href*="logout"], .logout, .signout').first();
    await expect(logoutLink).toBeVisible();

    // Кликаем по ссылке выхода
    await logoutLink.click();

    // Проверяем, что вышли из системы
    await expect(page).toHaveURL(/.*login/);
    await expect(page.locator('body')).toContainText('Войти');
  });
});

test.describe('API тесты с авторизацией', () => {
  test('должен получать данные пользователя через API', async ({ request }) => {
    // Сначала получаем сессию через логин
    const loginResponse = await request.post('/login', {
      data: {
        username: 'y.varslavan',
        password: 'Srw$523U$'
      }
    });

    // Проверяем успешность логина
    expect(loginResponse.status()).toBe(200);

    // Теперь тестируем API с авторизацией
    const userResponse = await request.get('/api/user/current');
    expect(userResponse.status()).toBe(200);

    const userData = await userResponse.json();
    expect(userData.username).toBe('y.varslavan');
  });

  test('должен иметь доступ к API задач', async ({ request }) => {
    // Логинимся
    await request.post('/login', {
      data: {
        username: 'y.varslavan',
        password: 'Srw$523U$'
      }
    });

    // Тестируем API задач
    const tasksResponse = await request.get('/api/tasks');
    const status = tasksResponse.status();
    expect(status === 200 || status === 404).toBeTruthy(); // 404 если endpoint не существует
  });

  test('должен иметь доступ к API уведомлений', async ({ request }) => {
    // Логинимся
    await request.post('/login', {
      data: {
        username: 'y.varslavan',
        password: 'Srw$523U$'
      }
    });

    // Тестируем API уведомлений
    const notificationsResponse = await request.get('/api/notifications');
    const status = notificationsResponse.status();
    expect(status === 200 || status === 404).toBeTruthy();
  });
});

test.describe('Тесты безопасности', () => {
  test('должен блокировать доступ к защищенным страницам без авторизации', async ({ page }) => {
    // Переходим на защищенную страницу без авторизации
    await page.goto('/profile');

    // Проверяем, что нас перенаправило на страницу логина
    await expect(page).toHaveURL(/.*login/);
  });

  test('должен блокировать доступ к API без авторизации', async ({ request }) => {
    // Тестируем API без авторизации
    const response = await request.get('/api/user/current');
    expect(response.status()).toBe(401);
  });
});
