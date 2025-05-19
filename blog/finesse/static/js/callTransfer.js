// Константы
const API_ENDPOINTS = {
    DIALOGS: '/finesse/proxy/dialogs',
    TRANSFER: '/finesse/proxy/transfer',
    CONFIG: '/finesse/static/config/config.json'
};

// Функция для получения конфигурации
async function getConfig() {
    try {
        console.log("Запрос конфигурации...");
        const response = await fetch(API_ENDPOINTS.CONFIG);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const jsonResponse = await response.json();
        console.log("Конфигурация успешно загружена:", jsonResponse);
        return jsonResponse;
    } catch (error) {
        console.error('Ошибка при загрузке конфигурации:', error.message);
        // Добавим проверку наличия файла, вдруг кто то рукожопый
        console.log("Проверьте, существует ли файл по пути: " + API_ENDPOINTS.CONFIG);
        throw error;
    }
}

// Функция для получения текущих диалогов
async function getCurrentDialogs() {
    try {
        const response = await fetch(API_ENDPOINTS.DIALOGS);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Проверяем, что получаем XML
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/xml')) {
            throw new Error(`Неверный тип контента: ${contentType}`);
        }

        const xmlText = await response.text();
        return extractCallIdFromXml(xmlText);// Парсим XML для получения ID активного звонка
    } catch (error) {
        console.error('Ошибка при получении диалогов:', error);
        throw error;
    }
}

// Функция для выполнения трансфера звонка
async function transferCall(destination) {
    try {
        // Получаем текущий ID звонка
        const callId = await getCurrentDialogs();
        if (!callId) {
            throw new Error('Активный звонок не найден');
        }
        // Проверка с тестовый Call ID
        // if (!callId) {
        //     console.log("Активные звонки не найдены, используется тестовый Call ID");
        //     const testCallId = '+71234667890';  // Тестовый Call ID
        //     return testCallId;
        // }

        const response = await fetch(API_ENDPOINTS.TRANSFER, {
            method: 'PUT', // Используем PUT для трансфера
            headers: {
                'Content-Type': 'application/json',// Передаем JSON
                'Accept': 'application/xml' // Ожидаем XML в ответ
            },
            body: JSON.stringify({
                callId: callId,
                destination: destination
            })
        });

        if (!response.ok) {
            throw new Error(`Ошибка при выполнении трансфера: ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/xml')) {
            throw new Error(`Неверный тип ответа при трансфере: ${contentType}`);
        }

        return await response.text(); // Возвращаем XML-ответ
    } catch (error) {
        console.error('Ошибка при выполнении трансфера:', error);
        throw error;
    }
}

// Обработчик события для кнопки трансфера
document.addEventListener('DOMContentLoaded',async () => {
    const button = document.getElementById('transferCallButton');
    if (button) {
        console.log("Кнопка найдена. Ожидание клика.");
        // Обновление текста кнопки при загрузке страницы
        await updateTransferButton();

        button.addEventListener('click', async () => {
            console.log("Кнопка нажата");
            try {
                const config = await getConfig();
                console.log("Конфигурация для трансфера:", config);
                const destination = config.transferNumber;

                const statusMessage = document.getElementById('statusMessage');
                statusMessage.textContent = 'Выполняется трансфер, ждите...';

                await transferCall(destination);
                statusMessage.textContent = 'Ура! Трансфер звонка успешно выполнен!';
                console.log("Трансфер звонка успешно выполнен");
            } catch (error) {
                console.error("Ошибка при выполнении трансфера:", error);
                const statusMessage = document.getElementById('statusMessage');
                statusMessage.textContent = `Ошибка: ${error.message}`;
            }
        });
    } else {
        console.error('Кнопка с ID "transferCallButton" не найдена в DOM');
    }
});

// async function getCurrentCallId() {
//     try {
//         const response = await fetch(API_ENDPOINTS.DIALOGS);
//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }

//         const xmlText = await response.text();
//         const callId = extractCallIdFromXml(xmlText);

//         if (!callId) {
//             throw new Error('Активные звонки не найдены');
//         }

//         return callId;
//     } catch (error) {
//         console.error('Ошибка при получении ID звонка:', error);
//         throw error;
//     }
// }
// Функция для парсинга XML и получения ID вызова
function extractCallIdFromXml(xmlText) {
    try {
        // Создаем DOM-parser
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, "text/xml");

        // Проверяем на ошибки парсинга
        const parserError = xmlDoc.querySelector('parsererror');
        if (parserError) {
            throw new Error('Ошибка парсинга XML');
        }

        // Получаем все диалоги и преобразуем их в массив для использования с for-of
        const dialogNodes = Array.from(xmlDoc.getElementsByTagName('Dialog'));
        if (dialogNodes.length === 0) {
            return null; // Нет активных звонков
        }

        // Ищем активный диалог, используя for-of
        for (const dialog of dialogNodes) {
            const state = dialog.querySelector('state');

            // Проверяем, что диалог активен
            if (state && ['ACTIVE', 'HELD'].includes(state.textContent)) {
                const idNode = dialog.getAttribute('id');
                if (idNode) {
                    return idNode;
                }
            }
        }

        return null; // Не найдено активных звонков
    } catch (error) {
        console.error('Ошибка при парсинге XML диалога:', error);
        throw new Error('Не удалось извлечь ID звонка из XML');
    }
}


// Функция для отображения номера на кнопке
async function updateTransferButton() {
    try {
        const config = await getConfig();
        const transferNumber = config.transferNumber;

        const button = document.getElementById('transferCallButton');
        if (button) {
            button.textContent = `Transfer call to ${transferNumber}`;
        }
    } catch (error) {
        console.error("Ошибка при обновлении текста кнопки:", error);
    }
}
