/**
 * Модуль для мониторинга сетевого соединения
 */
(function() {
    // Глобальные переменные
    let pingChart = null;
    let currentTarget = 'finesse';
    let updateInterval = null;
    let pingHistory = {};

    // Настройки
    const updateIntervalMs = 10000; // 10 секунд

    /**
     * Получает текущий статус сетевого соединения
     */
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'ok') {
                updateStatusCards(data.targets);
                return data.targets;
            } else {

                return null;
            }
        } catch (error) {

            showError('Не удалось получить статус соединения: ' + error.message);
            return null;
        }
    }

    /**
     * Получает историю пингов для указанной цели
     */
    async function fetchPingHistory(target = currentTarget) {
        try {
            const response = await fetch(`/api/ping-history?target=${target}&limit=50`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.history) {
                pingHistory[target] = data.history;
                updateChart(data.history);
                return data.history;
            } else {

                return [];
            }
        } catch (error) {

            showError('Не удалось получить историю пингов: ' + error.message);
            return [];
        }
    }

    /**
     * Выполняет активный пинг и обновляет данные
     */
    async function performPing() {
        try {
            const response = await fetch(`/api/ping?target=${currentTarget}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const pingResult = await response.json();

            // Обновляем данные после получения нового пинга
            await fetchStatus();
            await fetchPingHistory(currentTarget);

            return pingResult;
        } catch (error) {

            return null;
        }
    }

    /**
     * Обновляет карточки состояния сетевого соединения
     */
    function updateStatusCards(targets) {
        const container = document.getElementById('statusCards');
        if (!container) return;

        container.innerHTML = '';

        for (const [targetName, targetData] of Object.entries(targets)) {
            const statusClass = targetData.status;
            const pingTime = targetData.time_ms;

            const card = document.createElement('div');
            card.className = `status-card ${statusClass}`;

            let statusText = '';
            switch (statusClass) {
                case 'excellent': statusText = 'Отличное'; break;
                case 'good': statusText = 'Хорошее'; break;
                case 'average': statusText = 'Среднее'; break;
                case 'poor': statusText = 'Плохое'; break;
                case 'disconnected': statusText = 'Соединение потеряно'; break;
                default: statusText = 'Неизвестно';
            }

            card.innerHTML = `
                <h3>
                    <span class="status-indicator ${statusClass} ${targetData.success ? 'pulse' : ''}"></span>
                    ${targetName.charAt(0).toUpperCase() + targetName.slice(1)}
                </h3>
                <div class="status-details">
                    <div class="ping-time">${pingTime > 0 ? pingTime + ' мс' : 'Нет связи'}</div>
                    <div>Статус: ${statusText}</div>
                </div>
                <div class="status-timestamp">
                    Обновлено: ${targetData.timestamp}
                </div>
            `;

            container.appendChild(card);
        }
    }

    /**
     * Обновляет график истории пингов
     */
    function updateChart(historyData) {
        const ctx = document.getElementById('pingChart');
        if (!ctx) return;

        // Подготавливаем данные
        const labels = historyData.map(item => {
            const date = new Date(item.timestamp.replace(' ', 'T'));
            return date.toLocaleTimeString();
        });

        const pingData = historyData.map(item => item.success ? item.time_ms : null);

        // Создаем или обновляем график
        if (pingChart) {
            pingChart.data.labels = labels;
            pingChart.data.datasets[0].data = pingData;
            pingChart.update();
        } else {
            pingChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Время отклика (мс)',
                        data: pingData,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: function(context) {
                            const value = context.dataset.data[context.dataIndex];
                            if (value === null) return '#6c757d';
                            if (value < 100) return '#28a745';
                            if (value < 200) return '#17a2b8';
                            if (value < 500) return '#ffc107';
                            return '#dc3545';
                        }
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    return value !== null ? `Пинг: ${value} мс` : 'Соединение потеряно';
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            min: 0,
                            title: {
                                display: true,
                                text: 'Время (мс)'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        }
                    }
                }
            });
        }
    }

    /**
     * Показывает сообщение об ошибке
     */
    function showError(message) {
        // Проверяем наличие SweetAlert2
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'error',
                title: 'Ошибка',
                text: message,
                timer: 5000,
                toast: true,
                position: 'top-end',
                showConfirmButton: false
            });
        } else {

            alert('Ошибка: ' + message);
        }
    }

    /**
     * Инициализация модуля
     */
    function init() {
        // Получаем начальные данные
        fetchStatus();
        fetchPingHistory();

        // Настраиваем кнопки выбора цели
        document.querySelectorAll('.target-button').forEach(button => {
            button.addEventListener('click', function() {
                const target = this.dataset.target;

                // Обновляем активную кнопку
                document.querySelectorAll('.target-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');

                // Обновляем цель и загружаем данные
                currentTarget = target;

                // Если у нас уже есть история для этой цели, используем её
                if (pingHistory[target]) {
                    updateChart(pingHistory[target]);
                } else {
                    fetchPingHistory(target);
                }
            });
        });

        // Настраиваем кнопку обновления
        const refreshButton = document.getElementById('refreshButton');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                const icon = this.querySelector('i');

                // Добавляем анимацию и блокируем кнопку
                icon.classList.add('fa-spin');
                this.classList.add('loading');
                this.disabled = true;

                // Выполняем пинг
                performPing().finally(() => {
                    // Убираем анимацию и разблокируем кнопку
                    setTimeout(() => {
                        icon.classList.remove('fa-spin');
                        this.classList.remove('loading');
                        this.disabled = false;
                    }, 500);
                });
            });
        }

        // Устанавливаем интервал автоматического обновления
        updateInterval = setInterval(performPing, updateIntervalMs);
    }

    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', init);

    // Очистка при скрытии/выгрузке страницы (BFCache-friendly)
    window.addEventListener('pagehide', function() {
        if (updateInterval) {
            clearInterval(updateInterval);
        }
    });

    // Экспортируем API для внешнего использования
    window.networkMonitor = {
        fetchStatus,
        fetchPingHistory,
        performPing,
        changeTarget: function(target) {
            if (target) {
                currentTarget = target;
                fetchPingHistory(target);
            }
        }
    };
})();
