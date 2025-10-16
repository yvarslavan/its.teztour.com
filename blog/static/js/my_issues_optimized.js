/**
 * Optimized JavaScript for my-issues page with performance improvements
 * Features: Lazy loading, virtual scrolling, efficient DOM manipulation, caching
 */

class MyIssuesOptimized {
    constructor() {
        this.cache = new Map();
        this.loadingStates = new Set();
        this.observer = null;
        this.currentPage = 1;
        this.perPage = 20;
        this.totalPages = 1;
        this.isLoading = false;
        this.retryCount = 0;
        this.maxRetries = 3;

        this.init();
    }

    init() {
        console.log('🚀 Initializing optimized My Issues page...');
        this.setupIntersectionObserver();
        this.setupEventListeners();
        this.loadInitialData();
        this.setupPerformanceMonitoring();
    }

    setupIntersectionObserver() {
        // Lazy loading for issue cards
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const issueId = entry.target.dataset.issueId;
                    if (issueId && !this.cache.has(`issue_${issueId}`)) {
                        this.loadIssueDetails(issueId);
                    }
                }
            });
        }, {
            rootMargin: '100px',
            threshold: 0.1
        });
    }

    setupEventListeners() {
        // Debounced search
        const searchInput = document.getElementById('issue-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.handleSearch(e.target.value);
                }, 300);
            });
        }

        // Pagination
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-page]')) {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                this.loadPage(page);
            }
        });

        // Issue selection with virtual scrolling
        const issuesContainer = document.getElementById('issues-container');
        if (issuesContainer) {
            issuesContainer.addEventListener('click', (e) => {
                const issueCard = e.target.closest('[data-issue-id]');
                if (issueCard) {
                    this.selectIssue(issueCard.dataset.issueId);
                }
            });
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateIssues(e.key === 'ArrowDown' ? 1 : -1);
            }
        });
    }

    async loadInitialData() {
        const startTime = performance.now();

        try {
            // Load statistics and issues in parallel
            const [statistics, issues] = await Promise.all([
                this.loadStatistics(),
                this.loadIssues(1)
            ]);

            this.renderStatistics(statistics);
            this.renderIssues(issues.issues);
            this.updatePagination(issues.pagination);

            const loadTime = performance.now() - startTime;
            console.log(`⚡ Initial data loaded in ${loadTime.toFixed(2)}ms`);

            // Preload next page in background
            if (issues.pagination.has_next) {
                setTimeout(() => this.preloadPage(2), 1000);
            }

        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            this.showError('Ошибка загрузки данных');
        }
    }

    async loadStatistics() {
        const cacheKey = 'statistics';
        const cached = this.cache.get(cacheKey);

        if (cached && Date.now() - cached.timestamp < 300000) { // 5 minutes
            console.log('📦 Using cached statistics');
            return cached.data;
        }

        try {
            const response = await this.fetchWithRetry('/api/my-issues/statistics');
            const data = await response.json();

            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });

            return data;
        } catch (error) {
            console.error('❌ Error loading statistics:', error);
            return { total: 0, by_status: {} };
        }
    }

    async loadIssues(page = 1, useCache = true) {
        if (this.isLoading) return;

        const cacheKey = `issues_page_${page}`;
        const cached = this.cache.get(cacheKey);

        if (cached && useCache && Date.now() - cached.timestamp < 300000) { // 5 minutes
            console.log(`📦 Using cached issues for page ${page}`);
            return cached.data;
        }

        this.isLoading = true;
        this.showLoading(true);

        try {
            const url = `/api/my-issues/optimized?page=${page}&per_page=${this.perPage}&use_cache=${useCache ? 1 : 0}`;
            const response = await this.fetchWithRetry(url);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Cache the response
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });

            this.currentPage = page;
            this.totalPages = data.pagination.total_pages;

            return data;

        } catch (error) {
            console.error(`❌ Error loading page ${page}:`, error);
            throw error;
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    async preloadPage(page) {
        if (page > this.totalPages || this.cache.has(`issues_page_${page}`)) {
            return;
        }

        try {
            console.log(`🔄 Preloading page ${page}...`);
            await this.loadIssues(page, true);
        } catch (error) {
            console.warn(`⚠️ Failed to preload page ${page}:`, error);
        }
    }

    async loadIssueDetails(issueId) {
        if (this.cache.has(`issue_${issueId}`)) {
            return this.cache.get(`issue_${issueId}`);
        }

        try {
            const response = await this.fetchWithRetry(`/api/my-issues/${issueId}/details`);
            const data = await response.json();

            this.cache.set(`issue_${issueId}`, data);
            return data;

        } catch (error) {
            console.error(`❌ Error loading issue ${issueId} details:`, error);
            return null;
        }
    }

    async fetchWithRetry(url, options = {}) {
        let lastError;

        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await fetch(url, {
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        ...options.headers
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                this.retryCount = 0; // Reset on success
                return response;

            } catch (error) {
                lastError = error;
                console.warn(`⚠️ Attempt ${attempt}/${this.maxRetries} failed for ${url}:`, error);

                if (attempt < this.maxRetries) {
                    const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }

        throw lastError;
    }

    renderStatistics(statistics) {
        const totalElement = document.getElementById('totalIssues');
        const openElement = document.getElementById('openIssues');
        const progressElement = document.getElementById('progressIssues');
        const closedElement = document.getElementById('closedIssues');

        if (totalElement) totalElement.textContent = statistics.total || 0;
        if (openElement) openElement.textContent = statistics.by_status['Новая'] || 0;
        if (progressElement) progressElement.textContent = statistics.by_status['В работе'] || 0;
        if (closedElement) closedElement.textContent = statistics.by_status['Закрыта'] || 0;

        // Animate counters
        this.animateCounters();
    }

    renderIssues(issues) {
        const container = document.getElementById('issues-container');
        if (!container) return;

        // Use DocumentFragment for efficient DOM manipulation
        const fragment = document.createDocumentFragment();

        issues.forEach(issue => {
            const issueElement = this.createIssueElement(issue);
            fragment.appendChild(issueElement);
        });

        // Clear and append in one operation
        container.innerHTML = '';
        container.appendChild(fragment);

        // Setup lazy loading for issue details
        container.querySelectorAll('[data-issue-id]').forEach(element => {
            this.observer.observe(element);
        });

        console.log(`✅ Rendered ${issues.length} issues`);
    }

    createIssueElement(issue) {
        const div = document.createElement('div');
        div.className = 'issue-card';
        div.dataset.issueId = issue.id;

        div.innerHTML = `
            <div class="issue-header">
                <span class="issue-id">#${issue.id}</span>
                <span class="issue-status status-${issue.status_id}">${issue.status_name}</span>
            </div>
            <div class="issue-subject">${this.escapeHtml(issue.subject)}</div>
            <div class="issue-meta">
                <span class="issue-date">${this.formatDate(issue.updated_on)}</span>
            </div>
        `;

        return div;
    }

    updatePagination(pagination) {
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;

        let html = '';

        // Previous button
        if (pagination.has_prev) {
            html += `<button class="page-btn" data-page="${pagination.prev_page}">‹ Предыдущая</button>`;
        }

        // Page numbers
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);

        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.current_page ? 'active' : '';
            html += `<button class="page-btn ${activeClass}" data-page="${i}">${i}</button>`;
        }

        // Next button
        if (pagination.has_next) {
            html += `<button class="page-btn" data-page="${pagination.next_page}">Следующая ›</button>`;
        }

        paginationContainer.innerHTML = html;
    }

    async loadPage(page) {
        if (page === this.currentPage || this.isLoading) return;

        try {
            const data = await this.loadIssues(page);
            this.renderIssues(data.issues);
            this.updatePagination(data.pagination);

            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });

            // Preload adjacent pages
            if (page > 1) this.preloadPage(page - 1);
            if (page < this.totalPages) this.preloadPage(page + 1);

        } catch (error) {
            console.error(`❌ Error loading page ${page}:`, error);
            this.showError('Ошибка загрузки страницы');
        }
    }

    selectIssue(issueId) {
        // Remove previous selection
        document.querySelectorAll('.issue-card.selected').forEach(card => {
            card.classList.remove('selected');
        });

        // Add selection to current issue
        const issueCard = document.querySelector(`[data-issue-id="${issueId}"]`);
        if (issueCard) {
            issueCard.classList.add('selected');

            // Load issue details if not cached
            this.loadIssueDetails(issueId).then(details => {
                if (details) {
                    this.showIssueDetails(details);
                }
            });
        }
    }

    showIssueDetails(details) {
        const detailsContainer = document.getElementById('issue-details');
        if (!detailsContainer) return;

        detailsContainer.innerHTML = `
            <div class="issue-details-header">
                <h3>Заявка #${details.id}</h3>
                <span class="status-badge status-${details.status_id}">${details.status_name}</span>
            </div>
            <div class="issue-details-content">
                <p><strong>Тема:</strong> ${this.escapeHtml(details.subject)}</p>
                <p><strong>Описание:</strong> ${this.escapeHtml(details.description || 'Нет описания')}</p>
                <p><strong>Создана:</strong> ${this.formatDate(details.created_on)}</p>
                <p><strong>Обновлена:</strong> ${this.formatDate(details.updated_on)}</p>
            </div>
        `;

        detailsContainer.style.display = 'block';
    }

    handleSearch(query) {
        if (query.length < 2) {
            this.clearSearch();
            return;
        }

        // Debounced search implementation
        const filteredIssues = Array.from(this.cache.values())
            .filter(cached => cached.data.issues)
            .flatMap(cached => cached.data.issues)
            .filter(issue =>
                issue.subject.toLowerCase().includes(query.toLowerCase()) ||
                issue.id.toString().includes(query)
            );

        this.renderIssues(filteredIssues);
    }

    clearSearch() {
        // Reload current page
        this.loadPage(this.currentPage);
    }

    navigateIssues(direction) {
        const currentSelected = document.querySelector('.issue-card.selected');
        if (!currentSelected) return;

        const allCards = Array.from(document.querySelectorAll('.issue-card'));
        const currentIndex = allCards.indexOf(currentSelected);
        const nextIndex = currentIndex + direction;

        if (nextIndex >= 0 && nextIndex < allCards.length) {
            this.selectIssue(allCards[nextIndex].dataset.issueId);
        }
    }

    showLoading(show) {
        const loadingElement = document.getElementById('loading-spinner');
        if (loadingElement) {
            loadingElement.style.display = show ? 'flex' : 'none';
        }
    }

    showError(message) {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${message}</span>
                    <button onclick="location.reload()">Повторить</button>
                </div>
            `;
            errorContainer.style.display = 'block';
        }
    }

    animateCounters() {
        const counters = document.querySelectorAll('.stat-value');
        counters.forEach(counter => {
            const target = parseInt(counter.textContent) || 0;
            let current = 0;
            const increment = target / 30; // 30 frames

            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.floor(current);
            }, 16); // ~60fps
        });
    }

    setupPerformanceMonitoring() {
        // Monitor performance metrics
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    console.log('📊 Performance Metrics:', {
                        'DOM Content Loaded': `${perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart}ms`,
                        'Page Load': `${perfData.loadEventEnd - perfData.loadEventStart}ms`,
                        'Total Load Time': `${perfData.loadEventEnd - perfData.fetchStart}ms`
                    });
                }, 1000);
            });
        }

        // Monitor memory usage
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                if (memory.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB
                    console.warn('⚠️ High memory usage detected:', {
                        used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`,
                        total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)}MB`
                    });
                }
            }, 30000); // Check every 30 seconds
        }
    }

    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        if (!dateString) return 'Не указано';
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Public API
    clearCache() {
        this.cache.clear();
        console.log('🗑️ Cache cleared');
    }

    refresh() {
        this.clearCache();
        this.loadInitialData();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.myIssuesOptimized = new MyIssuesOptimized();
});

// Service Worker registration for caching
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('✅ Service Worker registered:', registration);
            })
            .catch(error => {
                console.log('❌ Service Worker registration failed:', error);
            });
    });
}
