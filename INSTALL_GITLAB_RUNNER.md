# 🔧 Установка GitLab Runner на Red Hat сервер

## 🚨 Проблема
На сервере `its.tez-tour.com` не установлен GitLab Runner, поэтому pipeline застрял в "Pending".

## 📋 Установка GitLab Runner на Red Hat

### 1. Подключаемся к серверу:
```bash
ssh deploy@its.tez-tour.com
# или
ssh deploy@10.7.74.252
```

### 2. Добавляем официальный репозиторий GitLab:
```bash
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh" | sudo bash
```

### 3. Устанавливаем GitLab Runner:
```bash
sudo dnf install gitlab-runner -y
```

### 4. Проверяем установку:
```bash
sudo systemctl status gitlab-runner
sudo systemctl enable gitlab-runner
sudo systemctl start gitlab-runner
```

### 5. Регистрируем runner в GitLab:

**Получите токен регистрации:**
- В GitLab: **Settings → CI/CD → Runners**
- Нажмите **"New project runner"**
- Скопируйте **registration token**

**Выполните регистрацию:**
```bash
sudo gitlab-runner register
```

**Введите данные:**
- **GitLab instance URL**: `https://gitlab.com` (или ваш GitLab URL)
- **Registration token**: `[ваш токен из GitLab]`
- **Description**: `Red Hat Flask Helpdesk Runner`
- **Tags**: `linux,redhat,shell`
- **Executor**: `shell`

### 6. Проверяем регистрацию:
```bash
sudo gitlab-runner list
sudo gitlab-runner verify
```

## 🚀 Быстрое решение - Shared Runners

**Если не хотите устанавливать runner, используйте shared runners:**

1. В GitLab: **Settings → CI/CD → Runners**
2. **Enable shared runners for this project** = **ON**
3. Измените `.gitlab-ci.yml` - уберите все теги:

```yaml
validate_syntax:
  stage: validate
  # Убираем теги для shared runners
  script:
    - echo "🔍 Проверка синтаксиса Python..."
```

## 📋 Настройка после установки

### Дать права deploy пользователю:
```bash
sudo usermod -aG docker deploy
sudo usermod -aG gitlab-runner deploy
```

### Настроить SSH для runner'а:
```bash
# Копируем SSH ключ для runner'а
sudo mkdir -p /home/gitlab-runner/.ssh
sudo cp /home/deploy/.ssh/authorized_keys /home/gitlab-runner/.ssh/
sudo chown -R gitlab-runner:gitlab-runner /home/gitlab-runner/.ssh
sudo chmod 700 /home/gitlab-runner/.ssh
sudo chmod 600 /home/gitlab-runner/.ssh/authorized_keys
```

## ✅ Проверка работы

После установки и регистрации:
1. **Коммитните изменения** в GitLab
2. **Pipeline должен запуститься** автоматически
3. **Проверьте логи**: `sudo journalctl -u gitlab-runner -f`

---

## 🔥 БЫСТРЫЙ СТАРТ (без установки runner'а):

**Просто включите shared runners в GitLab:**
1. **Settings → CI/CD → Runners**
2. **"Enable shared runners"** = ON
3. Pipeline запустится на GitLab shared infrastructure

**Выберите один из вариантов и сообщите результат!**
