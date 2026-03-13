(() => {
  const SECTION_STORAGE_KEY = 'taskDetailSection:';

  function closeAllActionMenus(exceptMenu = null) {
    document.querySelectorAll('.action-menu.show').forEach((menu) => {
      if (menu !== exceptMenu) {
        menu.classList.remove('show');
      }
    });
  }

  function toggleActionMenu(journalId) {
    const menu = document.getElementById(`menu-${journalId}`);
    if (!menu) {
      return;
    }

    closeAllActionMenus(menu);
    menu.classList.toggle('show');
  }

  function setTaskSectionState(sectionId, isOpen) {
    const section = document.querySelector(`[data-task-section="${sectionId}"]`);
    if (!section) {
      return;
    }

    section.classList.toggle('is-open', isOpen);
    section.classList.toggle('is-collapsed', !isOpen);
    localStorage.setItem(`${SECTION_STORAGE_KEY}${sectionId}`, isOpen ? 'open' : 'closed');
  }

  function restoreTaskSections() {
    document.querySelectorAll('[data-task-section]').forEach((section) => {
      const sectionId = section.getAttribute('data-task-section');
      const savedState = localStorage.getItem(`${SECTION_STORAGE_KEY}${sectionId}`);
      setTaskSectionState(sectionId, savedState !== 'closed');
    });
  }

  function initBackNavigation() {
    const backButton = document.getElementById('go-back-btn');
    if (!backButton) {
      return;
    }

    const referrer = document.referrer || '';
    const canUseHistoryBack = referrer.includes('/tasks/my-tasks');

    backButton.addEventListener('click', (event) => {
      if (!canUseHistoryBack || window.history.length <= 1) {
        return;
      }

      event.preventDefault();
      window.history.back();
    });
  }

  window.toggleTaskSection = (sectionId) => {
    const section = document.querySelector(`[data-task-section="${sectionId}"]`);
    if (!section) {
      return;
    }

    setTaskSectionState(sectionId, section.classList.contains('is-collapsed'));
  };

  document.addEventListener('click', (event) => {
    const actionBtn = event.target.closest('.comment-action-btn');
    if (actionBtn) {
      event.stopPropagation();
      toggleActionMenu(actionBtn.dataset.journalId);
      return;
    }

    const menuItem = event.target.closest('.menu-item');
    if (menuItem) {
      event.stopPropagation();
      const journalId = menuItem.dataset.journalId;
      const action = menuItem.dataset.action;

      closeAllActionMenus();

      if (action === 'edit' && typeof window.openEditCommentModal === 'function') {
        window.openEditCommentModal(journalId);
      } else if (action === 'delete' && typeof window.deleteComment === 'function') {
        window.deleteComment(journalId);
      }
      return;
    }

    if (!event.target.closest('.action-button-container')) {
      closeAllActionMenus();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeAllActionMenus();
    }
  });

  document.addEventListener('DOMContentLoaded', () => {
    restoreTaskSections();
    initBackNavigation();

    const taskDetail = document.querySelector('.modern-task-detail');
    if (!taskDetail) {
      return;
    }

    const toggleBtn = document.getElementById('compactModeToggle');
    const toggleIcon = toggleBtn?.querySelector('i');

    if (toggleBtn && toggleIcon) {
      const savedMode = localStorage.getItem('taskDetailCompactMode');
      if (savedMode === 'normal') {
        taskDetail.classList.remove('compact-mode');
        toggleIcon.classList.remove('fa-compress-alt');
        toggleIcon.classList.add('fa-expand-alt');
        toggleBtn.title = 'Включить компактность вторичных секций';
      }

      toggleBtn.addEventListener('click', () => {
        const isCompact = taskDetail.classList.contains('compact-mode');
        taskDetail.classList.toggle('compact-mode', !isCompact);

        toggleIcon.classList.toggle('fa-compress-alt', !isCompact);
        toggleIcon.classList.toggle('fa-expand-alt', isCompact);

        toggleBtn.title = isCompact
          ? 'Включить компактность вторичных секций'
          : 'Выключить компактность вторичных секций';
        localStorage.setItem('taskDetailCompactMode', isCompact ? 'normal' : 'compact');

        if (typeof window.showNotification === 'function') {
          window.showNotification(
            isCompact ? 'Обычный режим включен' : 'Компактность вторичных секций включена',
            isCompact ? 'info' : 'success'
          );
        }
      });
    }
  });
})();
