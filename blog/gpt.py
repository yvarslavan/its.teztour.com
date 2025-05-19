from datetime import datetime
import openai
import requests

# Установка вашего API ключа
openai.api_key = "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"

chat_history = [{"role": "system", "content": "Привет! Я ваш ассистент."}]


# Функция для общения с ассистентом
def chat_with_assistant(user_input):
    global chat_history

    headers = {
        "Authorization": f"Bearer {openai.api_key}",  # Использование openai.api_key
    }

   # Получение текущей даты в формате YYYY-MM-DD
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    try:
        response = requests.get(f"https://api.openai.com/v1/usage?date={current_date}", headers=headers, timeout=30)
        data = response.json()
        print(data)
    except requests.exceptions.RequestException as e:
        print("Произошла ошибка при запросе к квоте:", e)
        print("Проверьте вашу квоту и попробуйте позже.")
        return "Произошла ошибка при запросе к квоте. Проверьте вашу квоту и попробуйте позже."
    # Добавление сообщения пользователя в историю диалога
    user_message = {"role": "user", "content": user_input}
    chat_history.append(user_message)

    # Общение с ассистентом, используя текущую историю диалога
    chat_completion = openai.ChatCompletion.create(
        messages=chat_history,
        model="gpt-3.5-turbo",
        max_tokens=1000,
        temperature=0.7,
        n=1,
        stop=None,
        timeout=15,
    )

    # Получение ответа от ассистента и добавление его в историю диалога
    assistant_response = chat_completion.choices[0].message.content
    assistant_message = {"role": "assistant", "content": assistant_response}
    chat_history.append(assistant_message)

    # Возвращение ответа ассистента
    return assistant_response
