(() => {
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
    const toggleBtn = document.getElementById('compactModeToggle');
    const taskDetail = document.querySelector('.modern-task-detail');
    const toggleIcon = toggleBtn?.querySelector('i');

    if (!toggleBtn || !taskDetail || !toggleIcon) {
      return;
    }

    const savedMode = localStorage.getItem('taskDetailCompactMode');
    if (savedMode === 'normal') {
      taskDetail.classList.remove('compact-mode');
      toggleIcon.classList.remove('fa-compress-alt');
      toggleIcon.classList.add('fa-expand-alt');
      toggleBtn.title = 'Включить компактный режим';
    }

    toggleBtn.addEventListener('click', () => {
      const isCompact = taskDetail.classList.contains('compact-mode');
      taskDetail.classList.toggle('compact-mode', !isCompact);

      toggleIcon.classList.toggle('fa-compress-alt', !isCompact);
      toggleIcon.classList.toggle('fa-expand-alt', isCompact);

      toggleBtn.title = isCompact ? 'Включить компактный режим' : 'Выключить компактный режим';
      localStorage.setItem('taskDetailCompactMode', isCompact ? 'normal' : 'compact');

      if (typeof window.showNotification === 'function') {
        window.showNotification(
          isCompact ? 'Обычный режим включен' : 'Компактный режим включен',
          isCompact ? 'info' : 'success'
        );
      }
    });
  });
})();
