// Toggle accordion blocks
  function toggleBlock(id) {
    const block = document.querySelector(`[data-section="${id}"]`);
    if (!block) return;

    const isOpen = block.classList.contains('open');

    if (isOpen) {
      block.classList.remove('open');
      localStorage.setItem(`block_${id}`, 'closed');
      } else {
      block.classList.add('open');
      localStorage.setItem(`block_${id}`, 'open');
    }
  }

  // Restore block states
  function restoreBlocks() {
    const blocks = document.querySelectorAll('.accordion-block');
    blocks.forEach(block => {
      const id = block.getAttribute('data-section');
      const saved = localStorage.getItem(`block_${id}`);

      // Default: open description and history
      if (saved === 'open' || (saved === null && (id === 'description' || id === 'history'))) {
        block.classList.add('open');
      }
    });
  }

  // Toggle comment form
  function toggleCommentForm() {
    const form = document.getElementById('commentFormBlock');
    if (!form) return;

    if (form.style.display === 'none') {
      form.style.display = 'block';
      form.scrollIntoView({ behavior: 'smooth' });
      } else {
      form.style.display = 'none';
    }
  }

  // Toggle description
  function toggleDesc() {
    const text = document.getElementById('descText');
    const btn = document.getElementById('descToggle');
    if (!text || !btn) return;

    if (text.classList.contains('expanded')) {
      text.classList.remove('expanded');
      btn.innerHTML = '<i class="fas fa-chevron-down"></i> Показать полностью';
    } else {
      text.classList.add('expanded');
      btn.innerHTML = '<i class="fas fa-chevron-up"></i> Скрыть';
    }
  }

  // Disable submit
  function disableSubmit() {
    const btn = document.getElementById('submitBtn');
    if (!btn) return;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
  }

  // Safer: disable on submit event to avoid double submit blocking default
  function disableSubmitOnSubmit() {
    disableSubmit();
    return true; // allow form submit
  }

  // Download file
  async function downloadFile(event, attachmentId) {
    const issueId = window.location.pathname.match(/\/my-issues\/(\d+)/)?.[1];
    if (!issueId) {
      showNotif('Ошибка определения ID заявки');
      return;
    }

    const btn = event && event.target ? event.target.closest('.icon-button') : null;
    if (!btn) return;
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;

    try {
      const url = `/api/issue/${issueId}/attachment/${attachmentId}/download?v=${Date.now()}`;
      const resp = await fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {'Cache-Control': 'no-cache'}
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const data = await resp.json();

      if (data.success && data.download_url) {
        window.open(data.download_url, '_blank');
        showNotif(`Файл ${data.filename} загружается`);
      } else {
        throw new Error('URL не получен');
      }
    } catch (error) {
      console.error('Ошибка:', error);
      showNotif(`Ошибка: ${error.message}`);
    } finally {
      setTimeout(() => {
        btn.innerHTML = orig;
        btn.disabled = false;
      }, 1000);
    }
  }

  // Show notification
  function showNotif(msg) {
    const notif = document.getElementById('notification');
    if (!notif) return;
    notif.textContent = msg;
    notif.className = 'notification-toast show';
    setTimeout(() => {
      notif.className = 'notification-toast';
    }, 3000);
  }

  // Back to list
  function goBackToListOptimized(event) {
    // Keep native behavior for modified clicks (open in new tab/window).
    if (
      event &&
      (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button === 1)
    ) {
      return true;
    }

    if (event && typeof event.preventDefault === 'function') {
      event.preventDefault();
    }

    try {
      const currentId = window.location.pathname.match(/\/my-issues\/(\d+)/)?.[1];
      if (currentId) {
        sessionStorage.setItem('return_from_issue_id', currentId);
      }

      // 1) Fast path: if user came from /my-issues, return through history
      // to preserve DataTable state and avoid full re-fetch.
      const referrer = document.referrer || '';
      const fromMyIssues = /\/my-issues(\?|$|\/)/.test(referrer);
      if (fromMyIssues && window.history.length > 1) {
        window.history.back();
        return false;
      }

      // 2) Fallback: navigate with marker to highlight and restore table state.
      window.location.href = `/my-issues?from_issue=${currentId || ''}`;
      return false;
    } catch (e) {
      console.error('Ошибка:', e);
      window.location.href = '/my-issues';
      return false;
    }
  }

  // Init
  document.addEventListener('DOMContentLoaded', function() {
    restoreBlocks();
  });
