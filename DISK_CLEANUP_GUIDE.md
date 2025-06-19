# 💾 Руководство по очистке диска и мониторингу

## 🚨 Экстренная очистка диска

### Немедленные действия при 95%+ заполнении:

```bash
# 1. Остановка runner
sudo pkill -f Runner.Listener

# 2. Очистка главных виновников
sudo truncate -s 0 /var/www/flask_helpdesk/app_err.log    # 3.8GB
sudo rm -rf /home/yvarslavan/actions-runner               # 1.8GB

# 3. Очистка runner кэша
sudo rm -rf /home/github-actions/actions-runner/_work/*
sudo rm -rf /home/github-actions/.cache/pip/*
sudo rm -rf /home/github-actions/actions-runner/_diag/*

# 4. Очистка системных логов
sudo journalctl --vacuum-time=6h
sudo find /var/log -name "*.log" -mtime +3 -delete
sudo find /tmp -mtime +0 -delete

# 5. Проверка результата
df -h | grep root
```

## 🛡️ Предотвращение заполнения диска

### 1. Настройка ротации логов Flask:

```bash
sudo tee /etc/logrotate.d/flask_helpdesk << EOF
/var/www/flask_helpdesk/*.log {
    daily
    rotate 7
    compress
    maxsize 100M
    missingok
    notifempty
    create 644 www-data www-data
}
EOF

# Проверка конфигурации
sudo logrotate -d /etc/logrotate.d/flask_helpdesk

# Принудительная ротация
sudo logrotate -f /etc/logrotate.d/flask_helpdesk
```

### 2. Мониторинг диска:

```bash
# Ежедневная проверка (добавить в crontab)
0 2 * * * /home/yvarslavan/disk_monitoring.sh

# Или запуск вручную
./disk_monitoring.sh
```

### 3. Настройка Flask логирования:

Добавьте в конфигурацию Flask:

```python
import logging
from logging.handlers import RotatingFileHandler

# Ограничение размера логов
handler = RotatingFileHandler(
    'app_err.log',
    maxBytes=50*1024*1024,  # 50MB max
    backupCount=5
)
handler.setLevel(logging.ERROR)
app.logger.addHandler(handler)
```

## 📊 Регулярные проверки

### Поиск больших файлов:
```bash
# Файлы больше 100MB
find / -type f -size +100M -ls 2>/dev/null

# Папки с большим содержимым
sudo du -h / 2>/dev/null | sort -rh | head -20
```

### Анализ использования диска:
```bash
# Общая информация
df -h

# Детальный анализ по папкам
sudo du -sh /var/www/flask_helpdesk/
sudo du -sh /home/github-actions/
sudo du -sh /var/log/
```

## 🔄 Возврат к self-hosted runner

После освобождения 4GB+ места:

```bash
# 1. Проверка свободного места
df -h | grep root

# 2. Изменение workflow
# Заменить в .github/workflows/deploy.yml:
# runs-on: ubuntu-latest → runs-on: self-hosted

# 3. Запуск runner
cd /home/github-actions/actions-runner
sudo -u github-actions ./run.sh

# 4. Мониторинг
watch -n 30 'df -h | grep root'
```

## ⚠️ Признаки проблем

### Когда остановить runner:
- Свободно менее 1GB
- Заполнение более 95%
- Большие лог файлы (>100MB)

### Автоматические действия:
- Остановка runner при 95%
- Очистка кэша при 90%
- Ротация логов при 50MB+

## 📈 Результаты очистки

**До очистки:**
- 469MB свободно (99% заполнено)
- app_err.log: 3.8GB
- Дубли runner: 1.8GB

**После очистки:**
- 2.2GB свободно (91% заполнено)
- Освобождено: 1.7GB+

**Цель:**
- 8GB+ свободно (68% заполнено)
- Стабильная работа runner
- Контролируемый рост логов
