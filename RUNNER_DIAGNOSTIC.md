# 🔧 Диагностика GitLab Runner - Pipeline застрял в Pending

## 🚨 Проблема
Pipeline #3461 застрял в состоянии **"Pending"** после исправления конфигурации.

## 📋 Проверки для выполнения:

### 1. Проверить статус runner'а
В GitLab перейдите: **Settings → CI/CD → Runners**

Убедитесь что `linux_helpdesk_runner`:
- ✅ **Статус**: `active` (зеленый кружок)
- ✅ **Last contact**: недавнее время
- ✅ **Jobs**: не превышает лимит concurrent jobs

### 2. Проверить теги runner'а
Убедитесь что у runner'а есть тег `linux`:
- Теги должны быть: `docker`, `linux`
- Или добавьте тег `linux` если его нет

### 3. Проверить на сервере runner'а
SSH на сервер где установлен runner и выполните:

```bash
# Проверить статус GitLab Runner
sudo systemctl status gitlab-runner

# Проверить логи runner'а
sudo journalctl -u gitlab-runner -f

# Проверить конфигурацию runner'а
sudo gitlab-runner list

# Перезапустить runner если нужно
sudo systemctl restart gitlab-runner
```

## 🔧 Быстрые решения:

### Решение 1: Добавить fallback теги
В `.gitlab-ci.yml` добавьте альтернативные теги:

```yaml
validate_syntax:
  stage: validate
  tags:
    - linux
    - docker  # fallback
    - shell   # fallback
```

### Решение 2: Убрать теги полностью (временно)
Попробуйте убрать все теги из одного job для теста:

```yaml
validate_syntax:
  stage: validate
  # tags:
  #   - linux
  script:
    - echo "Тест без тегов"
```

### Решение 3: Использовать shared runners
Временно включите shared runners:
- **Settings → CI/CD → Runners**
- **Enable shared runners** = ON

## 🚀 Альтернативное решение - Docker runner

Если shell runner не работает, можно настроить Docker:

### На сервере runner'а:
```bash
# Установить Docker
sudo dnf install -y docker
sudo systemctl enable --now docker

# Добавить пользователя gitlab-runner в группу docker
sudo usermod -aG docker gitlab-runner

# Перезапустить runner
sudo systemctl restart gitlab-runner
```

## 📊 Диагностические команды

### На сервере GitLab Runner:
```bash
# Подробные логи
sudo gitlab-runner --debug run

# Проверить регистрацию
sudo gitlab-runner verify

# Показать конфигурацию
sudo cat /etc/gitlab-runner/config.toml
```

## ✅ Ожидаемый результат после исправления:
- Pipeline должен изменить статус с "Pending" на "Running"
- Jobs должны начать выполнение на runner'е
- В логах runner'а появятся сообщения о получении jobs

## 🆘 Если ничего не помогло:
1. **Создайте новый runner** с правильной конфигурацией
2. **Используйте shared runners** для деплоя
3. **Измените executor** на `docker` вместо `shell`

---

**Следующий шаг**: Проверьте статус runner'а в GitLab interface и выполните диагностику на сервере!
