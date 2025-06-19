# 🔄 Возврат к Self-Hosted Runner

## После исправления Node.js проблемы:

### 1. Проверьте что runner работает:
```bash
ps aux | grep Runner.Listener
tail -5 /home/github-actions/actions-runner/runner.log
```

### 2. Измените workflow обратно:
В файле `.github/workflows/deploy.yml` замените:
```yaml
runs-on: ubuntu-latest  # 🔧 Временно: переустанавливается self-hosted runner
```
на:
```yaml
runs-on: self-hosted  # ✅ Node.js исправлен - возврат к self-hosted runner
```

### 3. Создайте коммит:
```bash
git add .github/workflows/deploy.yml
git commit -m "🚀 Возврат к self-hosted runner - Node.js проблема исправлена"
git push origin main
```

### 4. Проверьте новый workflow:
- Должен запуститься на self-hosted runner
- Время выполнения: ~2-4 минуты
- Показать мониторинг диска: 69% заполнения (7.5GB свободно)

## Преимущества после возврата:
- ⚡ Быстрое выполнение (в 2-3 раза быстрее)
- 🔗 Прямой доступ к серверу деплоя
- 💾 Стабильное использование диска с мониторингом
- 🎯 Полный контроль над процессом CI/CD
