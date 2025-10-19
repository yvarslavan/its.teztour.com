/**
 * @file: theme-toggle.js
 * @description: Global theme management system with localStorage persistence
 * @dependencies: None (vanilla JS)
 * @created: 2025-01-06
 */

class ThemeManager {
    constructor() {
        this.STORAGE_KEY = 'site-theme';
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
     */
    applyTheme(theme) {
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

        // Dispatch custom event for other components to react
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme }
        }));


    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const currentTheme = this.getStoredTheme();
        const newTheme = currentTheme === this.THEMES.LIGHT
            ? this.THEMES.DARK
            : this.THEMES.LIGHT;

        this.applyTheme(newTheme);
    }

    /**
     * Initialize theme on page load
     */
    initTheme() {
        const theme = this.getStoredTheme();
        this.applyTheme(theme);
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
const themeManager = new ThemeManager();

// Watch for system theme changes
themeManager.watchSystemTheme();

// Export for use in other scripts
window.themeManager = themeManager;
