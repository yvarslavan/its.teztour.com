/**
 * Модуль для управления отображением статусов операторов Cisco Finesse
 * и сводкой очередей (CSQ Summary).
 */
(function () {
    const CSQ_DEFINITIONS = [
        {
            id: 'questions',
            name: 'RU-MSK-RETAIL-QUESTIONS',
            description: 'Вопросы клиентов',
            teamKeywords: ['RU-MSK-RETAIL'],
            agentKeywords: ['QUESTION', 'ВОПРОС', 'RETAIL'],
            callKeywords: ['QUESTION', 'ВОПРОС', 'ИНФО', 'КОНСУЛЬТ']
        },
        {
            id: 'purchase',
            name: 'RU-MSK-RETAIL-TOUR-PURCHASE',
            description: 'Покупка туров',
            teamKeywords: ['RU-MSK-RETAIL'],
            agentKeywords: ['PURCHASE', 'TOUR', 'ПРОДАЖ', 'ТУР'],
            callKeywords: ['PURCHASE', 'TOUR', 'ПОКУП', 'ПРОДАЖ', 'ТУР']
        }
    ];

    const WAITING_RESULT_CODES = new Set([0, 2, 3, 4, 5, 6]);
    const REFRESH_BUTTON_IDS = ['refreshAgentsBtn', 'refreshCsqBtn', 'refreshCsqFooterBtn'];

    let agentsData = [];
    let callsDataForQueues = [];
    let callsDataDate = '';
    let lastUpdateTime = null;
    let isLoading = false;

    const queueWaitStartedAt = new Map();
    const expandedQueues = new Set();

    function isFinesseAuthenticated() {
        return Boolean(window.finesseAuth && window.finesseAuth.isAuthenticated);
    }

    function setRefreshButtonsLoading(loading) {
        REFRESH_BUTTON_IDS.forEach((id) => {
            const button = document.getElementById(id);
            if (button) {
                button.classList.toggle('loading', loading);
            }
        });
    }

    function setPanelsVisible(isVisible) {
        const agentsPanel = document.getElementById('agentsPanelContainer');
        const csqPanel = document.getElementById('csqSummaryPanel');

        if (agentsPanel) {
            agentsPanel.style.display = isVisible ? '' : 'none';
        }

        if (csqPanel) {
            csqPanel.style.display = isVisible ? '' : 'none';
        }
    }

    function updateRefreshTimestamps(formattedTime) {
        const agentRefreshStatus = document.querySelector('#agentsPanelContainer .refresh-status');
        if (agentRefreshStatus) {
            agentRefreshStatus.textContent = `Обновлено: ${formattedTime}`;
        }

        const queueUpdatedAt = document.getElementById('csqUpdatedAt');
        if (queueUpdatedAt) {
            queueUpdatedAt.textContent = `Обновлено: ${formattedTime}`;
        }
    }

    async function fetchAgentStatuses() {
        isLoading = true;
        updateStatusMessage('Загрузка статусов операторов...', 'loading');
        setRefreshButtonsLoading(true);
        renderCsqSummary();

        try {
            if (!isFinesseAuthenticated()) {
                updateStatusMessage('Выполните вход Finesse для просмотра статусов', 'info');
                return;
            }

            const response = await fetch('/finesse/agents/status', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                const errorMessage = `Ошибка при получении статусов (${response.status})`;
                if (response.status === 401) {
                    showVpnNotification(
                        'Ошибка авторизации',
                        'У вас нет прав на просмотр статусов операторов в Cisco Finesse. Обратитесь к администратору.'
                    );
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            if (!Array.isArray(data)) {
                if (data && data.success === false) {
                    throw new Error(data.error || 'Ошибка сервера при получении статусов');
                }
                throw new Error('Некорректный формат ответа Finesse API');
            }

            agentsData = data;
            lastUpdateTime = new Date();

            displayAgentStatuses(agentsData);
            renderCsqSummary();

            const limitedAccess = response.headers.get('X-Finesse-Limited-Access') === '1';
            const formattedTime = lastUpdateTime.toLocaleTimeString('ru-RU');

            if (limitedAccess) {
                updateStatusMessage('Ограниченный доступ Finesse: отображается только ваш статус оператора', 'info');
            } else {
                updateStatusMessage(`Данные обновлены в ${formattedTime}`, 'success');
            }

            updateRefreshTimestamps(formattedTime);
        } catch (error) {
            const errorText = error && error.message ? error.message : 'Неизвестная ошибка';
            showError(`Ошибка при получении статусов: ${errorText}`);

            if (errorText.includes('Failed to fetch') || errorText.includes('Network') || errorText.includes('сет')) {
                showVpnNotification();
            }
        } finally {
            isLoading = false;
            setRefreshButtonsLoading(false);
            renderCsqSummary();
        }
    }

    function displayAgentStatuses(agents) {
        const container = document.getElementById('agentsContainer');
        if (!container) {
            return;
        }

        container.innerHTML = '';

        if (!Array.isArray(agents) || agents.length === 0) {
            container.innerHTML = '<div class="empty-message">Нет доступных данных об операторах</div>';
            return;
        }

        const agentsByTeam = {};
        agents.forEach((agent) => {
            const team = agent.team || 'Без команды';
            if (!agentsByTeam[team]) {
                agentsByTeam[team] = [];
            }
            agentsByTeam[team].push(agent);
        });

        Object.keys(agentsByTeam)
            .sort()
            .forEach((team) => {
                const teamGroup = document.createElement('div');
                teamGroup.className = 'team-group';

                const teamHeader = document.createElement('div');
                teamHeader.className = 'team-header';
                teamHeader.innerHTML = `
                    ${escapeHtml(team)}
                    <i class="fas fa-chevron-down team-accordion-icon"></i>
                `;
                teamGroup.appendChild(teamHeader);

                const teamContainer = document.createElement('div');
                teamContainer.className = 'team-container';
                teamContainer.style.maxHeight = '0';
                teamContainer.style.overflow = 'hidden';
                teamContainer.style.transition = 'max-height 0.3s ease-out';

                teamHeader.addEventListener('click', function () {
                    teamGroup.classList.toggle('active');
                    const icon = this.querySelector('.team-accordion-icon');

                    if (teamGroup.classList.contains('active')) {
                        teamContainer.style.maxHeight = `${teamContainer.scrollHeight}px`;
                        icon.classList.remove('fa-chevron-down');
                        icon.classList.add('fa-chevron-up');
                    } else {
                        teamContainer.style.maxHeight = '0';
                        icon.classList.remove('fa-chevron-up');
                        icon.classList.add('fa-chevron-down');
                    }
                });

                agentsByTeam[team].forEach((agent) => {
                    const card = document.createElement('div');
                    card.className = 'agent-card';

                    const statusClass = getAgentStatusClass(agent.status, true);
                    const statusText = getAgentStatusLabel(agent.status);

                    card.innerHTML = `
                        <div class="agent-name">
                            <span class="agent-status ${statusClass}"></span>
                            ${escapeHtml(getAgentDisplayName(agent))}
                        </div>
                        <div class="agent-details">
                            <div class="agent-status-text">${escapeHtml(statusText)}</div>
                            <div class="agent-phone">
                                <i class="fas fa-phone"></i> ${escapeHtml(agent.extension || 'не указан')}
                            </div>
                        </div>
                    `;

                    teamContainer.appendChild(card);
                });

                teamGroup.appendChild(teamContainer);
                container.appendChild(teamGroup);
            });
    }

    function updateStatusMessage(message, type = 'info') {
        const statusElement = document.getElementById('agentsStatusMessage');
        if (!statusElement) {
            return;
        }

        statusElement.classList.remove('status-error', 'status-success', 'status-loading', 'status-info');
        statusElement.classList.add(`status-${type}`);
        statusElement.textContent = message;
        statusElement.style.display = 'block';
    }

    function showError(message) {
        updateStatusMessage(message, 'error');
    }

    function createAgentsUI() {
        const container = document.createElement('div');
        container.className = 'supervisor-panel accordion-panel';
        container.id = 'agentsPanelContainer';

        if (!isFinesseAuthenticated()) {
            container.style.display = 'none';
        }

        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.innerHTML = `
            <span>Список операторов Cisco Finesse</span>
            <i class="fas fa-chevron-down accordion-icon"></i>
        `;
        container.appendChild(header);

        const content = document.createElement('div');
        content.className = 'accordion-content';
        container.appendChild(content);

        const statusMessage = document.createElement('div');
        statusMessage.id = 'agentsStatusMessage';
        statusMessage.className = 'status-message';
        statusMessage.style.display = 'none';
        content.appendChild(statusMessage);

        const agentsContainer = document.createElement('div');
        agentsContainer.id = 'agentsContainer';
        agentsContainer.className = 'agents-container';
        content.appendChild(agentsContainer);

        const refreshContainer = document.createElement('div');
        refreshContainer.className = 'refresh-container';
        content.appendChild(refreshContainer);

        const refreshStatus = document.createElement('div');
        refreshStatus.className = 'refresh-status';
        refreshStatus.textContent = 'Данные не загружены';
        refreshContainer.appendChild(refreshStatus);

        const refreshButton = document.createElement('button');
        refreshButton.id = 'refreshAgentsBtn';
        refreshButton.className = 'refresh-button';
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshButton.setAttribute('title', 'Обновить статусы операторов');
        refreshButton.addEventListener('click', function () {
            if (!isLoading) {
                fetchAgentStatuses();
            }
        });
        refreshContainer.appendChild(refreshButton);

        header.addEventListener('click', function () {
            container.classList.toggle('active');
        });

        const contentArea = document.querySelector('.container');
        if (contentArea) {
            const callsPanel = document.querySelector('.calls-panel');
            if (callsPanel) {
                contentArea.insertBefore(container, callsPanel);
            } else {
                contentArea.appendChild(container);
            }
        } else {
            document.body.appendChild(container);
        }

        container.classList.add('active');
        return container;
    }

    function createCsqSummaryUI() {
        const panel = document.createElement('section');
        panel.id = 'csqSummaryPanel';
        panel.className = 'csq-summary-panel';

        if (!isFinesseAuthenticated()) {
            panel.style.display = 'none';
        }

        panel.innerHTML = `
            <div class="csq-summary-header" id="csqSummaryHeader">
                <div class="csq-summary-title-wrap">
                    <span class="csq-summary-title-icon"><i class="fas fa-phone-alt"></i></span>
                    <div class="csq-summary-title-block">
                        <div class="csq-summary-title-row">
                            <h3 class="csq-summary-title">Очереди вызовов</h3>
                            <span class="csq-source-badge">Cisco Finesse · RU-MSK</span>
                        </div>
                    </div>
                </div>
                <div class="csq-summary-controls">
                    <button type="button" class="csq-header-btn" id="csqSettingsBtn" title="Настройки"><i class="fas fa-ellipsis-h"></i></button>
                    <button type="button" class="csq-header-btn" id="csqCollapseBtn" title="Свернуть/развернуть"><i class="fas fa-chevron-up"></i></button>
                    <button type="button" class="csq-header-btn csq-refresh-button" id="refreshCsqBtn" title="Обновить очереди"><i class="fas fa-sync-alt"></i></button>
                </div>
            </div>
            <div class="csq-summary-content">
                <div class="csq-table-scroll">
                    <table class="csq-summary-table" aria-label="Сводка очередей вызовов">
                        <thead>
                            <tr>
                                <th>Название очереди</th>
                                <th>Ожидают</th>
                                <th>В системе</th>
                                <th>Разговаривают</th>
                                <th>Готовы</th>
                                <th>Не готовы</th>
                                <th>После звонка</th>
                                <th>Зарезервированы</th>
                                <th>Дольше всего ждёт</th>
                            </tr>
                        </thead>
                        <tbody id="csqSummaryBody"></tbody>
                    </table>
                </div>
                <div class="csq-summary-footer">
                    <div class="csq-summary-updated" id="csqUpdatedAt">Обновлено: --:--:--</div>
                    <div class="csq-summary-footer-right">
                        <span class="csq-summary-api-label">Cisco Finesse API</span>
                        <button type="button" class="csq-footer-refresh-button csq-refresh-button" id="refreshCsqFooterBtn" title="Обновить очереди">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        const contentArea = document.querySelector('.container');
        if (contentArea) {
            const callsPanel = document.querySelector('.calls-panel');
            if (callsPanel) {
                contentArea.insertBefore(panel, callsPanel);
            } else {
                contentArea.appendChild(panel);
            }
        } else {
            document.body.appendChild(panel);
        }

        const header = document.getElementById('csqSummaryHeader');
        const settingsBtn = document.getElementById('csqSettingsBtn');
        const collapseBtn = document.getElementById('csqCollapseBtn');
        const refreshBtn = document.getElementById('refreshCsqBtn');
        const footerRefreshBtn = document.getElementById('refreshCsqFooterBtn');

        if (settingsBtn) {
            settingsBtn.addEventListener('click', (event) => {
                event.stopPropagation();
            });
        }

        if (collapseBtn) {
            collapseBtn.addEventListener('click', function (event) {
                event.stopPropagation();
                toggleCsqPanelCollapse();
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', function (event) {
                event.stopPropagation();
                if (!isLoading) {
                    fetchAgentStatuses();
                }
            });
        }

        if (footerRefreshBtn) {
            footerRefreshBtn.addEventListener('click', function () {
                if (!isLoading) {
                    fetchAgentStatuses();
                }
            });
        }

        if (header) {
            header.addEventListener('click', function () {
                toggleCsqPanelCollapse();
            });
        }

        panel.classList.remove('is-collapsed');
        renderCsqSummary();
        return panel;
    }

    function toggleCsqPanelCollapse(forceCollapsed) {
        const panel = document.getElementById('csqSummaryPanel');
        if (!panel) {
            return;
        }

        const collapsed = panel.classList.contains('is-collapsed');
        const shouldCollapse = typeof forceCollapsed === 'boolean' ? forceCollapsed : !collapsed;

        panel.classList.toggle('is-collapsed', shouldCollapse);

        const icon = panel.querySelector('#csqCollapseBtn i');
        if (icon) {
            icon.classList.toggle('fa-chevron-up', !shouldCollapse);
            icon.classList.toggle('fa-chevron-down', shouldCollapse);
        }
    }

    function getCurrentCallLogDate() {
        const datePicker = document.getElementById('callLogDatePicker');
        if (datePicker && datePicker.value) {
            return datePicker.value;
        }

        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }

    function extractCallsFromDomTable() {
        const rows = document.querySelectorAll('.calls-table tbody tr');
        if (!rows.length) {
            return [];
        }

        const calls = [];
        rows.forEach((row) => {
            if (row.querySelector('.no-calls-message') || row.querySelector('.error-message')) {
                return;
            }

            if (!row.cells || row.cells.length < 5) {
                return;
            }

            const operatorCell = row.cells[2];
            const operatorElement = operatorCell.querySelector('.operator-name-text');
            const operatorName = operatorElement ? operatorElement.textContent.trim() : operatorCell.textContent.trim();

            const resultBadge = row.cells[3].querySelector('.call-result-badge');
            let resultCode = null;
            if (resultBadge) {
                if (resultBadge.classList.contains('result-success')) {
                    resultCode = 1;
                } else if (resultBadge.classList.contains('result-dropped')) {
                    resultCode = 2;
                } else if (resultBadge.classList.contains('result-no-internet')) {
                    resultCode = 3;
                } else if (resultBadge.classList.contains('result-failed')) {
                    resultCode = 0;
                }
            }

            calls.push({
                operator: operatorName,
                time: row.cells[1].textContent.trim(),
                call_type_text: row.cells[4].textContent.trim(),
                result: resultCode
            });
        });

        return calls;
    }

    function handleCallLogUpdated(event) {
        const detail = event && event.detail ? event.detail : {};
        callsDataForQueues = Array.isArray(detail.calls) ? detail.calls : [];
        callsDataDate = detail.date || getCurrentCallLogDate();
        renderCsqSummary();
    }

    function renderCsqSummary() {
        const tbody = document.getElementById('csqSummaryBody');
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';

        if (isLoading && agentsData.length === 0) {
            tbody.innerHTML = `
                <tr class="csq-loading-row">
                    <td colspan="9"><i class="fas fa-spinner fa-spin"></i> Загрузка данных очередей...</td>
                </tr>
            `;
            return;
        }

        const now = new Date();

        CSQ_DEFINITIONS.forEach((queueDef) => {
            const metrics = getQueueMetrics(queueDef, now);
            const isExpanded = expandedQueues.has(queueDef.id);

            const mainRow = document.createElement('tr');
            mainRow.className = 'csq-main-row';
            if (isExpanded) {
                mainRow.classList.add('is-expanded');
            }

            const waitingCellClass = metrics.counts.waiting > 0 ? 'has-waiting' : '';
            const waitingTimerClass = metrics.waitSeconds > 30
                ? 'is-critical'
                : (metrics.waitSeconds > 0 ? 'is-active' : '');

            mainRow.innerHTML = `
                <td>
                    <div class="csq-queue-name">${escapeHtml(queueDef.name)}</div>
                    <div class="csq-queue-description">${escapeHtml(queueDef.description)}</div>
                </td>
                <td class="csq-waiting-cell ${waitingCellClass}">
                    <div class="csq-waiting-value-row">
                        ${metrics.counts.waiting > 0 ? '<span class="csq-waiting-dot"></span>' : ''}
                        <span class="csq-metric-value">${metrics.counts.waiting}</span>
                    </div>
                    <div class="csq-waiting-timer ${waitingTimerClass}">${formatDuration(metrics.waitSeconds)}</div>
                </td>
                <td><span class="csq-metric-value">${metrics.counts.inSystem}</span></td>
                <td><span class="csq-metric-value">${metrics.counts.talking}</span></td>
                <td>${renderDotMetric(metrics.counts.ready, 'ready')}</td>
                <td>${renderDotMetric(metrics.counts.notReady, 'not-ready')}</td>
                <td><span class="csq-metric-value">${metrics.counts.afterCall}</span></td>
                <td><span class="csq-metric-value">${metrics.counts.reserved}</span></td>
                <td>
                    <div class="csq-longest-cell">
                        <span class="csq-longest-value ${waitingTimerClass}">${formatDuration(metrics.waitSeconds)}</span>
                        <i class="fas fa-chevron-${isExpanded ? 'up' : 'down'} csq-row-chevron"></i>
                    </div>
                </td>
            `;

            mainRow.addEventListener('click', function () {
                toggleQueueRow(queueDef.id);
            });

            const detailsRow = document.createElement('tr');
            detailsRow.className = 'csq-details-row';
            if (isExpanded) {
                detailsRow.classList.add('is-open');
            }
            detailsRow.innerHTML = `
                <td colspan="9">
                    <div class="csq-details-drawer">
                        ${buildQueueOperatorsHtml(metrics)}
                    </div>
                </td>
            `;

            tbody.appendChild(mainRow);
            tbody.appendChild(detailsRow);
        });
    }

    function toggleQueueRow(queueId) {
        if (expandedQueues.has(queueId)) {
            expandedQueues.delete(queueId);
        } else {
            expandedQueues.add(queueId);
        }

        renderCsqSummary();
    }

    function renderDotMetric(value, type) {
        const dotClass = type === 'ready' ? 'dot-ready' : 'dot-not-ready';
        if (value > 0) {
            return `
                <span class="csq-dot-metric">
                    <span class="csq-dot ${dotClass}"></span>
                    <span class="csq-metric-value">${value}</span>
                </span>
            `;
        }

        return `<span class="csq-metric-value">${value}</span>`;
    }

    function getQueueMetrics(queueDef, now) {
        const queueOperators = getQueueOperators(queueDef);
        const queueCalls = getQueueCalls(queueDef);
        const callsByOperator = buildCallsByOperator(queueCalls);

        const counts = {
            waiting: 0,
            inSystem: 0,
            talking: 0,
            ready: 0,
            notReady: 0,
            afterCall: 0,
            reserved: 0
        };

        queueOperators.forEach((agent) => {
            const status = normalizeText(agent.status);

            if (isAgentInSystem(status)) {
                counts.inSystem += 1;
            }

            if (status === 'TALKING') {
                counts.talking += 1;
            }

            if (status === 'READY') {
                counts.ready += 1;
            }

            if (status === 'NOT_READY') {
                counts.notReady += 1;
            }

            if (status === 'WORK' || status === 'WORK_READY' || status === 'AFTER_CALL_WORK') {
                counts.afterCall += 1;
            }

            if (status === 'RESERVED') {
                counts.reserved += 1;
            }
        });

        const waitingState = calculateWaitingState(queueDef.id, queueCalls, counts, now);
        counts.waiting = waitingState.waiting;

        return {
            queueDef,
            operators: queueOperators,
            counts,
            waitSeconds: waitingState.waitSeconds,
            callsByOperator
        };
    }

    function getQueueOperators(queueDef) {
        if (!Array.isArray(agentsData) || agentsData.length === 0) {
            return [];
        }

        let scopedAgents = agentsData;
        if (Array.isArray(queueDef.teamKeywords) && queueDef.teamKeywords.length > 0) {
            scopedAgents = agentsData.filter((agent) => {
                const teamText = normalizeText(agent.team || '');
                return queueDef.teamKeywords.some((keyword) => teamText.includes(normalizeText(keyword)));
            });
        }

        const matched = scopedAgents.filter((agent) => {
            const searchText = normalizeText(`${agent.team || ''} ${getAgentDisplayName(agent)}`);
            return queueDef.agentKeywords.some((keyword) => searchText.includes(normalizeText(keyword)));
        });

        return matched.length > 0 ? matched : scopedAgents;
    }

    function getQueueCalls(queueDef) {
        if (!Array.isArray(callsDataForQueues) || callsDataForQueues.length === 0) {
            return [];
        }

        const matched = callsDataForQueues.filter((call) => {
            const callTypeText = normalizeText(`${call.call_type_text || ''} ${call.call_type || ''}`);
            return queueDef.callKeywords.some((keyword) => callTypeText.includes(normalizeText(keyword)));
        });

        return matched.length > 0 ? matched : callsDataForQueues;
    }

    function calculateWaitingState(queueId, queueCalls, counts, now) {
        const baseDate = callsDataDate || getCurrentCallLogDate();
        const activeThreshold = now.getTime() - 3 * 60 * 1000;

        const activeWaitingCalls = queueCalls
            .map((call) => ({
                call,
                date: parseCallDateTime(baseDate, call.time || call.call_time || call.datetime)
            }))
            .filter((item) => {
                const rawResult = item.call.result;
                if (rawResult === null || rawResult === undefined || rawResult === '') {
                    return false;
                }

                const resultCode = Number(rawResult);
                return (
                    item.date &&
                    Number.isFinite(resultCode) &&
                    WAITING_RESULT_CODES.has(resultCode) &&
                    item.date.getTime() >= activeThreshold
                );
            });

        let waiting = activeWaitingCalls.length;
        let candidateStart = null;

        if (activeWaitingCalls.length > 0) {
            candidateStart = Math.min(...activeWaitingCalls.map((item) => item.date.getTime()));
        }

        if (waiting === 0 && counts.reserved > counts.talking) {
            waiting = counts.reserved - counts.talking;
            candidateStart = now.getTime();
        }

        if (waiting > 0) {
            const previousStart = queueWaitStartedAt.get(queueId);
            let newStart = candidateStart !== null ? candidateStart : now.getTime();
            if (previousStart) {
                newStart = Math.min(previousStart, newStart);
            }
            queueWaitStartedAt.set(queueId, newStart);
        } else {
            queueWaitStartedAt.delete(queueId);
        }

        const waitStart = queueWaitStartedAt.get(queueId);
        const waitSeconds = waitStart ? Math.max(0, Math.floor((now.getTime() - waitStart) / 1000)) : 0;

        return {
            waiting,
            waitSeconds
        };
    }

    function parseCallDateTime(dateString, timeString) {
        if (!timeString) {
            return null;
        }

        const raw = String(timeString).trim();
        if (!raw) {
            return null;
        }

        const plainTimePattern = /^\d{2}:\d{2}(:\d{2})?$/;
        if (plainTimePattern.test(raw)) {
            const normalizedTime = raw.length === 5 ? `${raw}:00` : raw;
            const parsed = new Date(`${dateString}T${normalizedTime}`);
            if (!Number.isNaN(parsed.getTime())) {
                return parsed;
            }
        }

        const parsed = new Date(raw);
        if (!Number.isNaN(parsed.getTime())) {
            return parsed;
        }

        return null;
    }

    function buildCallsByOperator(calls) {
        const stats = new Map();
        calls.forEach((call) => {
            const aliases = getOperatorNameAliases(call.operator || call.operator_name || '');
            if (!aliases.length) {
                return;
            }

            aliases.forEach((alias) => {
                stats.set(alias, (stats.get(alias) || 0) + 1);
            });
        });
        return stats;
    }

    function buildQueueOperatorsHtml(metrics) {
        if (!metrics.operators.length) {
            return '<div class="csq-operators-empty">Нет операторов для отображения</div>';
        }

        const cards = [...metrics.operators]
            .sort((left, right) => getAgentDisplayName(left).localeCompare(getAgentDisplayName(right), 'ru'))
            .map((agent) => {
                const name = getAgentDisplayName(agent);
                const statusLabel = getAgentStatusLabel(agent.status);
                const statusClass = getAgentStatusClass(agent.status);
                const aliases = getOperatorNameAliases(name);
                const callsCount = aliases.reduce((maxValue, alias) => {
                    const aliasCount = metrics.callsByOperator.get(alias) || 0;
                    return Math.max(maxValue, aliasCount);
                }, 0);

                return `
                    <article class="csq-operator-card">
                        <div class="csq-operator-name">${escapeHtml(name)}</div>
                        <div class="csq-operator-status ${statusClass}">
                            <span class="csq-operator-status-dot"></span>
                            ${escapeHtml(statusLabel)}
                        </div>
                        <div class="csq-operator-calls">Звонков за день: <strong>${callsCount}</strong></div>
                    </article>
                `;
            })
            .join('');

        return `<div class="csq-operator-grid">${cards}</div>`;
    }

    function isAgentInSystem(status) {
        return status && status !== 'LOGOUT' && status !== 'LOGGED_OUT';
    }

    function getAgentDisplayName(agent) {
        return (agent && (agent.displayName || agent.username || agent.loginId)) || 'Неизвестный оператор';
    }

    function getAgentStatusClass(status, forLegacyCard = false) {
        const normalized = normalizeText(status);

        if (normalized === 'READY') {
            return forLegacyCard ? 'status-ready' : 'status-ready';
        }

        if (normalized === 'NOT_READY') {
            return forLegacyCard ? 'status-not-ready' : 'status-not-ready';
        }

        if (normalized === 'TALKING') {
            return forLegacyCard ? 'status-talking' : 'status-talking';
        }

        if (normalized === 'WORK' || normalized === 'WORK_READY' || normalized === 'AFTER_CALL_WORK') {
            return forLegacyCard ? 'status-work' : 'status-work';
        }

        return forLegacyCard ? 'status-logout' : 'status-logout';
    }

    function getAgentStatusLabel(status) {
        const normalized = normalizeText(status);

        if (normalized === 'READY') {
            return 'Готов';
        }

        if (normalized === 'NOT_READY') {
            return 'Не готов';
        }

        if (normalized === 'TALKING') {
            return 'Разговаривает';
        }

        if (normalized === 'WORK' || normalized === 'WORK_READY' || normalized === 'AFTER_CALL_WORK') {
            return 'После звонка';
        }

        if (normalized === 'RESERVED') {
            return 'Зарезервирован';
        }

        return 'Не в системе';
    }

    function formatDuration(totalSeconds) {
        const safeSeconds = Math.max(0, Number(totalSeconds) || 0);
        const hours = String(Math.floor(safeSeconds / 3600)).padStart(2, '0');
        const minutes = String(Math.floor((safeSeconds % 3600) / 60)).padStart(2, '0');
        const seconds = String(safeSeconds % 60).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }

    function normalizeText(value) {
        return String(value || '').trim().toUpperCase();
    }

    function normalizeOperatorName(value) {
        return normalizeText(value)
            .replace(/Ё/g, 'Е')
            .replace(/[^A-ZА-Я0-9\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function getOperatorNameAliases(value) {
        const normalized = normalizeOperatorName(value);
        if (!normalized || normalized === '-') {
            return [];
        }

        const tokens = normalized.split(' ').filter(Boolean);
        if (!tokens.length) {
            return [];
        }

        const aliases = new Set();
        const first = tokens[0];
        const last = tokens[tokens.length - 1];

        aliases.add(tokens.join(' '));

        if (tokens.length >= 2) {
            aliases.add(`${first} ${last}`.trim());
            aliases.add(`${last} ${first}`.trim());
            aliases.add(`${first.charAt(0)} ${last}`.trim());
            aliases.add(`${last} ${first.charAt(0)}`.trim());
            aliases.add(`${first}${last}`.trim());
            aliases.add(`${last}${first}`.trim());
        }

        return Array.from(aliases).filter((alias) => alias && alias !== '-');
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function init() {
        createAgentsUI();
        createCsqSummaryUI();

        callsDataDate = getCurrentCallLogDate();
        callsDataForQueues = extractCallsFromDomTable();
        renderCsqSummary();

        document.addEventListener('moscowCallLogUpdated', handleCallLogUpdated);

        if (isFinesseAuthenticated()) {
            setPanelsVisible(true);
            setTimeout(fetchAgentStatuses, 400);
        } else {
            setPanelsVisible(false);
            updateStatusMessage('Выполните вход Finesse для просмотра статусов', 'info');
        }

        document.addEventListener('finesseAuthSuccess', function () {
            setPanelsVisible(true);
            setTimeout(fetchAgentStatuses, 400);
        });

        document.addEventListener('finesseLogout', function () {
            agentsData = [];
            queueWaitStartedAt.clear();
            expandedQueues.clear();
            setPanelsVisible(false);
            renderCsqSummary();
        });
    }

    document.addEventListener('DOMContentLoaded', init);

    window.fetchAgentStatuses = fetchAgentStatuses;

    function showVpnNotification(
        title = 'Внимание: проблема с подключением',
        message = 'Невозможно получить данные Cisco Finesse. Проверьте подключение VPN Cisco AnyConnect.'
    ) {
        if (document.getElementById('vpn-notification')) {
            return;
        }

        const notification = document.createElement('div');
        notification.id = 'vpn-notification';
        notification.className = 'vpn-notification';
        notification.innerHTML = `
            <div class="vpn-notification-header">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${escapeHtml(title)}</span>
                <button class="vpn-close-btn">&times;</button>
            </div>
            <div class="vpn-notification-body">
                <p>${escapeHtml(message)}</p>
            </div>
        `;

        const style = document.createElement('style');
        style.textContent = `
            .vpn-notification {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 380px;
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-left: 4px solid #ffc107;
                border-radius: 4px;
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
                z-index: 1050;
                overflow: hidden;
                animation: slideIn 0.3s;
            }

            .vpn-notification-header {
                padding: 12px 15px;
                background-color: rgba(255, 193, 7, 0.2);
                display: flex;
                align-items: center;
                border-bottom: 1px solid #ffeeba;
            }

            .vpn-notification-header i {
                color: #856404;
                margin-right: 10px;
            }

            .vpn-notification-header span {
                flex: 1;
                font-weight: 600;
                color: #856404;
            }

            .vpn-close-btn {
                background: none;
                border: none;
                color: #856404;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                line-height: 1;
            }

            .vpn-notification-body {
                padding: 15px;
                color: #856404;
            }

            .vpn-notification-body p {
                margin-top: 0;
                margin-bottom: 0;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(notification);

        const closeBtn = notification.querySelector('.vpn-close-btn');
        closeBtn.addEventListener('click', function () {
            notification.style.animation = 'slideOut 0.3s forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        });

        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.animation = 'slideOut 0.3s forwards';
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 30000);
    }

    window.showVpnNotification = showVpnNotification;
})();
