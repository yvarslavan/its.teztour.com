/* Extracted from task_detail.html (non-Jinja legacy logic) */
const currentUserData = (window.TASK_DETAIL_CONTEXT && window.TASK_DETAIL_CONTEXT.currentUserData) || {
    username: '',
    fullName: 'Пользователь',
    firstLetter: 'U'
};

// Принудительное обновление стилей контекстного меню
document.addEventListener('DOMContentLoaded', function() {
    // Принудительно показываем кнопки действий
    const triggers = document.querySelectorAll('.comment-actions-trigger');
    triggers.forEach(trigger => {
        trigger.style.opacity = '0.5';
        trigger.style.visibility = 'visible';
        trigger.style.display = 'flex';
        trigger.style.transform = 'scale(1)';
    });
    // Принудительно применяем стили к контекстному меню
    const menus = document.querySelectorAll('.custom-context-menu');
    menus.forEach(menu => {
        menu.style.position = 'absolute';
        menu.style.top = '100%';
        menu.style.left = '0';
        menu.style.minWidth = '120px';
        menu.style.maxWidth = '140px';
        menu.style.borderRadius = '6px';
        menu.style.zIndex = '1000';
        menu.style.background = '#ffffff';
        menu.style.border = '1px solid #e5e7eb';
        menu.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        menu.style.marginTop = '2px';
    });

    const items = document.querySelectorAll('.custom-menu-item');
    items.forEach(item => {
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.gap = '6px';
        item.style.padding = '4px 8px';
        item.style.fontSize = '0.75rem';
        item.style.lineHeight = '1.2';
        item.style.minHeight = '24px';
        item.style.cursor = 'pointer';
        item.style.color = '#374151';
        item.style.borderBottom = '1px solid rgba(0, 0, 0, 0.05)';
    });

    const icons = document.querySelectorAll('.custom-menu-item i');
    icons.forEach(icon => {
        icon.style.fontSize = '0.7rem';
        icon.style.width = '12px';
        icon.style.display = 'inline-block';
        icon.style.flexShrink = '0';
        icon.style.textAlign = 'center';
    });
});

// Email функции
function toggleEmailInput() {
    const emailForm = document.getElementById('emailForm');
    const emailButton = document.querySelector('.email-button');

    if (emailForm.style.display === 'none' || emailForm.style.display === '') {
        emailForm.style.display = 'block';
        emailButton.style.display = 'none';

        // Вставляем HTML подпись в поле сообщения
        insertEmailSignature();

        // Обновляем тему для кнопки файлов
        if (typeof updateEmailFormTheme === 'function') {
            updateEmailFormTheme();
        }

        // Фокус на поле получателя
        const recipientField = emailForm.querySelector('input[name="recipient"]');
        if (recipientField) {
            recipientField.focus();
        }
    } else {
        emailForm.style.display = 'none';
        emailButton.style.display = 'block';
        // Очищаем форму
        emailForm.reset();
    }
}

function insertEmailSignature() {
    // Подпись будет добавлена автоматически при отправке email
    // Функция оставлена для совместимости
    if (typeof window.quillEditor !== 'undefined' && window.quillEditor && typeof window.quillEditor.setText === 'function') {
        // Очищаем редактор при открытии формы
        window.quillEditor.setText('');
    }
}

function disableEmailSubmitButton() {
    const submitBtn = document.getElementById('submitEmailBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Отправка...</span>';
    }
}

async function submitEmailAjax(event) {
    event.preventDefault();

    const form = document.getElementById('emailForm');
    const formData = new FormData(form);

    // Получаем данные из формы
    const recipient = formData.get('recipient')?.trim();
    const subject = formData.get('subject')?.trim();

    // Получаем HTML-контент из Quill.js
    const message = (typeof window.quillEditor !== 'undefined' && window.quillEditor && typeof window.quillEditor.root !== 'undefined') ? window.quillEditor.root.innerHTML : formData.get('message')?.trim();

    const cc = formData.get('cc')?.trim();
    const sendEmail = formData.get('send_email') === 'y';

    // Валидация
    if (!recipient) {
        showNotification('Email получателя обязателен', 'error');
        return;
    }
    if (!subject) {
        showNotification('Тема письма обязательна', 'error');
        return;
    }
    if (!message) {
        showNotification('Текст сообщения обязателен', 'error');
        return;
    }

    // Отключаем кнопку отправки
    disableEmailSubmitButton();

    try {
        const taskId = getTaskIdFromUrl();

        // Получаем CSRF токен из формы
        const csrfToken = form.querySelector('input[name="csrf_token"]')?.value;

        // Создаем FormData для отправки файлов
        const formDataToSend = new FormData();
        const sender = formData.get('sender')?.trim();

        // Добавляем HTML подпись к сообщению
        const signatureHtml = (window.TASK_DETAIL_CONTEXT && window.TASK_DETAIL_CONTEXT.emailSignatureHtml) || '';
        const messageWithSignature = message + '\n\n' + signatureHtml;

        formDataToSend.append('sender', sender || '');
        formDataToSend.append('recipient', recipient);
        formDataToSend.append('subject', subject);
        formDataToSend.append('message', messageWithSignature);
        formDataToSend.append('cc', cc || '');
        formDataToSend.append('send_email', sendEmail ? 'y' : 'n');

        // Добавляем файлы из формы
        const fileInput = document.getElementById('fileInput');
        if (fileInput && fileInput.files) {
            for (let i = 0; i < fileInput.files.length; i++) {
                formDataToSend.append('attachments', fileInput.files[i]);
            }
        }

        const headers = {
            'X-Requested-With': 'XMLHttpRequest'
        };

        // Добавляем CSRF токен если он есть
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch(`/tasks/api/task/${taskId}/send-email`, {
            method: 'POST',
            headers: headers,
            body: formDataToSend
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();

        if (data.success) {
            showNotification(data.message, 'success');

            // НОВЫЙ КОД: Добавляем комментарий в историю
            try {
                const attachmentCount = document.getElementById('fileInput')?.files?.length || 0;
                // Получаем текстовую версию сообщения (без HTML тегов)
                const plainTextMessage = message.replace(/<[^>]+>/g, '').trim();
                addEmailCommentToHistory(recipient, subject, plainTextMessage, cc, attachmentCount);
            } catch (commentError) {
                console.error('Ошибка при добавлении комментария в историю:', commentError);
            }

            // Очищаем форму и скрываем её
            form.reset();
            toggleEmailInput();
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Ошибка при отправке email:', error);
        showNotification('Ошибка при отправке email: ' + error.message, 'error');
    } finally {
        // Восстанавливаем кнопку отправки
        const submitBtn = document.getElementById('submitEmailBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-envelope"></i> <span>Отправить email</span>';
        }
    }
}

// Функция для добавления нового комментария об отправке email в DOM
function addEmailCommentToHistory(recipient, subject, message, cc = null, attachments = null) {
    const historyTimeline = document.querySelector('.history-timeline');
    if (!historyTimeline) {
        console.error('История задачи не найдена');
        return;
    }

    // Генерируем уникальный ID для комментария (временный)
    const tempJournalId = 'temp_' + Date.now();

    // Получаем текущее время в формате dd.mm.yyyy HH:MM
    const now = new Date();
    const timeString = now.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    // Формируем текст комментария (такой же как в Python коде)
    let commentLines = [`Получатель: ${recipient}`];

    if (cc) {
        commentLines.push(`Копия: ${cc}`);
    }

    if (attachments && attachments > 0) {
        commentLines.push(`Приложения: ${attachments} файл(ов)`);
    }

    // Добавляем само сообщение
    commentLines.push('', message);

    const commentText = commentLines.join('\n');

    // Создаем HTML для нового комментария
    const newCommentHTML = `
        <div class="history-item" data-type="comments">
            <div class="history-avatar">
                <div class="avatar-circle history">
                    ${currentUserData.firstLetter}
                </div>
            </div>

            <div class="history-content">
                <div class="history-header">
                    <div class="history-user">
                        <span class="user-name">${currentUserData.fullName}</span>
                        <span class="history-time">${timeString}</span>
                    </div>
                </div>

                <div class="history-comment" data-journal-id="${tempJournalId}">
                    <div class="comment-content">
                        ${commentText.replace(/\n/g, '<br>')}
                    </div>
                </div>
            </div>
        </div>
    `;

    // Добавляем в начало истории (чтобы был сверху)
    historyTimeline.insertAdjacentHTML('afterbegin', newCommentHTML);

    // Добавляем небольшую анимацию появления
    const newComment = historyTimeline.querySelector('.history-item[data-type="comments"]');
    if (newComment) {
        newComment.style.opacity = '0.5';
        newComment.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            newComment.style.transition = 'all 0.3s ease';
            newComment.style.opacity = '1';
            newComment.style.transform = 'translateY(0)';
        }, 100);
    }

    console.log('Комментарий об отправке email добавлен в историю');
}

async function deleteComment(journalId) {
  if (!confirm('Вы уверены, что хотите удалить этот комментарий?')) {
    return;
  }
  try {
    const taskId = getTaskIdFromUrl();
    const response = await fetch(`/tasks/api/task/${taskId}/comment/${journalId}/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        ...(() => {
          const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
          return token ? { 'X-CSRFToken': token } : {};
        })()
      }
    });
    if (!response.ok) {
      const errorText = await response.text();
      showNotification('Ошибка при удалении: ' + errorText, 'error');
      return;
    }
    const data = await response.json();
    if (data.success) {
      showNotification(data.message, 'success');
      const commentElement = document.querySelector(`[data-journal-id="${journalId}"]`);
      if (commentElement) {
        commentElement.closest('.history-item').remove();
      }
    } else {
      showNotification(data.error || 'Ошибка при удалении комментария', 'error');
    }
  } catch (error) {
    showNotification('Произошла ошибка при удалении комментария', 'error');
  }
}



// Функция применения стилей для темной темы
function applyDarkThemeStyles() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

  if (!isDark) return;

  const allSpans = document.querySelectorAll('span');

  allSpans.forEach(span => {
    const text = span.textContent.trim();

    // Сброс стилей
    span.style.color = '';
    span.style.backgroundColor = '';
    span.style.padding = '';
    span.style.border = '';
    span.style.borderRadius = '';
    span.style.fontWeight = '';

    // Стили для текста с "изменился" - только в описании изменений
    if (span.closest('.change-description') && (text.includes('изменился') || text.includes('Параметр'))) {
      span.style.color = '#fbbf24';
      span.style.fontWeight = 'bold';
      span.style.backgroundColor = 'rgba(251, 191, 36, 0.2)';
      span.style.padding = '2px 4px';
      span.style.borderRadius = '4px';
    }

    // Стили для значений - только по CSS классам (НЕ для имён пользователей)
    else if ((!span.classList.contains('user-name')) &&
             (span.classList.contains('old-value') || span.classList.contains('new-value'))) {
      span.style.color = '#51cf66';
      span.style.fontWeight = '600';
      span.style.backgroundColor = 'rgba(81, 207, 102, 0.2)';
      span.style.padding = '2px 6px';
      span.style.borderRadius = '4px';
      span.style.border = '1px solid #51cf66';
    }

    // Общие стили для span в истории (исключая пользователей)
    else if ((span.closest('.history-item') || span.closest('.change-item')) &&
             !span.classList.contains('user-name') &&
             !span.closest('.history-user')) {
      span.style.color = '#ffffff';
    }
  });
}

// Theme Toggle
function getCurrentTheme() {
  if (window.themeManager && typeof window.themeManager.getStoredTheme === 'function') {
    return window.themeManager.getStoredTheme();
  }
  const htmlTheme = document.documentElement.getAttribute('data-theme');
  if (htmlTheme) {
    return htmlTheme;
  }
  return document.body.classList.contains('dark-theme') ? 'dark' : 'light';
}

function updateThemeIcon(theme) {
  const themeIcon = document.getElementById('theme-icon');
  if (!themeIcon) {
    return;
  }

  themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function applyThemeFallback(nextTheme) {
  const html = document.documentElement;
  html.setAttribute('data-theme', nextTheme);
  document.body.classList.toggle('dark-theme', nextTheme === 'dark');
  document.body.classList.toggle('light-theme', nextTheme === 'light');
  localStorage.setItem('site-theme', nextTheme);
  updateThemeIcon(nextTheme);
  setTimeout(applyDarkThemeStyles, 100);
}

function toggleTheme() {
  if (window.themeManager && typeof window.themeManager.toggleTheme === 'function') {
    window.themeManager.toggleTheme();
  } else {
    const nextTheme = getCurrentTheme() === 'dark' ? 'light' : 'dark';
    applyThemeFallback(nextTheme);
  }
}

function handleThemeChange(theme) {
  updateThemeIcon(theme);
  setTimeout(applyDarkThemeStyles, 100);
}

// Initialize theme
document.addEventListener('DOMContentLoaded', function() {
  const initialTheme = getCurrentTheme();
  updateThemeIcon(initialTheme);
  setTimeout(applyDarkThemeStyles, 500);

  window.addEventListener('themeChanged', function(event) {
    handleThemeChange(event.detail.theme);
  });
});

// Copy Task Link
function copyTaskLink() {
  const url = window.location.href;
  navigator.clipboard.writeText(url).then(() => {
    showNotification('Ссылка скопирована в буфер обмена!', 'success');
  });
}

// Show Notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <i class="fas fa-${type === 'success' ? 'check' : 'info'}-circle"></i>
    <span>${message}</span>
  `;

  Object.assign(notification.style, {
    position: 'fixed',
    top: '2rem',
    right: '2rem',
    background: type === 'success' ? 'var(--success-color)' : 'var(--primary-color)',
    color: 'white',
    padding: '1rem 1.5rem',
    borderRadius: 'var(--border-radius)',
    boxShadow: 'var(--shadow-lg)',
    zIndex: '1001',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    animation: 'slideInRight 0.3s ease-out'
  });

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease-out';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// History Filters
function toggleHistoryFilters() {
  const filters = document.getElementById('historyFilters');
  filters.style.display = filters.style.display === 'none' ? 'block' : 'none';
}

// Toggle Card Sections
function toggleCard(cardId) {
  const content = document.getElementById(cardId + '-content');
  const toggle = document.getElementById(cardId + '-toggle');

  if (content.classList.contains('collapsed')) {
    content.classList.remove('collapsed');
    toggle.classList.remove('rotated');
  } else {
    content.classList.add('collapsed');
    toggle.classList.add('rotated');
  }
}

// Filter chips
document.addEventListener('DOMContentLoaded', function() {
  const filterChips = document.querySelectorAll('.filter-chip');
  const historyItems = document.querySelectorAll('.history-item');

  filterChips.forEach(chip => {
    chip.addEventListener('click', function() {
      // Remove active class from all chips
      filterChips.forEach(c => c.classList.remove('active'));
      // Add active class to clicked chip
      this.classList.add('active');

      const filter = this.getAttribute('data-filter');

      historyItems.forEach(item => {
        if (filter === 'all') {
          item.style.display = 'flex';
        } else if (filter === 'status') {
          // Показываем только элементы с изменениями статуса
          const itemType = item.getAttribute('data-type');
          if (itemType === 'changes') {
            // Проверяем, есть ли изменения статуса в этом элементе
            // Вариант 1: через класс .field-name (стандартная структура)
            const hasStatusFieldName = item.querySelector('.field-name') &&
                                       item.querySelector('.field-name').textContent.trim() === 'Статус';

            // Вариант 2: через содержимое текста (функция get_property_name)
            const changeDescriptions = item.querySelectorAll('.change-description span');
            let hasStatusInDescription = false;
            changeDescriptions.forEach(span => {
              if (span.textContent.includes('Параметр') && span.textContent.includes('Статус') && span.textContent.includes('изменился')) {
                hasStatusInDescription = true;
              }
            });

            item.style.display = (hasStatusFieldName || hasStatusInDescription) ? 'flex' : 'none';
          } else {
            item.style.display = 'none';
          }
        } else {
          const itemType = item.getAttribute('data-type');
          item.style.display = itemType === filter ? 'flex' : 'none';
        }
      });
    });
  });
});

// Smooth scrolling for internal links
document.addEventListener('DOMContentLoaded', function() {
  const links = document.querySelectorAll('a[href^="#"]');
  links.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }

  @keyframes slideOutRight {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
`;
document.head.appendChild(style);

// Helper function to get task ID from URL
function getTaskIdFromUrl() {
  const pathParts = window.location.pathname.split('/');
  const taskIndex = pathParts.indexOf('my-tasks');
  if (taskIndex !== -1 && taskIndex + 1 < pathParts.length) {
    const taskId = pathParts[taskIndex + 1];
    if (!isNaN(taskId)) {
      return taskId;
    }
  }
  return null;
}

// Attachment download function
async function downloadAttachment(attachmentId) {
  const taskId = getTaskIdFromUrl();

  if (!taskId) {
    showNotification('Ошибка: не удалось определить ID задачи', 'error');
    return;
  }

  // Показываем индикатор загрузки
  const downloadBtn = (event && event.target) ? event.target.closest('.attachment-download') : null;
  const originalContent = downloadBtn ? downloadBtn.innerHTML : '';
  if (downloadBtn) {
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    downloadBtn.disabled = true;
  }

  try {
    // Создаем URL для скачивания
    const downloadUrl = `/tasks/api/task/${taskId}/attachment/${attachmentId}/download`;

    // Получаем информацию о файле
    const response = await fetch(downloadUrl, {
      method: 'GET',
      credentials: 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.success && data.download_url) {
      // Открываем URL для скачивания в новом окне
      window.open(data.download_url, '_blank');
      showNotification(`Открывается скачивание файла: ${data.filename}`, 'success');
    } else {
      throw new Error('Не удалось получить URL для скачивания');
    }

  } catch (error) {
    console.error('Ошибка скачивания файла:', error);
    showNotification(`Ошибка скачивания файла: ${error.message}`, 'error');
  } finally {
    // Восстанавливаем кнопку
    setTimeout(() => {
      if (downloadBtn) {
        downloadBtn.innerHTML = originalContent;
        downloadBtn.disabled = false;
      }
    }, 1000);
  }
}

function goBackToTasksList(taskId) {
    // Получаем сохраненный режим просмотра или используем 'list' по умолчанию
    const savedView = sessionStorage.getItem('return_from_task_view') || 'list';

    console.log(`[goBackToTasksList] 🔄 Возврат к списку задач`);
    console.log(`[goBackToTasksList] 💾 Сохраненный режим просмотра: ${savedView}`);
    console.log(`[goBackToTasksList] 📋 Все sessionStorage:`, Object.fromEntries(Object.entries(sessionStorage)));

    // Очищаем выделение строки при возврате
    sessionStorage.removeItem('return_from_task_id');
    sessionStorage.removeItem('return_from_task_page');
    sessionStorage.removeItem('return_from_task_view');

    console.log(`[goBackToTasksList] 🧹 Очищены данные выделения строки`);

    // Переходим обратно с параметром режима
    const returnUrl = `/tasks/my-tasks?view=${savedView}&return=1`;
    console.log(`[goBackToTasksList] 🚀 Переход по URL: ${returnUrl}`);

    window.location.href = returnUrl;
}

// Функционал изменения статуса задачи подключен из внешнего файла task_status_change.js

// ===== Р¤РЈРќРљР¦РРћРќРђР› РљРћРњРњР•РќРўРђР РР•Р’ =====

/**
 * Переключение видимости формы комментариев
 */
function toggleCommentInput() {
    const commentForm = document.getElementById('commentForm');
    const commentButton = document.querySelector('.comment-button');

    if (commentForm.style.display === 'none' || commentForm.style.display === '') {
        commentForm.style.display = 'block';
        commentButton.style.display = 'none';
        // Фокус на поле ввода
        const textarea = commentForm.querySelector('textarea');
        if (textarea) {
            textarea.focus();
        }
    } else {
        commentForm.style.display = 'none';
        commentButton.style.display = 'block';
        // Очищаем поле ввода
        const textarea = commentForm.querySelector('textarea');
        if (textarea) {
            textarea.value = '';
        }
    }
}

/**
 * Отключение кнопки отправки для предотвращения двойного нажатия
 */
function disableSubmitButton() {
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Отправка...</span>';
    }
}



/**
 * Отправка комментария через AJAX (альтернативный способ)
 */
async function submitCommentAjax(event) {
    event.preventDefault();

    const form = document.getElementById('commentForm');
    const textarea = form.querySelector('textarea');
    const comment = textarea.value.trim();

    if (!comment) {
        showNotification('Комментарий не может быть пустым', 'error');
        return;
    }

    // Отключаем кнопку отправки
    disableSubmitButton();

    try {
        const taskId = getTaskIdFromUrl();

        // Получаем CSRF токен из формы
        const csrfToken = form.querySelector('input[name="csrf_token"]')?.value;

        const headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };

        // Добавляем CSRF токен если он есть
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        console.log('Отправляем AJAX запрос:', {
            url: `/tasks/api/task/${taskId}/comment`,
            method: 'POST',
            headers: headers,
            body: { comment: comment }
        });

        const response = await fetch(`/tasks/api/task/${taskId}/comment`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                comment: comment
            })
        });

        console.log('Получен ответ:', response.status, response.statusText);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка HTTP:', response.status, errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log('Данные ответа:', data);

        if (data.success) {
            showNotification(data.message, 'success');
            // Очищаем форму и скрываем её
            textarea.value = '';
            toggleCommentInput();
            // Можно перезагрузить страницу для обновления истории
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Ошибка при отправке комментария:', error);
        showNotification('Ошибка при отправке комментария: ' + error.message, 'error');
    } finally {
        // Восстанавливаем кнопку отправки
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> <span>Отправить</span>';
        }
    }
}



/**
 * Скрытие формы комментариев при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', function() {
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.style.display = 'none';
    }

    // Очистка формы после успешной отправки (без Jinja в JS)
    const CLEAR_COMMENT = !!(window.TASK_DETAIL_CONTEXT && window.TASK_DETAIL_CONTEXT.clearComment);
    if (CLEAR_COMMENT) {
        const textarea = document.querySelector('#commentForm textarea');
        if (textarea) {
            textarea.value = '';
        }
    }

});

let editingJournalId = null;

function openEditCommentModal(journalId) {
  editingJournalId = journalId;
  // Получаем текст комментария из DOM
  const commentBlock = document.querySelector(`.history-comment[data-journal-id="${journalId}"] .comment-content`);
  const commentText = commentBlock ? commentBlock.innerText : '';
  document.getElementById('editCommentTextarea').value = commentText;
  document.getElementById('editCommentModal').style.display = 'flex';
}

function closeEditCommentModal() {
  editingJournalId = null;
  document.getElementById('editCommentModal').style.display = 'none';
}


document.addEventListener('DOMContentLoaded', function() {
  // Навешиваем обработчики для модального окна редактирования комментария
  const cancelBtn = document.getElementById('cancelEditCommentBtn');
  const closeBtn = document.getElementById('closeEditCommentModalBtn');
  const saveBtn = document.getElementById('saveEditCommentBtn');

  if (cancelBtn) cancelBtn.onclick = closeEditCommentModal;
  if (closeBtn) closeBtn.onclick = closeEditCommentModal;
  if (saveBtn) saveBtn.onclick = async function() {
    const newText = document.getElementById('editCommentTextarea').value.trim();
    if (!newText) {
      showNotification('Комментарий не может быть пустым', 'error');
      return;
    }
    try {
      const taskId = getTaskIdFromUrl();
      const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      const response = await fetch(`/tasks/api/task/${taskId}/comment/${editingJournalId}/edit`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          ...(token ? { 'X-CSRFToken': token } : {})
        },
        body: JSON.stringify({ comment: newText })
      });
      if (!response.ok) {
        const errorText = await response.text();
        showNotification('Ошибка при сохранении: ' + errorText, 'error');
        return;
      }
      const data = await response.json();
      if (data.success) {
        showNotification('Комментарий обновлён', 'success');
        closeEditCommentModal();
        setTimeout(() => window.location.reload(), 500);
      } else {
        showNotification(data.error || 'Ошибка при сохранении', 'error');
      }
    } catch (e) {
      showNotification('Ошибка при сохранении: ' + e, 'error');
    }
  };

  // Добавляем прямой обработчик клика для кнопки "Назад к списку"
  const goBackBtn = document.getElementById('go-back-btn');
  if (goBackBtn) {
    console.log('🔙 Найдена кнопка "Назад к списку", добавляем обработчик клика');
    goBackBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();

      const taskId = this.getAttribute('data-task-id');
      console.log('🔙 Клик по кнопке "Назад к списку", ID задачи:', taskId);

      if (taskId) {
        goBackToTasksList(taskId);
      } else {
        console.error('❌ Не найден ID задачи в атрибуте data-task-id');
        // Если ID не найден, используем резервный метод
        const taskIdFromUrl = getTaskIdFromUrl();
        if (taskIdFromUrl) {
          goBackToTasksList(taskIdFromUrl);
        } else {
          console.error('❌ Не удалось определить ID задачи');
          showNotification('Ошибка: не удалось определить ID задачи', 'error');
        }
      }
    });
  } else {
    console.error('❌ Кнопка "Назад к списку" не найдена');
  }
});


