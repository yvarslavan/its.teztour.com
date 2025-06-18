/**
 * Critical UI Fixes - Критические исправления интерфейса
 * Исправляет проблемы с двойным спинером и принудительно применяет стили
 */

console.log('[CriticalFixes] 🚨 Загрузка критических исправлений UI...');

// Защита от двойного срабатывания
let spinnerManager = {
  isActive: false,
  lockDuration: 1000, // 1 секунда блокировка
  lastShowTime: 0,

  show() {
    const now = Date.now();
    if (this.isActive && (now - this.lastShowTime) < this.lockDuration) {
      console.log('[CriticalFixes] 🚫 Спинер уже активен, игнорируем дублированный вызов');
      return false;
    }

    this.isActive = true;
    this.lastShowTime = now;

    // Принудительно показываем только один спинер
    const spinner = document.querySelector('.loading-overlay');
    if (spinner) {
      spinner.style.display = 'flex';
      spinner.style.visibility = 'visible';
      spinner.style.opacity = '1';
      console.log('[CriticalFixes] 🔄 Спинер показан с защитой от дублирования');
    }

    return true;
  },

  hide() {
    this.isActive = false;

    // Скрываем все возможные спинеры
    const spinners = document.querySelectorAll('.loading-overlay, #loading-spinner');
    spinners.forEach(spinner => {
      spinner.style.display = 'none';
      spinner.style.visibility = 'hidden';
      spinner.style.opacity = '0';
    });

    console.log('[CriticalFixes] ✅ Спинер скрыт');
  }
};

// Переопределяем LoadingManager если он существует
document.addEventListener('DOMContentLoaded', function() {
  console.log('[CriticalFixes] 🔧 Переопределение LoadingManager...');

  // Создаем улучшенный LoadingManager
  window.ImprovedLoadingManager = {
    show() {
      return spinnerManager.show();
    },

    hide() {
      return spinnerManager.hide();
    },

    forceHide() {
      console.log('[CriticalFixes] 🚨 Принудительное скрытие всех спинеров');
      spinnerManager.isActive = false;
      spinnerManager.hide();
    }
  };

  // Заменяем старый LoadingManager
  if (window.LoadingManager) {
    console.log('[CriticalFixes] 🔄 Замена старого LoadingManager...');
    window.LoadingManager = window.ImprovedLoadingManager;
  }

  // Принудительное применение стилей через 500ms
  setTimeout(() => {
    console.log('[CriticalFixes] 🎨 Принудительное применение стилей...');
    forceApplyStyles();
  }, 500);

  // Повторное применение через 2 секунды для гарантии
  setTimeout(() => {
    console.log('[CriticalFixes] 🎨 Повторное применение стилей...');
    forceApplyStyles();
  }, 2000);
});

function forceApplyStyles() {
  // Принудительно применяем стили к спинеру
  const spinnerIcons = document.querySelectorAll('.spinner-icon, .loading-overlay .spinner-icon, #loading-spinner .spinner-icon');
  spinnerIcons.forEach(icon => {
    icon.style.color = '#3b82f6';
    icon.style.fontSize = '4rem';
    icon.style.animation = 'spin 1s linear infinite, pulse-glow 2s ease-in-out infinite';
  });

  // Принудительно применяем стили к кнопкам
  const primaryButtons = document.querySelectorAll('.action-button.primary');
  primaryButtons.forEach(btn => {
    btn.style.background = 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 50%, #1e40af 100%)';
    btn.style.color = 'white';
    btn.style.boxShadow = '0 4px 15px 0 rgba(59, 130, 246, 0.3), 0 2px 10px 0 rgba(59, 130, 246, 0.2)';
    btn.style.border = '2px solid rgba(255, 255, 255, 0.1)';
    btn.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
  });

  const secondaryButtons = document.querySelectorAll('.action-button.secondary');
  secondaryButtons.forEach(btn => {
    btn.style.background = 'rgba(255, 255, 255, 0.9)';
    btn.style.color = '#3b82f6';
    btn.style.border = '2px solid rgba(59, 130, 246, 0.2)';
    btn.style.backdropFilter = 'blur(20px)';
    btn.style.webkitBackdropFilter = 'blur(20px)';
    btn.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
  });

  // Корректируем отступы заголовка
  const pageHeader = document.querySelector('.tasks-page-container .page-header');
  if (pageHeader) {
    pageHeader.style.padding = '1.25rem 0 1.5rem 0';
    pageHeader.style.marginBottom = '1.5rem';
  }

  const content = document.querySelector('.tasks-page-container.content');
  if (content) {
    content.style.paddingTop = '0.5rem';
  }

  console.log('[CriticalFixes] ✅ Стили принудительно применены');
}

// Экспортируем для глобального использования
window.CriticalFixManager = {
  spinnerManager,
  forceApplyStyles,
  forceHideAllSpinners: () => spinnerManager.hide()
};

console.log('[CriticalFixes] 🚀 Критические исправления UI загружены');
