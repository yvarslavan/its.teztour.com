/**
 * @file: theme-toggle-with-sync.js
 * @description: Enhanced theme manager with server-side cookie synchronization
 * @dependencies: None (vanilla JS)
 * @created: 2025-01-06
 */

class ThemeManagerWithSync {
    constructor() {
        this.STORAGE_KEY = 'site-theme';
        this.SYNC_ENDPOINT = '/api/theme/sync';
        this.THEMES = {
            LIGHT: 'light',
            DARK: 'dark'
        };

        // Initialize theme immediately to prevent flicker
        this.initTheme();
    }

    /**
     * Get the current theme from localStorage or system preference
     * @returns {string} 'light' or 'dark'
     */
    getStoredTheme() {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        if (stored) {
            return stored;
        }

        // Fallback to system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return this.THEMES.DARK;
        }

        return this.THEMES.LIGHT;
    }

    /**
     * Apply theme to document
     * @param {string} theme - 'light' or 'dark'
     * @param {boolean} sync - Whether to sync with server
     */
    async applyTheme(theme, sync = true) {
        const html = document.documentElement;
        const body = document.body;

        // Set data-theme attribute on HTML (new system)
        html.setAttribute('data-theme', theme);

        // Remove old theme classes
        body.classList.remove('light-theme', 'dark-theme');
        html.classList.remove('light-theme', 'dark-theme');

        // Add new theme class (for compatibility with old system)
        body.classList.add(`${theme}-theme`);
        html.classList.add(`${theme}-theme`);

        // Save to localStorage
        localStorage.setItem(this.STORAGE_KEY, theme);

        // Sync with server if enabled
        if (sync) {
            await this.syncThemeWithServer(theme);
        }

        // Update theme toggle button icons
        this.updateToggleButtonIcons(theme);

        // Dispatch custom event for other components to react
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme }
        }));


    }

    /**
     * Sync theme with server via cookie
     * @param {string} theme - 'light' or 'dark'
     */
    async syncThemeWithServer(theme) {
        try {
            const response = await fetch(this.SYNC_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ theme })
            });

            if (!response.ok) {

            }
        } catch (error) {

            // Don't throw - theme still works locally
        }
    }

    /**
     * Toggle between light and dark themes
     */
    async toggleTheme() {
        const currentTheme = this.getStoredTheme();
        const newTheme = currentTheme === this.THEMES.LIGHT
            ? this.THEMES.DARK
            : this.THEMES.LIGHT;

        await this.applyTheme(newTheme);
    }

    /**
     * Initialize theme on page load
     */
    initTheme() {
        const theme = this.getStoredTheme();
        // Don't sync on init to avoid unnecessary requests
        this.applyTheme(theme, false);
    }

    /**
     * Update theme toggle button icons
     * @param {string} theme - 'light' or 'dark'
     */
    updateToggleButtonIcons(theme) {
        const toggleButton = document.getElementById('theme-toggle');
        if (!toggleButton) return;

        const lightIcon = toggleButton.querySelector('.theme-icon-light');
        const darkIcon = toggleButton.querySelector('.theme-icon-dark');

        if (!lightIcon || !darkIcon) return;

        // Force update icons based on theme
        if (theme === this.THEMES.DARK) {
            // Dark theme - show sun icon (light icon)
            lightIcon.style.opacity = '1';
            lightIcon.style.transform = 'translate(-50%, -50%) rotate(0deg) scale(1)';
            darkIcon.style.opacity = '0';
            darkIcon.style.transform = 'translate(-50%, -50%) rotate(-90deg) scale(0.8)';
        } else {
            // Light theme - show moon icon (dark icon)
            lightIcon.style.opacity = '0';
            lightIcon.style.transform = 'translate(-50%, -50%) rotate(90deg) scale(0.8)';
            darkIcon.style.opacity = '1';
            darkIcon.style.transform = 'translate(-50%, -50%) rotate(0deg) scale(1)';
        }

        // Update tooltip
        const tooltip = theme === this.THEMES.DARK
            ? 'Переключить на светлую тему'
            : 'Переключить на темную тему';
        toggleButton.setAttribute('title', tooltip);
        toggleButton.setAttribute('aria-label', tooltip);
    }

    /**
     * Listen for system theme changes
     */
    watchSystemTheme() {
        if (!window.matchMedia) return;

        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

        darkModeQuery.addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            if (!localStorage.getItem(this.STORAGE_KEY)) {
                this.applyTheme(e.matches ? this.THEMES.DARK : this.THEMES.LIGHT);
            }
        });
    }
}

// Initialize theme manager
const themeManager = new ThemeManagerWithSync();

// Watch for system theme changes
themeManager.watchSystemTheme();

// Export for use in other scripts
window.themeManager = themeManager;

// Ensure icons are updated when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Update icons after a short delay to ensure everything is loaded
    setTimeout(() => {
        const currentTheme = themeManager.getStoredTheme();
        themeManager.updateToggleButtonIcons(currentTheme);
    }, 100);
});

// Also update icons when navigating (for HTMX or SPA-like behavior)
window.addEventListener('load', function() {
    const currentTheme = themeManager.getStoredTheme();
    themeManager.updateToggleButtonIcons(currentTheme);
});
