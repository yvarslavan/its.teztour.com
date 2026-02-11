(() => {
  async function uploadImageFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/upload_image', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    return data.location || null;
  }

  function initQuillEditor() {
    if (!window.Quill) {
      return;
    }

    const editorElement = document.getElementById('quillEditor');
    if (!editorElement) {
      return;
    }

    const quill = new Quill('#quillEditor', {
      theme: 'snow',
      modules: {
        toolbar: {
          container: [
            ['bold', 'italic', 'underline'],
            [{ color: [] }, { background: [] }],
            [{ align: [] }],
            [{ list: 'ordered' }, { list: 'bullet' }],
            ['link', 'image'],
            ['clean']
          ],
          handlers: {
            link() {
              const range = quill.getSelection();
              if (!range) {
                return;
              }
              const url = prompt('Введите URL:');
              if (url) {
                quill.format('link', url);
              }
            },
            image() {
              const input = document.createElement('input');
              input.type = 'file';
              input.accept = 'image/*';
              input.click();

              input.onchange = async () => {
                const file = input.files?.[0];
                if (!file) {
                  return;
                }
                try {
                  const uploadedUrl = await uploadImageFile(file);
                  if (!uploadedUrl) {
                    return;
                  }
                  const range = quill.getSelection(true) || { index: quill.getLength() };
                  quill.insertEmbed(range.index, 'image', uploadedUrl);
                } catch (error) {
                  console.error('Ошибка загрузки изображения:', error);
                }
              };
            }
          }
        }
      },
      placeholder: 'Введите текст сообщения...'
    });

    quill.on('text-change', () => {
      const hiddenInput = document.querySelector('#emailMessageField');
      if (hiddenInput) {
        hiddenInput.value = quill.root.innerHTML;
      }
    });

    window.quillEditor = quill;
  }

  function initFileInputUI() {
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const fileButton = document.getElementById('fileButton');

    if (!fileInput || !fileList) {
      return;
    }

    fileInput.setAttribute('multiple', 'multiple');

    fileInput.addEventListener('change', (event) => {
      const files = event.target.files || [];
      if (files.length > 0) {
        const fileNames = Array.from(files).map((file) => file.name).join('<br>');
        fileList.innerHTML = `<strong>Выбрано файлов: ${files.length}</strong><br>${fileNames}`;
        fileList.style.color = '#28a745';
      } else {
        fileList.textContent = 'Файл не выбран';
        fileList.style.color = '#6c757d';
      }
    });

    if (fileButton) {
      fileButton.style.backgroundColor = '#ff6b35';
      fileButton.style.borderColor = '#ff6b35';
      fileButton.style.color = '#ffffff';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initQuillEditor();
    initFileInputUI();
  });
})();
