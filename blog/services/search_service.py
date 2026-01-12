import json
import os
import re
from flask import current_app

class SearchService:
    def __init__(self, app=None):
        self.index = []
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Инициализирует индекс при старте приложения"""
        self.root_path = app.root_path
        with app.app_context():
            self.build_index()

    def _normalize_word(self, word):
        """Простейший стемминг для русского языка"""
        word = word.lower()
        if len(word) > 4:
            if word.endswith(('ая', 'яя', 'ые', 'ие', 'ое', 'ее', 'ый', 'ий', 'ой', 'ей', 'ом', 'ем', 'ах', 'ях', 'ую', 'юю')):
                return word[:-2]
            elif word.endswith(('а', 'я', 'о', 'е', 'ы', 'и', 'ь', 'у', 'ю')):
                return word[:-1]
        return word

    def _get_tokens(self, text):
        """Разбивает текст на токены (стемы)"""
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        return set(self._normalize_word(w) for w in words)

    def build_index(self):
        """Собирает контент из JSON и шаблонов для поиска"""
        self.index = []
        print("[SearchService] Building search index...")
        
        project_root = os.path.dirname(self.root_path) 
        docs_path = os.path.join(project_root, 'docs', 'guides_content.json')
        
        VALID_GUIDE_IDS = {"1", "2", "3", "4", "5", "6"}
        
        if os.path.exists(docs_path):
            try:
                with open(docs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for card_id, content_data in data.items():
                    if str(card_id) not in VALID_GUIDE_IDS:
                        continue

                    full_text = []
                    title = content_data.get('filename', f"Инструкция #{card_id}").replace('.md', '').replace('.docx', '')
                    
                    first_header = None
                    for block in content_data.get('content', []):
                        text = block.get('text', '')
                        if text:
                            full_text.append(text)
                            if not first_header and block.get('type') == 'paragraph' and len(text) < 100:
                                first_header = text

                    if first_header:
                         title = first_header

                    content_str = " ".join(full_text)
                    
                    self.index.append({
                        'id': f"guide_{card_id}",
                        'type': 'guide',
                        'title': title,
                        'url': f"/guide/{card_id}",
                        'content': content_str,
                        'tokens': self._get_tokens(title + " " + content_str)
                    })
                print(f"[SearchService] Indexed {len(data)} guides from JSON (filtered)")
            except Exception as e:
                print(f"[SearchService] Error indexing JSON: {e}")
        else:
            print(f"[SearchService] Docs file not found at {docs_path}")

        static_pages = [
            {
                'id': 'vdi',
                'title': 'Инструкция VDI (Виртуальный рабочий стол)',
                'url': '/vdi',
                'keywords': 'vdi удаленный доступ рабочий стол virtual desktop vmware horizon'
            },
            {
                'id': 'tez_cloud',
                'title': 'Корпоративный файловый сервер CLOUD TEZ TOUR',
                'url': '/tez_cloud',
                'keywords': 'cloud облако облачное хранилище диск файлы обмен files share'
            },
            {
                'id': 'auto_resp',
                'title': 'Настройка автоответчика почты',
                'url': '/auto_resp',
                'keywords': 'почта автоответчик outlook отпуск заместитель'
            },
            {
                 'id': 'calls',
                 'title': 'Звонки и конференции',
                 'url': '/calls_and_conferences',
                 'keywords': 'телефон звонки конференция cisco jabber связь'
            },
            {
                'id': 'vacuum_setup',
                'title': 'Как настроить аккаунт Vacuum-IM?',
                'url': '/vacuum_setup',
                'keywords': 'vacuum im jabber chat чат программа сообщений'
            },
            {
                'id': 'no_access_site',
                'title': 'Веб-сайты не загружаются?',
                'url': '/no_access_site',
                'keywords': 'сайт доступ интернет не работает прокси'
            },
            {
                'id': 'remote_connection',
                'title': 'Удаленное подключение к Вам специалиста',
                'url': '/remote_connection',
                'keywords': 'удаленка помощь поддержка support teamviewer anydesk vnc rdp'
            },
            {
                'id': 'adress_book',
                'title': 'Корпоративная адресная книга',
                'url': '/adress_book',
                'keywords': 'адреса контакты телефоны сотрудники поиск людей'
            },
            {
                'id': 'email_setup',
                'title': 'Настройка почты на мобильных устройствах',
                'url': '/email-setup',
                'keywords': 'почта телефон android ios iphone настройка email'
            },
            {
                'id': 'setup_mail_account',
                'title': 'Настройка почтового ящика (Thunderbird/Outlook)',
                'url': '/setup_mail_account',
                'keywords': 'почта outlook thunderbird настройка пк windows email pop3 imap не работает'
            },
            {
                'id': 'setup_mail_forwarding',
                'title': 'Как переадресовать почту?',
                'url': '/setup_mail_forwarding',
                'keywords': 'почта переадресация пересылка правилa outlook'
            },
            {
                'id': 'ciscoanyconnect',
                'title': 'Как пользоваться Cisco AnyConnect',
                'url': '/ciscoanyconnect',
                'keywords': 'vpn cisco anyconnect доступ из дома удаленная работа'
            },
            {
                'id': 'questionable_email',
                'title': 'Подозрительное письмо?',
                'url': '/questionable_email',
                'keywords': 'фишинг вирус спам безопасность письмо мошенники'
            },
            {
                'id': 'safe_internet',
                'title': 'Безопасное использование интернета',
                'url': '/safe_internet',
                'keywords': 'безопасность интернет вирусы скачать защита'
            }
        ]
        
        for page in static_pages:
            content_combined = page['title'] + " " + page['keywords']
            self.index.append({
                'id': page['id'],
                'type': 'page',
                'title': page['title'],
                'url': page['url'],
                'content': content_combined,
                'tokens': self._get_tokens(content_combined)
            })
        
        print(f"[SearchService] Index building complete. Total items: {len(self.index)}")

    def search(self, query):
        """Поиск по индексу с ранжированием и префиксным совпадением"""
        if not query:
            return []
        
        query = query.strip()
        if len(query) < 2:  # Минимум 2 символа для поиска
            return []
            
        query_lower = query.lower()
        results = []
        
        for item in self.index:
            score = 0
            title_lower = item['title'].lower()
            content_lower = item['content'].lower()
            
            # ПРИОРИТЕТ 1: Точное совпадение в начале заголовка (например, "Th" -> "Thunderbird")
            if title_lower.startswith(query_lower):
                score += 100
            
            # ПРИОРИТЕТ 2: Точное совпадение подстроки в заголовке (например, "ундер" внутри "Thunderbird")
            elif query_lower in title_lower:
                score += 80
            
            # ПРИОРИТЕТ 3: Префиксное совпадение слов в заголовке
            # Разбиваем заголовок на слова и проверяем, начинается ли какое-то слово с запроса
            title_words = title_lower.split()
            for word in title_words:
                if word.startswith(query_lower):
                    score += 60
                    break
            
            # ПРИОРИТЕТ 4: Префиксное совпадение в контенте (слабое)
            if score == 0:
                content_words = content_lower.split()
                for word in content_words:
                    if word.startswith(query_lower):
                        score += 20
                        break
            
            # ПРИОРИТЕТ 5: Совпадение токенов (стемминг) для длинных запросов
            if len(query) >= 4:
                query_tokens = self._get_tokens(query)
                item_tokens = item['tokens']
                
                for q_token in query_tokens:
                    for item_token in item_tokens:
                        # Префиксное совпадение токена
                        if item_token.startswith(q_token):
                            score += 10
                            break
            
            if score > 0:
                results.append({
                    'title': item['title'],
                    'url': item['url'],
                    'type': item['type'],
                    'score': score
                })
        
        # Сортируем по релевантности и ограничиваем до 8 результатов
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:8]

# Создаем глобальный экземпляр
search_service = SearchService()
