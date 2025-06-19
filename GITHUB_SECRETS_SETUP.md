# 🔐 Настройка секретов GitHub Actions для деплоя

## Проблема
GitHub Actions workflow падает с ошибкой:
```
Error: missing server host
```

Это происходит потому, что не настроены секреты для SSH подключения к серверу.

## Решение

### 1. Добавление секретов в GitHub

1. Перейдите в ваш репозиторий на GitHub
2. Нажмите **Settings** (в верхнем меню репозитория)
3. В левом меню выберите **Secrets and variables** → **Actions**
4. Нажмите **New repository secret**

### 2. Необходимые секреты

Добавьте следующие секреты:

| Название | Описание | Пример |
|----------|----------|---------|
| `HOST` | IP адрес или домен сервера | `192.168.1.100` или `myserver.com` |
| `USERNAME` | Имя пользователя SSH | `ubuntu`, `root`, `deploy` |
| `KEY` | Приватный SSH ключ | Содержимое файла `~/.ssh/id_rsa` |
| `PORT` | Порт SSH | `22` (по умолчанию) |

### 3. Получение SSH ключа

#### На Windows:
```bash
# Генерация нового ключа (если нет)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Просмотр приватного ключа
type %USERPROFILE%\.ssh\id_rsa
```

#### На Linux/Mac:
```bash
# Генерация нового ключа (если нет)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Просмотр приватного ключа
cat ~/.ssh/id_rsa
```

### 4. Настройка сервера

На вашем сервере добавьте публичный ключ:

```bash
# Создание директории (если нет)
mkdir -p ~/.ssh

# Добавление публичного ключа
echo "ваш_публичный_ключ" >> ~/.ssh/authorized_keys

# Установка правильных прав
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 5. Включение деплоя

После настройки секретов, раскомментируйте секцию `deploy` в файле `.github/workflows/deploy.yml`:

```yaml
# Удалите комментарии (#) перед этими строками:
deploy:
  needs: test-dependencies
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main'
  name: Deploy to Production

  steps:
  - uses: actions/checkout@v4

  - name: Deploy to server
    uses: appleboy/ssh-action@v1.0.3
    # ... остальная конфигурация
```

## Тестирование подключения

Проверьте SSH подключение локально:

```bash
ssh -i ~/.ssh/id_rsa username@your_server_ip -p 22
```

## Альтернативные варианты

### Вариант 1: Использование пароля (менее безопасно)
Добавьте секрет `PASSWORD` вместо `KEY`:

```yaml
- name: Deploy to server
  uses: appleboy/ssh-action@v1.0.3
  with:
    host: ${{ secrets.HOST }}
    username: ${{ secrets.USERNAME }}
    password: ${{ secrets.PASSWORD }}
    port: ${{ secrets.PORT }}
```

### Вариант 2: Локальный деплой
Если сервер не готов, можно использовать только тестирование зависимостей (текущая настройка).

## Проверка статуса

После настройки секретов:

1. Сделайте коммит в ветку `main`
2. Проверьте статус workflow в разделе **Actions**
3. Убедитесь, что job `test-dependencies` проходит успешно
4. После раскомментирования - проверьте job `deploy`

---
*Создано: 2024-12-20*
*Статус: Deploy временно отключен до настройки секретов*
