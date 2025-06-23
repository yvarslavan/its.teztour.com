# ✅ ЧЕКЛИСТ ЗАПУСКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ

## 🚨 **НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ (5 минут):**

### 1. Настройка GitLab переменных
- [ ] Откройте GitLab проект → Settings → CI/CD → Variables
- [ ] Добавьте переменные:
  - [ ] `SSH_PRIVATE_KEY` - содержимое `~/.ssh/id_rsa`
  - [ ] `DEPLOY_HOST` - IP Ubuntu сервера
  - [ ] `DEPLOY_USER` - `yvarslavan`
  - [ ] `DEPLOY_PORT` - `22`

### 2. Запуск первого pipeline
- [ ] Выполните команды:
```bash
git add .
git commit -m "🚀 Service restored - ready for auto-deploy"
git push origin main
```
- [ ] Перейдите в GitLab → CI/CD → Pipelines
- [ ] Дождитесь завершения build_application
- [ ] Нажмите "Play" на deploy_to_server

### 3. Финализация на сервере
После успешного деплоя выполните на Ubuntu:
```bash
sudo systemctl daemon-reload
sudo systemctl restart flask-helpdesk
sudo systemctl status flask-helpdesk
```

## 🎯 **РЕЗУЛЬТАТ:**
- ✅ Автоматический деплой настроен
- ✅ Каждый push в main будет деплоиться автоматически
- ✅ Сервис работает стабильно

## 📞 **ЕСЛИ ПРОБЛЕМЫ:**
1. Проверьте логи GitLab Pipeline
2. Убедитесь в SSH доступе к серверу
3. Проверьте статус сервиса: `sudo systemctl status flask-helpdesk`

---
**Время выполнения: ~10 минут**
**Статус сервиса: ✅ Работает**
**Готовность к деплою: 🚀 100%**
