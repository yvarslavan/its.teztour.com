// ============================================================================
// БЛОК "АКТИВНЫЕ ЗАЯВКИ" - JavaScript для страницы "Мои заявки"
// ============================================================================

const MY_ISSUES_ACTIVITY_URL = "/my-issues/api/recent-activity?limit=12";
let activityRequestPromise = null;
let activityAbortController = null;
let activityAutoRefreshId = null;

function getActivityElements() {
    return {
        container: document.getElementById("recent-activity-container"),
        loading: document.getElementById("activity-loading"),
        list: document.getElementById("activity-list"),
        empty: document.getElementById("activity-empty"),
        error: document.getElementById("activity-error"),
        content: document.getElementById("activity-accordion-content"),
    };
}

function setActivityViewState(state) {
    const { loading, list, empty, error } = getActivityElements();
    if (!loading || !list || !empty || !error) {
        return;
    }

    loading.style.display = state === "loading" ? "flex" : "none";
    list.style.display = state === "list" ? "block" : "none";
    empty.style.display = state === "empty" ? "flex" : "none";
    error.style.display = state === "error" ? "flex" : "none";
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
}

function updateActivityCount(count) {
    const badge = document.getElementById("activity-count-badge");
    if (!badge) {
        return;
    }

    if (count > 0) {
        badge.textContent = count;
        badge.style.display = "inline-block";
    } else {
        badge.style.display = "none";
    }
}

function createActivityItem(activity) {
    const item = document.createElement("div");
    item.className = "activity-item";
    item.setAttribute("data-activity-type", activity.activity_type || "update");

    const iconColors = {
        status: "#3b82f6",
        comment: "#10b981",
        priority: "#f59e0b",
        assigned: "#8b5cf6",
        description: "#6b7280",
        attachment: "#14b8a6",
        update: "#3b82f6",
    };

    const iconColor = iconColors[activity.activity_type] || "#6b7280";

    item.innerHTML = `
        <div class="activity-icon-wrapper">
            <i class="fas fa-clock activity-icon-simple" style="color: ${iconColor};"></i>
        </div>
        <div class="activity-content">
            <div class="activity-main">
                <a href="/my-issues/${activity.issue_id}" class="activity-issue-link">
                    <span class="activity-issue-id">#${activity.issue_id}</span>
                    <span class="activity-subject">${escapeHtml(activity.subject)}</span>
                </a>
            </div>
            <div class="activity-meta">
                <span class="activity-type-text">${escapeHtml(activity.activity_text)}</span>
                <span class="activity-separator">•</span>
                <span class="activity-time">${escapeHtml(activity.time_ago || "")}</span>
            </div>
            <div class="activity-details">
                <span class="activity-status">
                    <i class="fas fa-circle" style="font-size: 8px; color: ${iconColor};"></i>
                    ${escapeHtml(activity.status_name || "")}
                </span>
            </div>
        </div>
    `;

    return item;
}

function renderActivityList(activities) {
    const list = document.getElementById("activity-list");
    if (!list) {
        return;
    }

    list.innerHTML = "";
    activities.forEach((activity) => {
        list.appendChild(createActivityItem(activity));
    });
}

function shouldRefreshActivity() {
    const { content } = getActivityElements();
    if (document.hidden) {
        return false;
    }

    if (!content) {
        return true;
    }

    return content.classList.contains("active");
}

function startActivityAutoRefresh() {
    if (activityAutoRefreshId) {
        return;
    }

    activityAutoRefreshId = window.setInterval(() => {
        if (!shouldRefreshActivity()) {
            return;
        }

        loadRecentActivity({ forceRefresh: true }).catch(() => {});
    }, 120000);
}

function initActivityAccordion() {
    const header = document.getElementById("activity-accordion-toggle");
    const content = document.getElementById("activity-accordion-content");

    if (!header || !content) {
        return;
    }

    header.classList.add("active");
    content.classList.add("active");

    header.addEventListener("click", function () {
        const isActive = header.classList.contains("active");
        header.classList.toggle("active", !isActive);
        content.classList.toggle("active", !isActive);
    });
}

function loadRecentActivity(options = {}) {
    const { forceRefresh = false } = options;
    const { container } = getActivityElements();

    if (!container) {
        return Promise.resolve([]);
    }

    if (activityRequestPromise && !forceRefresh) {
        return activityRequestPromise;
    }

    if (forceRefresh && activityAbortController) {
        activityAbortController.abort();
    }

    setActivityViewState("loading");
    activityAbortController = new AbortController();

    activityRequestPromise = fetch(MY_ISSUES_ACTIVITY_URL, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        signal: activityAbortController.signal,
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            if (!data.success) {
                throw new Error(data.error || "Ошибка загрузки активности");
            }

            const activityData = Array.isArray(data.data) ? data.data : [];
            updateActivityCount(activityData.length);

            if (activityData.length === 0) {
                setActivityViewState("empty");
            } else {
                renderActivityList(activityData);
                setActivityViewState("list");
            }

            startActivityAutoRefresh();
            return activityData;
        })
        .catch((error) => {
            if (error.name === "AbortError") {
                return [];
            }

            setActivityViewState("error");
            throw error;
        })
        .finally(() => {
            activityRequestPromise = null;
            activityAbortController = null;
        });

    return activityRequestPromise;
}

document.addEventListener(
    "DOMContentLoaded",
    function () {
        initActivityAccordion();
        loadRecentActivity().catch(() => {});
    },
    { once: true }
);
