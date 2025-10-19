// Скрипт для обработки кнопки "Выслать пароль"


document.addEventListener("DOMContentLoaded", function() {


    // Находим кнопку по ID
    const sendPasswordButton = document.getElementById("sendPasswordButton");

    if (sendPasswordButton) {


        // Добавляем обработчик события
        sendPasswordButton.addEventListener("click", function() {


            // Получаем имя пользователя из data-атрибута
            const username = sendPasswordButton.getAttribute("data-username");


            if (!username) {

                Swal.fire({
                    icon: 'error',
                    title: 'Ошибка!',
                    text: 'Имя пользователя не найдено'
                });
                return;
            }

            // Получаем CSRF токен
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

            // Показываем индикатор загрузки
            sendPasswordButton.disabled = true;
            sendPasswordButton.classList.add("loading");
            const originalContent = sendPasswordButton.innerHTML;
            sendPasswordButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';

            // Создаем FormData для отправки
            const formData = new FormData();
            formData.append('Username', username);
            formData.append('csrf_token', csrfToken || '');

            // Отправляем запрос на сервер
            fetch('/send_password', {
                method: 'POST',
                body: formData
            })
            .then(response => {

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Восстанавливаем кнопку
                sendPasswordButton.disabled = false;
                sendPasswordButton.classList.remove("loading");
                sendPasswordButton.innerHTML = originalContent;


                // Показываем результат
                if (data.message) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Успешно!',
                        text: data.message,
                        timer: 3000,
                        showConfirmButton: false
                    });
                } else {
                    throw new Error('Пустой ответ от сервера');
                }
            })
            .catch(error => {
                // Восстанавливаем кнопку
                sendPasswordButton.disabled = false;
                sendPasswordButton.classList.remove("loading");
                sendPasswordButton.innerHTML = originalContent;



                // Показываем ошибку
                Swal.fire({
                    icon: 'error',
                    title: 'Ошибка!',
                    text: 'Не удалось отправить пароль. Пожалуйста, попробуйте позже.'
                });
            });
        });
    } else {

    }
});
