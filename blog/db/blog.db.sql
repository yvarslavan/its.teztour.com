BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "T_AGENCY_PHONE" (
	"AGENCY_ID"	NUMERIC(8, 0) NOT NULL,
	"AGENCY_PHONE"	VARCHAR(1000),
	"OC_ROWID"	VARCHAR(18),
	"O_ROWID"	VARCHAR(18),
	PRIMARY KEY("AGENCY_ID")
);
CREATE TABLE IF NOT EXISTS "T_CALL_INFO" (
	"CALL_INFO_ID"	INTEGER NOT NULL,
	"TIME_BEGIN"	DATETIME,
	"TIME_END"	DATETIME,
	"AGENCY_ID"	VARCHAR(255),
	"PHONE_NUMBER"	VARCHAR(15),
	"CURRATOR"	VARCHAR(128),
	"THEME"	VARCHAR(128),
	"REGION"	VARCHAR(3),
	"AGENCY_MANAGER"	VARCHAR(50),
	"AGENCY_NAME"	VARCHAR(255),
	PRIMARY KEY("CALL_INFO_ID")
);
CREATE TABLE IF NOT EXISTS "_alembic_tmp_notifications" (
	"id"	INTEGER NOT NULL,
	"user_id"	INTEGER,
	"issue_id"	INTEGER,
	"old_status"	TEXT,
	"new_status"	TEXT,
	"old_subj"	TEXT,
	"date_created"	DATETIME,
	PRIMARY KEY("id"),
	UNIQUE("id")
);
CREATE TABLE IF NOT EXISTS "alembic_version" (
	"version_num"	VARCHAR(32) NOT NULL,
	CONSTRAINT "alembic_version_pkc" PRIMARY KEY("version_num")
);
CREATE TABLE IF NOT EXISTS "chat_messages" (
	"id"	INTEGER NOT NULL,
	"message_id"	VARCHAR NOT NULL,
	"from_jid"	VARCHAR NOT NULL,
	"to_jid"	VARCHAR NOT NULL,
	"body"	TEXT NOT NULL,
	"timestamp"	DATETIME,
	"type"	VARCHAR NOT NULL,
	"status"	VARCHAR,
	"contact_name"	VARCHAR,
	"contact_status"	VARCHAR,
	"is_archived"	BOOLEAN,
	PRIMARY KEY("id"),
	UNIQUE("message_id")
);
CREATE TABLE IF NOT EXISTS "notifications" (
	"id"	INTEGER NOT NULL UNIQUE,
	"user_id"	INTEGER NOT NULL,
	"issue_id"	INTEGER NOT NULL,
	"old_status"	TEXT,
	"new_status"	TEXT,
	"old_subj"	TEXT,
	"date_created"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "notifications_add_notes" (
	"id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"issue_id"	INTEGER NOT NULL,
	"author"	TEXT,
	"notes"	TEXT,
	"date_created"	TEXT,
	"source_id"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "posts" (
	"id"	INTEGER NOT NULL,
	"title"	VARCHAR(100) NOT NULL,
	"date_posted"	DATETIME NOT NULL,
	"content"	TEXT,
	"image_post"	VARCHAR(30),
	"user_id"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("user_id") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "push_subscriptions" (
	"id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"endpoint"	TEXT NOT NULL,
	"p256dh_key"	TEXT NOT NULL,
	"auth_key"	TEXT NOT NULL,
	"user_agent"	TEXT,
	"created_at"	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"last_used"	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"is_active"	BOOLEAN NOT NULL DEFAULT 1,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("user_id","endpoint"),
	FOREIGN KEY("user_id") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL,
	"username"	VARCHAR(20) NOT NULL,
	"full_name"	VARCHAR(255),
	"password"	VARCHAR(60) NOT NULL,
	"email"	VARCHAR(120) NOT NULL,
	"office"	VARCHAR(120),
	"last_seen"	DATETIME,
	"department"	VARCHAR(120),
	"position"	VARCHAR(120),
	"phone"	VARCHAR(30),
	"image_file"	VARCHAR(20) NOT NULL,
	"vpn"	INTEGER,
	"vpn_end_date"	VARCHAR(20),
	"vacuum_im_notifications"	INTEGER DEFAULT 0,
	"online"	BOOLEAN DEFAULT FALSE,
	"is_redmine_user"	BOOLEAN DEFAULT FALSE,
	"id_redmine_user"	INTEGER DEFAULT 4,
	"is_admin"	INTEGER NOT NULL DEFAULT 0,
	"can_access_quality_control"	BOOLEAN DEFAULT FALSE,
	"browser_notifications_enabled"	BOOLEAN NOT NULL DEFAULT 0,
	"can_access_contact_center_moscow"	BOOLEAN NOT NULL DEFAULT 0,
	"last_notification_check"	DATETIME,
	UNIQUE("email"),
	PRIMARY KEY("id"),
	UNIQUE("username")
);
INSERT INTO "alembic_version" ("version_num") VALUES ('c1631af72cff');
INSERT INTO "notifications" ("id","user_id","issue_id","old_status","new_status","old_subj","date_created") VALUES (4611,53,261895,'Запрошено уточнение','Закрыта','Разместить текста по направлению Таиланд','2025-05-30 14:35:16.000000');
INSERT INTO "notifications" ("id","user_id","issue_id","old_status","new_status","old_subj","date_created") VALUES (4620,17,262190,'Новая','Закрыта','Доступ в ЕРП','2025-05-30 17:53:48.000000');
INSERT INTO "notifications" ("id","user_id","issue_id","old_status","new_status","old_subj","date_created") VALUES (4634,1,258367,'Перенаправлена','Приостановлена','ТЕСТ','2025-05-30 21:52:07.000000');
INSERT INTO "notifications_add_notes" ("id","user_id","issue_id","author","notes","date_created","source_id") VALUES (1,17,262186,'a.tskhai@nsk.tez-tour.com','<p>Приведите пример заявки, к которой вам нужен доступ, но его нет.</p>
','2025-05-30 14:17:59.000000',13104);
INSERT INTO "notifications_add_notes" ("id","user_id","issue_id","author","notes","date_created","source_id") VALUES (2,53,261895,'i.kuran@tez-tour.com','<p>Сделано, "Тайланд" везде исправлен на "Таиланд".</p>
','2025-05-30 14:35:16.000000',13107);
INSERT INTO "notifications_add_notes" ("id","user_id","issue_id","author","notes","date_created","source_id") VALUES (5,17,262186,'a.tskhai@nsk.tez-tour.com','<p>Автоматическая смена подзадачи #262190</p>','2025-05-30 17:53:48.000000',13118);
INSERT INTO "notifications_add_notes" ("id","user_id","issue_id","author","notes","date_created","source_id") VALUES (6,17,262190,'a.tskhai@nsk.tez-tour.com','<p>Предоставление прав В обход фильтра "Только свои заявки по региону" для пользователя a.tskhai согласовано.</p>
','2025-05-30 17:53:48.000000',13119);
INSERT INTO "notifications_add_notes" ("id","user_id","issue_id","author","notes","date_created","source_id") VALUES (7,17,262186,'a.tskhai@nsk.tez-tour.com','<p>Предоставление прав В обход фильтра "Только свои заявки по региону" для пользователя a.tskhai согласовано.</p>
','2025-05-30 17:53:48.000000',13121);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (1,'Информационный Telegram бот','2024-02-18 13:44:43.271481','Служба поддержки должна отвечать на запросы оперативно, а для этого её нужно так же оперативно уведомлять. Нет нужды придумывать что-то своё — любой современный мессенджер справится с этой задачей на ура. Мы выбрали Telegram. Он удобен, работает на всех основных платформах, а функционал бота опережает любой из мессенджеров как минимум на год. В нашем случае, бот представляет собой информационный канал, к которому могут легко подключиться сотрудники компании, и с которым можно взаимодействовать текстовыми командами или кнопками пользовательской клавиатуры. Основные его возможности описаны <a href="https://teztour.gitbook.io/teztour-support-bot" style="color: blue; text-decoration: underline;">здесь</a>.Чтобы сотруднику подключиться к боту достаточно перейти по данной <a href="https://t.me/TezTourHelpDesk_bot" style="color: blue; text-decoration: underline;">ссылке</a>. Однако, наш бот предназначен исключительно для внутреннего использования. Нельзя допустить, чтобы кто угодно мог получить доступ к нему. Поэтому функционал бота становится доступным после авторизации пользователя в нем.','2fba9eb098acbb33b340272960121d64.jpg',1);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (2,'ГИС Электронная путёвка','2024-03-26 16:10:43.257435','<p>&nbsp;</p>
<p style="text-align: left;">С 15 ноября 2023 года туроператоры и турагенты, которые продают зарубежные поездки, обязаны передавать в информационную систему Электронная путёвка сведения о себе, туристских продуктах и заключённых договорах, включая информацию о туристах и условиях путешествия.</p>
<ul style="text-align: left;">
<li>
<h3 style="text-align: left;"><strong>Функционал системы Электронная путёвка</strong></h3>
</li>
</ul>
<p style="text-align: left;">Техническая информация по ГИС ЭП находится по адресу <u><a href="https://eisep.ru/">https://eisep.ru/</a></u>. Система функционирует как агрегатор информации, которую предоставляют участники туристического рынка в рамках электронного взаимодействия. Туристы или заказчики могут получить доступ к необходимым сведениям, но только тем, которые касаются конкретного туриста и (или) заказчика. По предоставленным в ГИС сведениям государство отслеживает турпродукты, проданные путёвки, условия заключённых договоров, их выполнение. Посредством ГИС формируется электронная путёвка, как документ, который предоставляется клиентам туроператора и турагента. По данным в ГИС госорганы проводят проверку соблюдения установленных правил участниками рынка. При необходимости государство может оперативно вмешаться и оказать российским туристам помощь, например, если с туром возникнут какие-то проблемы.</p>
<ul style="text-align: left;">
<li>
<h3><strong>Требования к туроператорам и турагентам</strong></h3>
</li>
</ul>
<p style="text-align: left;">Для каждого туроператора, который продаёт зарубежные туры, а с 1 сентября 2024 года и внутренние турпродукты, установлена обязанность <u><a href="https://ev.tourism.gov.ru/prod_guide.html">подключиться к ГИС</a></u> и передавать определённый набор сведений.</p>
<p style="text-align: left;">Для подключения и работы в ГИС нужен квалифицированный сертификат электронной подписи:</p>
<ol style="text-align: left;">
<li style="text-align: justify;">
<p>Обязанность туроператора &mdash; каждый месяц, до 15 числа, передавать в ГИС сведения о договорах, которые были заключены в прошлом месяце, а также номер турагента, если договор был заключён через него. Для передачи сведений нужна КЭП уполномоченного лица, который имеет статус администратора. В данном случае квалифицированный сертификат выпускает Удостоверяющий центр ФНС или его доверенное лицо.</p>
</li>
<li>
<p style="text-align: justify;">Поскольку в системе от имени туроператора могут работать его сотрудники, каждому из них нужен квалифицированный сертификат, то есть <a href="https://iitrust.ru/el-podpis/tarif/elektronnaya-podpis-bazovaya/"><u>квалифицированная электронная подпись (КЭП)</u></a>. Сотрудники, как физические лица, получают сертификаты в коммерческих удостоверяющих центрах, которые должны быть аккредитованы Минцифры.</p>
</li>
</ol>
<p style="text-align: left;">Для турагентств, учитывая, что они выполняют роль посредника, нет обязанности передавать в ГИС сведения. Эти участники туристического рынка взаимодействуют с туроператорами, в том числе направляют в их информационную систему электронную путёвку, согласно Правилам обмена информацией, которые утверждены <u><a href="https://docs.cntd.ru/document/560304028?marker=64U0IK">постановлением Правительства от 08.06.2019 № 748</a></u>. Для электронного документооборота и взаимодействия туроператоров и турагентов, в том числе их сотрудников, нужна <u><a href="https://iitrust.ru/el-podpis/">квалифицированная ЭП</a></u>.</p>
<ul style="text-align: left;">
<li>
<h3><strong>Подключение к ГИС ЭП в компании</strong></h3>
</li>
</ul>
<p style="text-align: left;">На текущий момент осуществлено подключение к демонстрационному и продуктовому стендам электронной путевки.</p>
<p style="text-align: left;"><strong>📌 Демонстрационный стенд</strong></p>
<p style="text-align: left;">Адрес подключения:<strong>10.7.74.235</strong></p>
<p style="text-align: left;">Личный кабинет администратора ГИС ЭП:<u><a href="https://study.eisep.ru:10333/lkto/rcisto">https://study.eisep.ru:10333/lkto/rcisto</a></u></p>
<p style="text-align: left;">Личный кабинет пользователя ГИС ЭП: <u><a href="https://study.eisep.ru:10334/lk/">https://study.eisep.ru:10334/lk/</a></u></p>
<p style="text-align: left;">Сертификат - <strong>Тестовый УЦ ИнфоТеКС</strong>, истекает <strong>12.04.2024</strong></p>
<p style="text-align: left;">Туннелирование связи с удаленными узлами настроено для следующих компаний:</p>
<p style="text-align: left;"><strong>Общество с ограниченной ответственностью &laquo;ООО Компания ТЕЗ ТУР&raquo;</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5556, </strong>адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo; <a href="http://10.7.74.235:5556/EPMessageExchangeWS/?wsdl"><u>http</u><u>://10.7.74.235:5556/</u><u>EPMessageExchangeWS</u><u>/?</u><u>wsdl</u></a></p>
<ul style="text-align: left;">
<li>
<p>Обмен НСИ, порт <strong>5557, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40001</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <u><a href="http://10.7.74.235:5557/EPInputWS?wsdl">http://10.7.74.235:5557/EPInputWS?wsdl</a></u></p>
<p style="text-align: left;"><strong>Общество с ограниченной ответственностью &laquo;ООО ТЕЗ ТУР ЦЕНТР&raquo;</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5560, </strong>адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo; <u><a href="http://10.7.74.235:5560/EPMessageExchangeWS/?wsdl">http://10.7.74.235:5560/EPMessageExchangeWS/?wsdl</a></u></p>
<p style="text-align: left;">Обмен НСИ, порт <strong>5561, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40001</strong></p>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <u><a href="http://10.7.74.235:5561/EPInputWS?wsdl">http://10.7.74.235:5561/EPInputWS?wsdl</a></u></p>
<p style="text-align: left;"><strong>Общество с ограниченной ответственностью &laquo;ООО "ТЕЗ ТУР"&raquo; (Тез Тур Северо-Запад)</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5559, </strong>адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo; <u><a href="http://10.7.74.235%205559">http://10.7.74.235: 5559/EPMessageExchangeWS/?wsdl</a></u></p>
<ul style="text-align: left;">
<li>
<p>Обмен НСИ, порт <strong>5558, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40001</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <u><a href="http://10.7.74.235:5558/EPInputWS?wsdl">http://10.7.74.235:5558/EPInputWS?wsdl</a></u></p>
<p style="text-align: left;"><strong>Общество с ограниченной ответственностью &laquo;ООО "ЮНИТУР-2007"&raquo;</strong></p>
<p style="text-align: left;">Адрес подключения: <strong>10.7.98.12</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5575, </strong>адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo;</p>
<p style="text-align: left;"><u><a href="http://10.7.98.12:5575/EPMessageExchangeWS/?wsdl">http://10.7.98.12:5575/EPMessageExchangeWS/?wsdl</a></u></p>
<ul style="text-align: left;">
<li>
<p>Обмен НСИ, порт <strong>5570, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>study.eisep.ru : 40001</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <a href="http://10.7.98.12:5575/EPInputWS?wsdl"><u>http://10.7.98.12:5575/EPInputWS?wsdl</u></a></p>
<p style="text-align: left;"><strong>📌 Продуктивный стенд</strong></p>
<p style="text-align: left;">Личный кабинет администратора ГИС ЭП:<a href="https://prod.eisep.ru:10333/lkto/rcisto"><u>https://</u><u>prod</u><u>.eisep.ru:10333/lkto/rcisto</u></a></p>
<p style="text-align: left;">Личный кабинет пользователя ГИС ЭП: <a href="https://prod.eisep.ru:10334/lk/"><u>https://</u><u>prod</u><u>.eisep.ru:10334/lk/</u></a></p>
<p style="text-align: left;">Туннелирование связи с удаленными узлами настроено для следующих компаний:</p>
<p style="text-align: left; background-color: red;"><strong>Общество с ограниченной ответственностью &laquo;ООО &quot;КОМПАНИЯ ТЕЗ ТУР&quot;</strong></p>
<p style="text-align: left;">Сертификат: ООО "АйтиКом"</p>
<p style="text-align: left;">Истекает: 24.08.2024</p>
<p style="text-align: left;">Адрес подключения: <strong>10.7.98.12</strong></p>
<p style="text-align: left;">Мнемоника инф.системы:<strong>1027739288994-1</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5565, </strong>адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo; <a href="http://10.7.98.12:5565/EPMessageExchangeWS/?wsdl"><u>http</u><u>://10.7.98.12:5565/</u><u>EPMessageExchangeWS</u><u>/?</u><u>wsdl</u></a></p>
<ul style="text-align: left;">
<li>
<p>Обмен НСИ, порт <strong>5560, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40001</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <u><a href="http://10.7.98.12:5560/EPInputWS?wsdl">http://10.7.98.12:5560/EPInputWS?wsdl</a></u></p>
<p style="text-align: left; background-color: red;"><strong>Общество с ограниченной ответственностью &laquo;ООО "ТТЦ"&raquo; (Тез Тур Центр)</strong></p>
<p style="text-align: left;">Сертификат: ООО "АйтиКом"</p>
<p style="text-align: left;">Истекает: 30.08.2024</p>
<p style="text-align: left;">Адрес подключения: <strong>10.7.98.11</strong></p>
<p style="text-align: left;">Мнемоника инф.системы:<strong>1177746031319-1</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5565, </strong>адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo; <a href="http://10.7.98.11:5565/EPMessageExchangeWS/?wsdl"><u>http</u><u>://10.7.98.11:5565/</u><u>EPMessageExchangeWS</u><u>/?</u><u>wsdl</u></a></p>
<ul style="text-align: left;">
<li>
<p>Обмен НСИ, порт <strong>5560, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40001</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <u><a href="http://10.7.98.11:5560/EPInputWS?wsdl">http://10.7.98.11:5560/EPInputWS?wsdl</a></u></p>
<p style="text-align: left; background-color: red;"><strong>Общество с ограниченной ответственностью &laquo;ООО "ТЕЗ ТУР"&raquo; (Тез Тур Северо-Запад) </strong></p>
<p style="text-align: left;">Сертификат: ООО "АйтиКом"</p>
<p style="text-align: left;">Истекает: 23.08.2024</p>
<p style="text-align: left;">Адрес подключения: <strong>10.7.98.10</strong></p>
<p style="text-align: left;">Мнемоника инф.системы:<strong>1057811931275-1</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5565, </strong>адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo; <a href="http://10.7.98.10:5565/EPMessageExchangeWS/?wsdl"><u>http</u><u>://10.7.98.10:5565/</u><u>EPMessageExchangeWS</u><u>/?</u><u>wsdl</u></a></p>
<ul style="text-align: left;">
<li>
<p>Обмен НСИ, порт <strong>5560, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40001</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <u><a href="http://10.7.98.10:5560/EPInputWS?wsdl">http://10.7.98.10:5560/EPInputWS?wsdl</a></u></p>
<p style="text-align: left; background-color: red;"><strong>Общество с ограниченной ответственностью &laquo;ООО "ЮНИТУР-2007"&raquo;</strong></p>
<p style="text-align: left;">Сертификат: ООО "АйтиКом"</p>
<p style="text-align: left;">Истекает: 17.08.2024</p>
<p style="text-align: left;">Адрес подключения: <strong>10.7.98.9</strong></p>
<p style="text-align: left;">Мнемоника инф.системы:<strong>1076671016971-1</strong></p>
<ul style="text-align: left;">
<li>
<p>Обмен путевками, порт <strong>5565, </strong>адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40000</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен путевками&raquo; <a href="http://10.7.98.9:5565/EPMessageExchangeWS/?wsdl"><u>http</u><u>://10.7.98.9:5565/</u><u>EPMessageExchangeWS</u><u>/?</u><u>wsdl</u></a></p>
<ul style="text-align: left;">
<li>
<p>Обмен НСИ, порт <strong>5560, </strong>Адрес и порт удаленного узла ГИС ЭП <strong>prod</strong><strong>.eisep.ru : 40001</strong></p>
</li>
</ul>
<p style="text-align: left;">Проверка работы туннеля &laquo;Обмен НСИ&raquo; <u><a href="http://10.7.98.9:5560/EPInputWS?wsdl">http://10.7.98.9:5560/EPInputWS?wsdl</a></u></p>
<p>&nbsp;</p>',NULL,1);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (3,'Выкладка новой версии ЕРП','2024-04-02 11:58:33.766607','<p style="font-size: 18px; text-align: justify;">Для загрузки файлов новой версии системы ЕРП на FTP-сервера используется 
    программа <a href="https://www.emtec.com/pyrobatchftp/index.html"><b>«EmTec PyroBatchFTP»</b></a>, 
    позволяющая загружать файлы с/на FTP сервера в автоматическом режиме через скрипт, используя простой пакетный 
    язык сценария. Дистрибутив программы находится на <strong>S:\SOFT\PyroBatchFTP V2.25.exe</strong>. 
    Сам процесс установки приложения несложен и состоит из того, что Вы отвечаете на вопросы программы установки и 
    нажимаете кнопку Далее.</p>
<p style="font-size: 18px; text-align: justify;">📌Для выкладки новой версии ЕРП следует:</p>
<p style="font-size: 18px; text-align: justify;">🔹Запустить программу PyroBatchFTP V2.25</p>
<p style="font-size: 18px; text-align: justify;">🔹Запустить с локального компьютера bat файл <strong>transfer.bat</strong> от имени администратора (Исходный файл лежит <strong>F:\tech\BatchFTP</strong>)</p>
<p style="font-size: 18px; text-align: justify;">🔹Готово</p>
','ec9273fbf22fc5436d0ec421acb2a967.png',3);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (4,'Zabbix сервера','2024-04-15 10:05:18.187176','<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Servers</title>
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }

        th {
            border: 1px solid #B3B3B3;
            text-align: center;
            padding: 8px;
        }

        td {
            border: 1px solid #B3B3B3;
            text-align: left;
            padding: 8px;
        }

        .header-row th {
            background-color: #deb887;
        }
.support-info {
            font-size: 16px;
            text-align: left;
            margin-bottom: 10px;
        }

        .support-info a {
            color: blue;
            text-decoration: underline;
        }
    </style>
</head>
<body>
<p class="support-info">🔥 Доступы для технической поддержки:<br /> 
    Авторизация <a href="https://zabbix.teztour.com/">Zabbix</a></p>
<p class="support-info">🔹 Логин: support</p>
<p class="support-info">🔹 Пароль: support</p>
<p style="font-size: 18px; text-align: left;">💡 <strong>Zabbix разделы</strong></p>
<p style="font-size: 16px; text-align: left;">Для мониторинга и быстрого реагирования на проблемы:</p>
<p style="font-size: 16px; text-align: left;">🔹 Раздел <strong>&laquo;Проблемы&raquo;</strong> - отображаются проблемы с серверами и сервисами</p>
<p style="font-size: 16px; text-align: left;">🔹 Раздел <strong>&laquo;Сетевое оборудование&raquo;</strong> - отображаются проблемы с сетевым оборудованием</p>
<p style="font-size: 16px; text-align: left;">🔹 Раздел <strong>&laquo;Информационная панель&raquo;</strong> - текущая вспомогательная информация</p>
<p style="font-size: 18px; text-align: left;">💡 <strong>Zabbix маркировка</strong></p> 
<p style="font-size: 16px; text-align: left;"><strong>GW</strong> - маршрутизатор, <strong>SW</strong> - свитч, <strong>ASA</strong> - межсетевой экран</p>
<p style="font-size: 18px; text-align: left;">💡 <strong>Zabbix сервера</strong></p>
<table>
    <tr class="header-row">
        <th>№ п/п</th>
        <th>Наименование</th>
        <th>IP-адрес</th>
        <th>Описание</th>
    </tr>
    <tr>
        <th>21</th>
        <td><a href="https://onega.teztour.com/">onega.teztour.com</a></td>
        <td>10.7.80.4</td>
        <td>Томкат-сервер, book.tez-tour.com</td>
    </tr>
<tr>
    <th>2</th>
    <td><a href="https://adapter-ru.teztour.com/">adapter-ru.teztour.com</a></td>
    <td>10.7.74.241</td>
    <td>Компонент корпоративной шины (в разработке)</td>
</tr>
            <th>3</th>
            <td><a href="https://almaty.proxy.teztour.com/">almaty.proxy.teztour.com</a></td>
            <td>172.16.15.253</td>
            <td>Proxy-сервер SQUID</td>
        </tr>
        <tr>
            <th>4</th>
            <td><a href="https://amba.teztour.com">amba.teztour.com</td>
            <td>10.0.4.51</td>
            <td>Боевой веб-сервер (www,online,xmlgate,search и т.д)</td>
        </tr>
<tr>
    <th>5</th>
    <td><a href="https://amba.teztour.com">dev-lt.teztour.com</td>
    <td>10.7.74.201</td>
    <td>Тестовый веб-сервер приложений для разработчиков (Литва)</td>
</tr>
<tr>
    <th>6</th>
    <td><a href="https://dev2.teztour.com">dev2.teztour.com</td>
    <td>10.7.74.202</td>
    <td>Тестовый сервер для web-разработчиков (www,online,xmlgate,search и т.д)</td>
</tr>
<tr>
    <th>7</th>
    <td><a href="https://devtr.teztour.com">devtr.teztour.com</td>
    <td>10.7.74.21</td>
    <td>Тестовый сервер для разработчиков турецких приложений</td>
</tr>
<tr>
    <th>8</th>
    <td><a href="https://dhcp.teztour.com">dhcp.teztour.com</td>
    <td>10.7.74.5</td>
    <td>DHCP-сервер на M9</td>
</tr>
<tr>
    <th>9</th>
    <td><a href="https://dhcpd.teztour.com">dhcpd.teztour.com</td>
    <td>10.0.0.10</td>
    <td>DHCP-сервер на 3Data</td>
</tr>
<tr>
    <th>10</th>
    <td><a href="https://dhcpd.teztour.com">dhcpd.teztour.com</td>
    <td>10.7.80.8</td>
    <td>Боевой веб-сервер (www,online,xmlgate,search и т.д)</td>
</tr>
<tr>
    <th>11</th>
    <td><a href="https://duck.teztour.com">duck.teztour.com</td>
    <td>10.7.74.49</td>
    <td>Сервер KVM-виртуализации на M9 (backups)</td>
</tr>
<tr>
    <th>12</th>
    <td><a href="https://elastic.teztour.com">elastic.teztour.com</td>
    <td>10.7.74.44</td>
    <td>Elasticsearch - кеш подбора туров</td>
</tr>
<tr>
    <th>13</th>
    <td><a href="https://elixir.tez-tour.com">elixir.tez-tour.com</td>
    <td>10.7.74.110</td>
    <td>Proxy-сервер SQUID на M9</td>
</tr>
<tr>
    <th>14</th>
    <td><a href="https://elixir.tez-tour.com">elixir.tez-tour.com</td>
    <td>10.38.10.113</td>
    <td>Почтовый-сервер Postfix-relay (Киев)</td>
</tr>
<tr>
    <th>15</th>
    <td><a href="https://emx2.teztour.com">emx2.teztour.com</td>
    <td>10.38.10.114</td>
    <td>Почтовый-сервер Postfix-relay (Киев)</td>
</tr>
<tr>
    <th>16</th>
    <td><a href="https://enisarch.teztour.com">enisarch.teztour.com</td>
    <td>10.7.80.20</td>
    <td>Боевой сервер Oracle DB с данными ЕРП заявок</td>
</tr>
<tr>
    <th>17</th>
    <td><a href="https://enisk.teztour.com">enisk.teztour.com</td>
    <td>10.7.69.2</td>
    <td>Боевая Oracle DB ENISEY</td>
</tr>
<tr>
    <th>18</th>
    <td><a href="https://enism.teztour.com">enism.teztour.com</td>
    <td>10.7.70.2</td>
    <td>Standby-сервер Oracle ENISEY</td>
</tr>
<tr>
    <th>19</th>
    <td>F5-BigIP-3D-LOCALNET</td>
    <td>10.0.0.197</td>
    <td>Балансировщик F5-BigIP</td>
</tr>
<tr>
    <th>20</th>
    <td>F5-BigIP-3Data-198</td>
    <td>10.0.0.198</td>
    <td>Балансировщик F5-BigIP</td>
</tr>
 <tr>
    <th>21</th>
    <td><a href="https://F5-BigIP-M9-197.teztour.com/">F5-BigIP-M9-197</a></td>
    <td>10.7.74.197</td>
    <td>Балансировщик F5-BigIP</td>
</tr>
<tr>
    <th>22</th>
    <td><a href="https://F5-BigIP-M9-LOCALNET.teztour.com/">F5-BigIP-M9-LOCALNET</a></td>
    <td>10.7.74.198</td>
    <td>Балансировщик F5-BigIP</td>
</tr>
<tr>
    <th>23</th>
    <td><a href="https://galera01.teztour.com/">galera01</a></td>
    <td>10.7.74.31</td>
    <td>Galera MySQL-cluster</td>
</tr>
<tr>
    <th>24</th>
    <td><a href="https://galera02.teztour.com/">galera02</a></td>
    <td>10.0.0.45</td>
    <td>Galera MySQL-cluster</td>
</tr>
<tr>
    <th>25</th>
    <td><a href="https://galera03.teztour.com/">galera03</a></td>
    <td>10.0.0.46</td>
    <td>Galera MySQL-cluster</td>
</tr>
<tr>
    <th>26</th>
    <td><a href="https://grafana.teztour.com/">grafana.teztour.com</a></td>
    <td>10.7.74.55</td>
    <td>Система сбора и анализа логов (ELK)</td>
</tr>
<tr>
    <th>27</th>
    <td><a href="https://haribda.teztour.com/">haribda.teztour.com</a></td>
    <td>10.7.74.175</td>
    <td>Система-рассылок Mailwizz (https://mailinglists.tez-tour.com/) Landing Page сайты на Wordpress</td>
</tr>
<tr>
    <th>28</th>
    <td><a href="https://helpdesk.teztour.com/">helpdesk.teztour.com</a></td>
    <td>10.7.74.72</td>
    <td>Система Easy Redmine для Helpdesk Moscow</td>
</tr>
<tr>
    <th>29</th>
    <td><a href="https://hermes.teztour.com/">hermes.teztour.com</a></td>
    <td>10.7.74.6</td>
    <td>S3 cloud storage (storage.tez-tour.com)</td>
</tr>
<tr>
    <th>30</th>
    <td><a href="https://hex.teztour.com/">hex.teztour.com</a></td>
    <td>10.7.74.199</td>
    <td>SVN, Jira, Confluence, GitLab</td>
</tr>
<tr>
    <th>31</th>
    <td><a href="https://hv1.3data.teztour.com/">hv1.3data.teztour.com</a></td>
    <td>10.197.170.1</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>32</th>
    <td><a href="https://hv1.gra.teztour.com/">hv1.gra.teztour.com</a></td>
    <td>10.49.4.1</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>33</th>
    <td><a href="https://hv2.3data.teztour.com/">hv2.3data.teztour.com</a></td>
    <td>10.197.170.2</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>34</th>
    <td><a href="https://hv2.gra.teztour.com/">hv2.gra.teztour.com</a></td>
    <td>10.49.4.2</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>35</th>
    <td><a href="https://hv3.gra.teztour.com/">hv3.gra.teztour.com</a></td>
    <td>10.49.4.3</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>36</th>
    <td><a href="https://hv3.m9.teztour.com/">hv3.m9.teztour.com</a></td>
    <td>10.197.160.3</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>37</th>
    <td><a href="https://hv4.m9.teztour.com/">hv4.m9.teztour.com</a></td>
    <td>10.197.160.4</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>38</th>
    <td><a href="https://hv5.m9.teztour.com/">hv5.m9.teztour.com</a></td>
    <td>10.197.160.5</td>
    <td>Гипервизор ESXi</td>
</tr>
<tr>
    <th>39</th>
    <td><a href="https://james.teztour.com/">james.teztour.com</a></td>
    <td>10.0.4.53</td>
    <td>Томкат-сервер, book.tez-tour.com</td>
</tr>
<tr>
    <th>40</th>
    <td><a href="https://kube01.teztour.com/">kube01</a></td>
    <td>10.7.74.223</td>
    <td>Kubernetes-cluster</td>
</tr>
<tr>
    <th>41</th>
    <td><a href="https://kube02.teztour.com/">kube02</a></td>
    <td>10.7.74.224</td>
    <td>Kubernetes-cluster</td>
</tr>
<tr>
    <th>42</th>
    <td><a href="https://kube03.teztour.com/">kube03</a></td>
    <td>10.0.0.223</td>
    <td>Kubernetes-cluster</td>
</tr>
<tr>
    <th>43</th>
    <td><a href="https://lt.dev.teztour.com/">lt.dev.teztour.com</a></td>
    <td>10.7.74.242</td>
    <td>Тестовый веб-сервер приложений для разработчиков (Литва)</td>
</tr>
<tr>
    <th>44</th>
    <td><a href="https://mail.ekb.teztour.com/">mail.ekb.teztour.com</a></td>
    <td>10.7.96.254</td>
    <td>Почтовый сервер Екатеринбурга</td>
</tr>
<tr>
    <th>45</th>
    <td><a href="https://mail.teztour.com.ua/">mail.teztour.com.ua</a></td>
    <td>10.38.10.3</td>
    <td>Почтовый сервер Ukraine</td>
</tr>
<tr>
    <th>46</th>
    <td><a href="https://mailh.teztour.com/">mailh.teztour.com</a></td>
    <td>10.1.1.211</td>
    <td>Backup mail server (Новохохловская)</td>
</tr>
<tr>
    <th>47</th>
    <td><a href="https://mamba.teztour.com/">mamba.teztour.com</a></td>
    <td>10.0.4.54</td>
    <td>Боевой веб-сервер (www,online,xmlgate,search и т.д)</td>
</tr>
<tr>
    <th>48</th>
    <td><a href="https://market-ufa.teztour.com/">market-ufa.teztour.com</a></td>
    <td>10.7.74.131</td>
    <td>Система Easy Redmine для маркетологов (Отделы ценообразования, продаж и бронирования)(г.УФА)</td>
</tr>
<tr>
    <th>49</th>
    <td><a href="https://munin.tez-tour.com/">munin.tez-tour.com</a></td>
    <td>10.0.0.100</td>
    <td>Сервер системы мониторинга</td>
</tr>
<tr>
    <th>50</th>
    <td><a href="https://mxe.teztour.com/">mxe.teztour.com</a></td>
    <td>10.7.74.116</td>
    <td>Почтовый-сервер Postfix-relay</td>
</tr>
<tr>
    <th>51</th>
    <td><a href="https://mxk.teztour.com/">mxk.teztour.com</a></td>
    <td>10.0.0.113</td>
    <td>Почтовый-сервер Postfix-relay</td>
</tr>
<tr>
    <th>52</th>
    <td><a href="https://mxm.teztour.com/">mxm.teztour.com</a></td>
    <td>10.7.74.113</td>
    <td>Почтовый-сервер Postfix-relay</td>
</tr>
<tr>
    <th>53</th>
    <td><a href="https://mxs.teztour.com/">mxs.teztour.com</a></td>
    <td>10.0.0.116</td>
    <td>Почтовый-сервер Postfix-relay</td>
</tr>
<tr>
    <th>54</th>
    <td><a href="https://newhermes.teztour.com/">newhermes.teztour.com</a></td>
    <td>10.7.80.19</td>
    <td>Тестовый Oracle DB сервер разработчиков</td>
</tr>
<tr>
    <th>55</th>
    <td><a href="https://nginx-channel.teztour.com/">nginx-channel.teztour.com</a></td>
    <td>10.0.0.147</td>
    <td>Nginx-channel - компонент для кеширования подбора тура</td>
</tr>
<tr>
    <th>56</th>
    <td><a href="https://ngx-balancing-01.teztour.com/">ngx-balancing-01</a></td>
    <td>10.7.74.185</td>
    <td>NGINX-балансировщик</td>
</tr>
<tr>
    <th>57</th>
    <td><a href="https://ngx-balancing-02.teztour.com/">ngx-balancing-02</a></td>
    <td>10.7.74.186</td>
    <td>NGINX-балансировщик</td>
</tr>
<tr>
    <th>58</th>
    <td><a href="https://ngx-balancing-03.teztour.com/">ngx-balancing-03</a></td>
    <td>10.7.74.187</td>
    <td>NGINX-балансировщик</td>
</tr>
<tr>
    <th>59</th>
    <td><a href="https://ngx-balancing-04.teztour.com/">ngx-balancing-04</a></td>
    <td>10.0.0.216</td>
    <td>NGINX-балансировщик</td>
</tr>
<tr>
    <th>60</th>
    <td><a href="https://ngx-proxy-1.teztour.com/">ngx-proxy-1</a></td>
    <td>10.7.74.230</td>
    <td>NGINX-балансировщик</td>
</tr>
<tr>
    <th>61</th>
    <td><a href="https://ngx-proxy-2.teztour.com/">ngx-proxy-2</a></td>
    <td>10.0.0.230</td>
    <td>NGINX-балансировщик</td>
</tr>
<tr>
    <th>62</th>
    <td><a href="https://noodle.teztour.com/">noodle.teztour.com</a></td>
    <td>10.7.74.7</td>
    <td>LDAP-сервер</td>
</tr>
<tr>
    <th>63</th>
    <td><a href="https://ns1.tez-tour.com/">ns1.tez-tour.com</a></td>
    <td>10.7.74.3</td>
    <td>NS1 - Первичный DNS-сервер</td>
</tr>
<tr>
    <th>64</th>
    <td><a href="https://ns2.tez-tour.com/">ns2.tez-tour.com</a></td>
    <td>10.0.0.140</td>
    <td>NS2 - Вторичный DNS-сервер</td>
</tr>
<tr>
    <th>65</th>
    <td><a href="https://nytro.teztour.com/">nytro.teztour.com</a></td>
    <td>10.7.74.50</td>
    <td>Сервер KVM-виртуализации на M9 (backups)</td>
</tr>
<tr>
    <th>66</th>
    <td><a href="https://nyx.teztour.com/">nyx.teztour.com</a></td>
    <td>10.7.80.57</td>
    <td>Боевой веб-сервер (www,online,xmlgate,search и т.д)</td>
</tr>
<tr>
    <th>67</th>
    <td><a href="https://observium.teztour.com/">observium.teztour.com</a></td>
    <td>10.7.74.100</td>
    <td>Система мониторинга</td>
</tr>
<tr>
    <th>68</th>
    <td><a href="https://odin.teztour.com/">odin.teztour.com</a></td>
    <td>10.7.80.2</td>
    <td>Боевой веб-сервер (www,online,xmlgate,search и т.д)</td>
</tr>
<tr>
    <th>69</th>
    <td><a href="https://onega.teztour.com/">onega.teztour.com</a></td>
    <td>10.7.80.4</td>
    <td>Томкат-сервер, book.tez-tour.com</td>
</tr>
<tr>
    <th>70</th>
    <td><a href="https://otrs.teztour.com/">otrs.teztour.com</a></td>
    <td>10.7.74.142</td>
    <td>OTRS - система обработки заявок (Использовалась ранее до Easy Redmine)</td>
</tr>
<tr>
    <th>71</th>
    <td><a href="https://pgsql-eu.tez-tour.com/">pgsql-eu.tez-tour.com</a></td>
    <td>10.49.48.50</td>
    <td>Cубд Postgresql</td>
</tr>
<tr>
    <th>72</th>
    <td><a href="https://pgsql-eu2.tez-tour.com/">pgsql-eu2.tez-tour.com</a></td>
    <td>10.49.48.52</td>
    <td>Cубд Postgresql</td>
</tr>
<tr>
    <th>73</th>
    <td><a href="https://pgsql-ru.tez-tour.com/">pgsql-ru.tez-tour.com</a></td>
    <td>10.7.74.240</td>
    <td>Cубд Postgresql</td>
</tr>
<tr>
    <th>74</th>
    <td><a href="https://pgsql-ru2.tez-tour.com/">pgsql-ru2.tez-tour.com</a></td>
    <td>10.7.74.243</td>
    <td>Cубд Postgresql</td>
</tr>
<tr>
    <th>75</th>
    <td><a href="https://puppet.teztour.com/">puppet.teztour.com</a></td>
    <td>10.0.0.105</td>
    <td>Puppet - система управления конфигурациями</td>
</tr>
<tr>
    <th>76</th>
    <td><a href="https://quality.teztour.com/">quality.teztour.com</a></td>
    <td>10.7.74.130</td>
    <td>Система Easy Redmine для отдела контроля качества)(г. Москва)</td>
</tr>
<tr>
    <th>77</th>
    <td><a href="https://rel.teztour.com/">rel.teztour.com</a></td>
    <td>10.7.74.204</td>
    <td>Тестовый сервер для web-разработчиков (www,online,xmlgate,search и т.д)</td>
</tr>
<tr>
    <th>78</th>
    <td><a href="https://shan.teztour.com/">shan.teztour.com</a></td>
    <td>10.1.1.67</td>
    <td>Сервер KVM-виртуализации на Новохохловской (mail backup)</td>
</tr>
<tr>
    <th>79</th>
    <td><a href="https://sk.teztour.com/">sk.teztour.com</a></td>
    <td>10.0.0.63</td>
    <td>Mail backup, cloud.teztour.com</td>
</tr>
<tr>
    <th>80</th>
    <td><a href="https://solar.teztour.com/">solar.teztour.com</a></td>
    <td>10.7.80.63</td>
    <td>Боевой почтовый сервер CommunigatePro (mail.tez-tour.com)</td>
</tr>
<tr>
    <th>81</th>
    <td><a href="https://solar.teztour.com/">solar.teztour.com</a></td>
    <td>10.0.0.6</td>
    <td>Тестовый Oracle DB сервер разработчиков</td>
</tr>
<tr>
    <th>82</th>
    <td><a href="https://spok.teztour.com/">spok.teztour.com</a></td>
    <td>10.0.0.12</td>
    <td>Боевой сервер Oracle DB подбора туров</td>
</tr>
<tr>
    <th>83</th>
    <td><a href="https://spom.teztour.com/">spom.teztour.com</a></td>
    <td>10.7.74.12</td>
    <td>Боевой сервер Oracle DB подбора туров</td>
</tr>
<tr>
    <th>84</th>
    <td><a href="https://subscribe.tez-tour.com/">subscribe.tez-tour.com</a></td>
    <td>10.0.0.114</td>
    <td>Сервер почтовых рассылок Mailman</td>
</tr>
<tr>
    <th>85</th>
    <td><a href="https://syrup.tez-tour.com/">syrup.tez-tour.com</a></td>
    <td>10.0.0.110</td>
    <td>Proxy-сервер SQUID на 3Data</td>
</tr>
<tr>
    <th>86</th>
    <td><a href="https://tariffk.teztour.com/">tariffk.teztour.com</a></td>
    <td>10.0.0.80</td>
    <td>Боевой сервер Oracle DB подбора туров</td>
</tr>
<tr>
    <th>87</th>
    <td><a href="https://tariffk2.teztour.com/">tariffk2.teztour.com</a></td>
    <td>10.0.0.120</td>
    <td>Боевой сервер Oracle DB подбора туров</td>
</tr>
<tr>
    <th>88</th>
    <td><a href="https://tariffm.teztour.com/">tariffm.teztour.com</a></td>
    <td>10.7.74.80</td>
    <td>Боевой сервер Oracle DB подбора туров</td>
</tr>
<tr>
    <th>89</th>
    <td><a href="https://tariffm2.teztour.com/">tariffm2.teztour.com</a></td>
    <td>10.7.74.120</td>
    <td>Боевой сервер Oracle DB подбора туров</td>
</tr>
<tr>
    <th>90</th>
    <td><a href="https://tbs.teztour.com/">tbs.teztour.com</a></td>
    <td>10.7.74.89</td>
    <td>Боевой Oracle DB сервер TBS</td>
</tr>
<tr>
    <th>91</th>
    <td><a href="https://tbsdev.teztour.com/">tbsdev.teztour.com</a></td>
    <td>172.25.33.158</td>
    <td>Тестовый Oracle DB сервер разработчиков TBS (Минск)</td>
</tr>
<tr>
    <th>92</th>
    <td><a href="https://teztour.ro/">teztour.ro</a></td>
    <td>10.7.74.118</td>
    <td>Сайт TEZ TOUR Румыния</td>
</tr>
<tr>
    <th>93</th>
    <td><a href="https://tir.teztour.com/">tir.teztour.com</a></td>
    <td>10.7.74.203</td>
    <td>Тестовый сервер для web-разработчиков (www,online,xmlgate,search и т.д)</td>
</tr>
<tr>
    <th>94</th>
    <td><a href="https://truba.teztour.com/">truba.teztour.com</a></td>
    <td>10.0.0.50</td>
    <td>Nagios, RADIUS-сервер (авторизация для VPN)</td>
</tr>
<tr>
    <th>95</th>
    <td><a href="https://turk.teztour.com/">turk.teztour.com</a></td>
    <td>10.0.4.197</td>
    <td>Веб-сервер турецких приложений (operation reservation agency best bigblue center dooel granitas gt-group guide hotels list shopping sport travel turist
veneta ws.tezagency.com ws.tezhotels.com ws.teztour.com.tr erp traveleg trans infoboard dooel-ar tracking notification infoeg shopguide icontactws)</td>
</tr>
<tr>
    <th>96</th>
    <td><a href="https://turkm.tez-tour.com/">turkm.tez-tour.com</a></td>
    <td>10.7.80.197</td>
    <td>Веб-сервер турецких приложений (operation reservation agency best bigblue center dooel granitas gt-group guide hotels list shopping sport travel turist
veneta ws.tezagency.com ws.tezhotels.com ws.teztour.com.tr erp traveleg trans infoboard dooel-ar tracking notification infoeg shopguide icontactws)</td>
</tr>
<tr>
    <th>97</th>
    <td><a href="https://udon.teztour.com/">udon.teztour.com</a></td>
    <td>10.38.10.63</td>
    <td>LDAP-сервер, RADIUS-сервер (КИЕВ)</td>
</tr>
<tr>
    <th>98</th>
    <td><a href="https://voipcrm.teztour.com/">voipcrm.teztour.com</a></td>
    <td>10.0.0.99</td>
    <td>Система CRM колл-центра (г. Москва)</td>
</tr>
<tr>
    <th>99</th>
    <td><a href="https://ws.services.teztour.com/">ws.services.teztour.com</a></td>
    <td>10.0.0.111</td>
    <td>Веб-сервер турецких приложений (iguide, cron.teztour.com.tr, cron-ws)</td>
</tr>
<tr>
    <th>100</th>
    <td><a href="https://xmpp.tez-tour.com/">xmpp.tez-tour.com</a></td>
    <td>10.0.0.65</td>
    <td>XMPP Jabber-сервер</td>
</tr>
<tr>
    <th>101</th>
    <td><a href="https://zabbix.teztour.com/">zabbix.teztour.com</a></td>
    <td>10.0.0.104</td>
    <td>Zabbix-сервер</td>
</tr>
<tr>
    <th>102</th>
    <td><a href="https://zeus.teztour.com/">zeus.teztour.com</a></td>
    <td>10.0.4.57</td>
    <td>Боевой веб-сервер (www,online,xmlgate,search и т.д)</td>
</tr>
</table>
</body>
</html>',NULL,1);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (5,'Должностная инструкция специалиста техподдержки','2024-04-15 16:42:22.897439','<p style="font-size: 18px; text-align: left;">📌<strong>Общие положения</strong></p>
<p style="font-size: 14px; text-align: left;">Специалист службы технической поддержки (далее &ndash; Специалист) относится к категории работников отдела системной интеграции, принимаемых на работу и увольняемых Генеральным директором организации. Основная задача деятельности Специалиста &ndash; удовлетворение потребностей сотрудников в использовании разрабатываемых в техническом отделе компании программных продуктов, принятие мер для обеспечения бесперебойной работы средств автоматизации, сервисов и серверов в сети.</p>
<p style="font-size: 14px; text-align: left;">Специалист находится в прямом подчинении руководителя отдела системной интеграции. Специалист контролирует на всех этапах своей деятельности соблюдение требований действующих в компании стандартов, руководящих и методических документов.</p>
<p style="font-size: 14px; text-align: left;">Специалист должен руководствоваться в своей деятельности:</p>
<p style="font-size: 14px; text-align: left;">правилами эксплуатации компьютерной техники; правилами внутреннего трудового распорядка; постановлениями, распоряжениями, приказами и другими руководящими и нормативными документами компании; правилами и нормами охраны труда, техники безопасности, производственной санитарии и противопожарной защиты; настоящей должностной инструкцией; основами организации труда; законодательством о труде и охране труда РФ; использовать только те информационные ресурсы, доступ к которым был получен официально; доступ к ресурсам, который не был согласован установленным образом (авторизован), является нарушением информационной безопасности компании.</p>
<p style="font-size: 14px; text-align: left;">Настоящая должностная инструкция составлена в двух экземплярах, один из которых храниться у компании, другой у работника.</p>
<p style="font-size: 18px; text-align: left;">📌<strong>Требования к квалификации</strong></p>
<p style="font-size: 14px; text-align: left;">Специалист должен иметь высшее образование или среднее техническое образование со специальной подготовкой (переподготовкой), со стажем работы не менее 2 лет.&gt;</p>
<p style="font-size: 14px; text-align: left;">Специалист должен знать:<br><br>🔹 Конфигурацию и технические особенности компьютерной техники, оборудования, правила пользования ими, эксплуатационные параметры вычислительных систем;<br> 🔹 Устройство и технические особенности вычислительных сетей;<br> 🔹 Профессиональные навыки работы в операционных системах MS Windows 9х &ndash;<br> XP (установка, настройка, решение проблем в работе);<br> 🔹 Программы стандартного офисного набора: MS Office,ICQ,The Bat,Thunderbird;<br> 🔹 Основные функции офисных АТС;<br> 🔹 Базовые знания о средствах разработки программных продуктов используемых в компании;<br> 🔹 Знания в области общего программного обеспечения;<br> 🔹 Правила техники безопасности и охраны труда, противопожарной безопасности;<br> 🔹 Функциональные комплексы задач, решаемые в эксплуатируемых в компании программных системах.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Должностные обязанности</strong></p>

<p style="font-size: 14px; text-align: left;">В обязанности Специалиста входит:<br><br>

🔹Соблюдение правил внутреннего трудового распорядка, охраны труда и техники безопасности;<br>
🔹Соблюдение требований действующих в компании стандартов, руководящих и методических документов;<br>
🔹Обслуживание входящих звонков “горячей линии” тел. 775-10-09, 660-10-09;<br>
🔹Изучение состава и функций внешних и внутренних сервисов компании, 🔹поддержка актуальной внутренней документации по ним;<br>
🔹Прием и регистрация поступающих заявок, обращений и пожеланий пользователей в автоматизированной системе учета и управления заявками и передача этих заявок в рабочие группы для исполнения;<br>
🔹Исполнение заявок и обращений, поступающих от сотрудников в рамках своей компетенции в случае возможности их выполнения, а так же поручений руководства департамента;<br>
🔹Информирование руководства отдела о просроченных и не исполненных задачах;<br>
🔹Эскалация технических проблем на вышестоящий уровень при невозможности своевременного самостоятельного их решения;<br>
🔹Постоянное повышение квалификации;<br>
🔹Рекомендации по оптимальной конфигурации и настройке компьютерной техники пользователей для обеспечения их оптимальной работы;<br>
🔹Тесное взаимодействие с коллегами, обмен с ними профессиональными знаниями и опытом;<br>
🔹Выполнение других поручений непосредственного руководства в рамках своих должностных обязанностей;</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Права</strong></p>
<p style="font-size: 14px; text-align: left;">Специалист имеет право:
 <br>🔹 Пользоваться всеми льготами, предоставляемыми предприятием в соответствии с условиями трудового договора и действующим законодательством;
<br>🔹 Вносить предложения по совершенствованию работ, связанных со своей деятельностью; 
<br>🔹 Требовать от руководства обеспечения необходимых условий для выполнения своих обязанностей, а так же информацию, необходимую для выполнения возложенных функций;
<br>🔹 Принимать самостоятельные решения по вопросам своей компетенции. <br>🔹 Докладывать руководителю обо всех выявленных недостатках в пределах своей компетенции;
<br>🔹 Взаимодействовать со всеми отделами(сотрудниками) по вопросам своей деятельности; 
<br>🔹 Выходить к непосредственному руководству с предложениями по улучшению/изменению условий труда;</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Ответственность</strong></p>

<p style="font-size: 14px; text-align: left;">Специалист несет ответственность за:<br><br>
<br>🔹 Ненадлежащее выполнение своих обязанностей.
<br>🔹 Нетактичное отношение к сотрудникам отдела и компании, а так же к обращающимся по телефону и другим каналам связи в службу технической поддержки по различным вопросам;
<br>🔹 Качество и своевременность выполнения возложенных на него настоящей инструкцией обязанностей и за своевременное информирование вышестоящего руководства о задержках и проблемах, возникших работе;
<br>🔹 Неправомерные действия с документами и информацией о деятельности организации и сохранение коммерческих тайн организации;</p>
  
<p style="font-size: 14px; text-align: left;">Дисциплинарная, материальная и иная ответственность Специалиста определяется в соответствии с действующим законодательством;</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Контроль выполнения</strong></p>

<p style="font-size: 14px; text-align: left;">Контроль за выполнением данной должностной инструкции возлагается на руководителя службы технической поддержки.</p>

<p style="font-size: 14px; text-align: left;"><strong>Обязанности специалиста службы поддержки:</strong>strong><br>

<p style="font-size: 14px; text-align: left;">Специалист службы технической поддержки отвечает за своевременный прием и регистрацию поступающих заявок, обращений и пожеланий сотрудников компании.
<br>🔹 Принимает входящие звонки;
<br>🔹 При поступлении заявок от сотрудников компании по почте или другим каналам связи оперативно их регистрирует в системе автоматизированной системе управления заявками (далее по тексту Easy Redmine);
<br>🔹 Контролирует задачи в системе на предмет не назначенных, не решённых, важных или просроченных задач;
<br>🔹 Следит за своевременностью назначения ответственных исполнителей по задачам старшими в группах (взятия на решение задач исполнителями). В случае задержки назначения исполнителей напоминать об этом старшим в группах; 
<br>🔹 Уведомляет сотрудников, инициаторов заявок по телефону или электронным письмом о факте начала итсполнения задачи соответвующим специалистом.
<br>🔹 После исполнения задачи уведомлять сотрудников о факте решения задачи; 
<br>🔹 Уведомляет сотрудников (устно или письмом) о случаях задержки исполнения задач с доведением до них новых сроков исполнения;
  В случае обнаружения просроченных задач уведомляет устно или электронным письмом непосредственных исполнителей; 
<br>🔹 Ежедневно, периодически  проверяет состояние работы технических средств и оборудования серверной и коммуникационной комнат путем личного осмотра; 
<br>🔹  Своевременно докладывает руководству отдела и другим ответственным сотрудникам об обнаруженных недостатках (сбоях) в работе технического оборудования;</p> 

<p style="font-size: 18px; text-align: left;">📌<strong>Обязанности по проверке технического оборудования</strong></p>

<p style="font-size: 14px; text-align: left;">При проверке оборудования, находящегося в серверной, коммуникационной, помещении технического отдела производить визуальный осмотр технических средств. Немедленно оповещать администраторов отдела при обнаружении неисправностей в работе технических средств в рабочее время, во внерабочее время – непосредственного руководителя или руководство отдела. В случае возникновения форс-мажорных обстоятельств в дневное или ночное время (отключение электропитания, задымление и т.п.) немедленно оповещать охрану и руководство отдела. Путем осмотра убедится в работоспособности следующего оборудования: Серверная: кондиционеры (рабочая температура должна быть постоянно в пределах 18-20 градусов); серверов размещенных в стойках; сервера (почтовый, Novell, Barer, проверить работоспособность с помощью консоли переключения); оборудование Cisco; ИБП APC серии Symmetra LX; источники бесперебойного питания; проверять степень нагрева коробов электропроводки. Коммуникационная: источники бесперебойного питания; сетевые коммутаторы; оборудование АТС. Помещение отделов: в рабочее время проверять (не менее двух раз в рабочее время) состояние бачков для слива конденсата от работы кондиционеров; в нерабочее время окна должны быть закрыты, кондиционеры, электронагревательные приборы (электрочайники, кофеварки и пр.) выключены, компьютеры на рабочих местах сотрудников, кроме работающих круглосуточно выключены, мониторы выключены на всех компьютерах. Осуществлять контроль общего технического состояния на рабочем месте следующих объектов: сервера баз данных; репликация данных; прокси-сервер; почтовый сервер; музыка на hold-e на АТС.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Порядок ответа на входящие телефонные звонки горячей линии</strong></p>

<p style="font-size: 14px; text-align: left;">Время работы службы технической поддержки: рабочие дни, с 10:00 до 19:00. Телефоны горячей линии: 775-10-09, 660-10-09

<br>🔹Представиться ("Здравствуйте, технический отдел TEZTOUR, имя");
<br>🔹Уточнить, кто звонит и по какому вопросу. В случае, если задача уже создана в системе уточнить её номер в системе для ее быстрого поиска;
<br>🔹Провести первичную диагностику ситуации;
<br>🔹Определить категорию проблемы;
<br>🔹Приступить к её решению;
<br>🔹Если вопрос не представляется решить сразу, звонящему назвать срок, в течение которого он получит ответ, и способ ответа (почта, повторный звонок или самостоятельный звонок);
<br>🔹При невозможности разрешения ситуации своими силами, проблема эскалируется исполнителям 2-ой линии поддержки;</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Порядок обработки почтовых обращений</strong></p>

<p style="font-size: 14px; text-align: left;">Все почтовые сообщения, поступающие на адрес help@tez-tour.com заносятся в систему.
<br>🔹Уясняя задачу, назначить непосредственного исполнителя или группу исполнителей задачи;
<br>🔹Все обращения пользователей регистрируются в базе данных системы;
В базе хранится информация об идентификационных данных пользователя, о дате обращения, содержании вопроса и содержании ответа на обращение;
<br>🔹Зарегистрированному обращению (заявке) присваивается уникальный номер, который сообщается заявителю;
<br>🔹Пользователь может получить информацию о состоянии выполнения заявки. Для этого пользователю необходимо ответить на автоматически полученное письмо-уведомление от службы технической поддержки либо уточнить информацию по телефону, сообщив номер обращения;
<br>🔹Время реагирования на обращение, поступившее по электронной почте, составляет до 30 мин. За это время созданная по обращению заявка должна быть назначена на исполнителя или же переведена в статус в "В работе";
<br>🔹1 линия поддержки может запросить любую дополнительную информацию по проблеме;
<br>🔹Ответы на стандартные, часто задаваемые вопросы, могут быть даны в виде ссылок на пояснительные материалы;</p>',NULL,1);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (6,'Несколько советов для сотрудника техподдержки','2024-04-15 16:43:18.500366','<p style="font-size: 18px; text-align: left;">📌<strong>Дайте пользователю надежду на то, что вы ему поможете</p>
<p style="font-size: 14px; text-align: left;">Для вас звонок пользователя – это новое обращение. Пользователь на свою проблему уже потратил достаточно времени – попытки самостоятельно разобраться, ожидание на телефонной линии и т.п. Стоит ли удивляться изначально негативному настрою? Выслушайте, наконец, в чем состоит его проблема, и только потом переходите к уточнению личности пользователя, отдела, и т.п.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Дайте пользователю надежду на то, что вы ему поможете</p>
<p style="font-size: 14px; text-align: left;">Прежде чем решать проблему, убедитесь, что вы беретесь за решение правильной проблемы.
Можно потратить полчаса на попытку разобраться с проблемой, которой не существует. Для начала стоит убедиться, что ситуация, которую видит пользователь, не является частью более крупного инцидента, который он пока не заметил.</p>

<p style="font-size: 14px; text-align: left;">Например, пользователь звонит с обращением <i>«У меня мышка залипает»</i>.</p>

<p style="font-size: 14px; text-align: left;">Один сценарий выяснять: оптическая или механическая, проводная или беспроводная, светиться ли диод и светился ли он раньше и т.п. Разговоров на 20 минут, а до проблемы вы можете так и не добраться.</p>

<p style="font-size: 14px; text-align: left;">Попробуем зайти с другого конца: <i>«Итак, у вас не работает мышь, а все остальное на компьютере работает нормально?</i> Попробуйте перейти в другую программу при помощи клавиш «Alt» + «Tab» или запустить программу из стартового меню при помощи «Ctrl»+«Esc» и стрелок».</p>

<p style="font-size: 14px; text-align: left;">Если все работает, то можно попытаться выяснить, что случилось с мышкой. Если же нет, то мышь не причем и разбираться нужно уже с компьютером.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Не стоит выяснять, что пользователь уже делал</strong></p>
<p style="font-size: 14px; text-align: left;">Типичный стереотип, которому подвержены сотрудники техподдержки – 80% проблем пользователей исправляются фразой <i>«А вы пробовали выключить и включить?»</i>. Ну да, это часто срабатывает. В то же время, большинство пользователей достаточно хорошо знакомы с компьютером, чтобы проделать такие шаги самостоятельно.</p>

<p style="font-size: 14px; text-align: left;">Они отвечают «Да», даже не задумываясь над каждым вашим «Вы уже пробовали…»</p>

<p style="font-size: 14px; text-align: left;">- Вы пробовали выключить и включить?</p>

<p style="font-size: 14px; text-align: left;">- Да</p>

<p style="font-size: 14px; text-align: left;">- Вы держали нажатыми [Ctrl] и [Alt], когда нажимали [Delete]?”</p>

<p style="font-size: 14px; text-align: left;">- Да</p>

<p style="font-size: 14px; text-align: left;">- Вы держали компьютер над головой, когда выполняли ритуальный танец?</p>

<p style="font-size: 14px; text-align: left;">- Да</p>

<p style="font-size: 14px; text-align: left;">Вместо того, чтобы спрашивать, что пользователь уже делал, намного эффективнее дать пользователю задание, которое он должен проделать прямо сейчас и говорить с ним о том, что он видел. Эффективный метод – проделать по шагам весь путь пользователя к его ошибкам, например, запустив у себя те же программы. Если ошибка появится и на вашем компьютере, то это хорошая причина эскалировать инцидент другим специалистам.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Техподдержка должна использовать туже рабочую среду, что и большинство пользователей</strong></p>
<p style="font-size: 14px; text-align: left;">Нельзя посадить техподдержку на Linux, если пользователи работают в Windows. Не стоит мигрировать техподдержку на Windows 10, если в компании все еще активно используется Windows 7. Очень важно для сотрудника техподдержки иметь среду близкую к той, что у пользователя на компьютере. Так он может предсказать нормальное поведение компьютера и подсказать пользователю правильные шаги. Рабочая среда компьютера – лучшая подсказка в любых ситуациях, если вы хотя бы примерно знаете, что нужно делать.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Не притворяйтесь, что знаете больше, чем на самом деле</strong></p>
<p style="font-size: 14px; text-align: left;">Многие пользователи считают, что техподдержка должна знать абсолютно все о компьютерах и программном обеспечении. Мы с вами знаем, что среди тех кто работает на первой линии таких людей нет, но очень многие пытаются ими притворяться. Часто техподдержка пытается угадать правильное решение. В итоге пара неудачных догадок и вы полностью теряете доверие пользователей. Что же делать? Честность – лучшая политика. Если вы не знаете решения и не можете передать пользователя тому, кто знает, то попытайтесь разобраться в ситуации вместе с пользователем. Поищите в интернете, спросите не нашел ли пользователь там решение, попробуйте вместе с пользователем пройти это решение. Многие чувствуют себя глупо и неуверенно, общаясь с техподдержкой. Вовлечение пользователя в поиск решения может придать им уверенность в себе и повысить удовлетворенность от общения с техподдержкой.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Внимательно слушайте пользователей</strong></p>
<p style="font-size: 14px; text-align: left;">Недостаточно просто услышать слова пользователя, нужно понять его интонацию, и, самое главное, оценить важность обращения. Даже если с вашей точки зрения у пользователя несущественная проблема, для него это очень важно, потому что, обращаясь за помощью, он теряет свое драгоценное рабочее время.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Реагируйте на проблемы пользователей</strong></p>
<p style="font-size: 14px; text-align: left;">Никому не хочется слышать: «Мы не можем Вам помочь». Даже если вы не можете удовлетворить все потребности пользователей и исправить все их проблемы, всегда можно сделать что-то, чтобы помочь им справиться с возникшими трудностями.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Относитесь к пользователям по-человечески</strong></p>
<p style="font-size: 14px; text-align: left;">Узнаете, кто они, как их зовут и в чем заключается их проблема. Не забывайте, что это – люди, а не запросы.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Расскажите пользователям о работе службы поддержки</strong></p>
<p style="font-size: 14px; text-align: left;">Если бы пользователи знали проблемы, с которыми вам приходится иметь дело, они бы меньше жаловались на службу поддержки. Расскажите им, как работает ваша служба. У вас может быть лучшая служба техподдержки, но если пользователи не понимают, как она работает, они могут попросту запутаться, потерять терпение и разозлиться на вас.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Научитесь извиняться</strong></p>
<p style="font-size: 14px; text-align: left;"Нужно уметь извиняться за ошибки ИТ-отдела, даже если виноваты не вы. Пользователю неважно из-за кого возникла проблема, ему нужен кто-то, кто возьмет на себя ответственность за допущенную ошибку и поможет ее исправить.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Организуйте регулярную обратную связь</strong></p>
<p style="font-size: 14px; text-align: left;"Поощряйте и приветствуйте предложения пользователей по улучшению работы службы поддержки. Это поможет вам предотвратить вероятные проблемы с поддержкой и лучше понять своих пользователей.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Обеспечьте открытость работы службы поддержки</strong></p>
<p style="font-size: 14px; text-align: left;">Пользователи должны знать, какие работы по улучшению предоставления ИТ-услуг были проделаны и ведутся в настоящее время. Нужно информировать пользователей о потенциальных проблемах или предстоящих простоях. Они должны знать, когда планируется техническое обслуживание ИТ-систем, из-за которого у них не будет доступа к корпоративным сетям или сервисам.</p>
<p style="font-size: 18px; text-align: left;">📌<strong>Поддерживайте всех сотрудников компании</strong></p>
<p style="font-size: 14px; text-align: left;">Вы должны понимать, что не все работают в офисе, есть сотрудники, которые работают удаленно. Им нельзя сказать: «Мы решим проблему, когда Вы будете в офисе». Они так же важны для компании, как и сотрудники, которые работают в офисе, и их проблемы не менее критичны.</p>

<p style="font-size: 18px; text-align: left;">📌<strong>Ваша цель сделать пользователя счастливым</strong></p>
<p style="font-size: 14px; text-align: left;">ИТ-специалисты в большинстве случаев не считают себя воспитателями детского сада для пользователей. Даже шутки при общении с пользователями чаще всего специфические и мало понятные «простым смертным». Задача техподдержки – помочь и поддержать пользователей. Если пользователи завершат разговор довольными, то и вы скорее всего будете чувствовать удовлетворение от хорошей работы, а значит и работать будет значительно легче.</p>
','0e90c0d60d9f8307b4c9b9e75c5ab61f.png',1);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (7,'Обновление настроек Vacuum-IM для Минского офиса','2024-07-12 19:06:54.879777','Минский офис перешел на новый почтовый домен tez-tour.by. 
В связи с изменением почтового адреса в карточке ERP на новый домен (tez-tour.by), при подключении к вакууму необходимо будет указывать домен tez-tour.by. Если подключение не удается, в настройках указать адрес хоста: xmpp.tez-tour.com.
Обновление ростера происходит раз в сутки в 21:00.
Пожалуйста, убедитесь, что все настройки подключения обновлены.','79e16f3f31f282da2f5817d9227a8d4a.png',1);
INSERT INTO "posts" ("id","title","date_posted","content","image_post","user_id") VALUES (8,'Изменились email адреса офиса в МИНСКЕ','2024-09-13 12:13:59.059534','<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Обновление почтовых адресов</title>
    <style>
        .centered-list {
            text-align: center; /* Центрирование текста */
            margin: 0 auto; /* Автоматические отступы для центрирования контейнера */
            display: inline-block; /* Позволяет элементу занимать ширину содержимого */
        }
        .department {
            text-align: left; /* Выравнивание текста по левому краю для каждого элемента списка */
        }
    </style>
</head>
<body>
    <p>Обращаем внимание, что офис в <strong>МИНСКЕ</strong> перешел на новый почтовый сервер <a href="mailto:@tez-tour.by">@tez-tour.by</a></p>

    <p>Общие адреса отделов дублирую ниже, личные адреса сотрудников можно проверить в ЕРП - Контакты - Офис в Минске (данные уже обновлены). В личных адресах изменилось только название сервера, названия (имя) почтового ящика сохранилось. Если вы использовали какие-то наши адреса для рассылок/групп - замените, пожалуйста, на новые адреса.</p>

    <div class="centered-list">
        <p class="department">Отдел продаж: <a href="mailto:info@tez-tour.by">info@tez-tour.by</a></p>
        <p class="department">Отдел бронирования: <a href="mailto:book@tez-tour.by">book@tez-tour.by</a></p>
        <p class="department">Отдел маркетинга: <a href="mailto:calc@tez-tour.by">calc@tez-tour.by</a></p>
        <p class="department">Юридический отдел: <a href="mailto:pravo@tez-tour.by">pravo@tez-tour.by</a></p>
        <p class="department">Отдел выдачи: <a href="mailto:voucher@tez-tour.by">voucher@tez-tour.by</a></p>
        <p class="department">Визовый отдел: <a href="mailto:visa@tez-tour.by">visa@tez-tour.by</a></p>
        <p class="department">Бухгалтерия: <a href="mailto:buh@tez-tour.by">buh@tez-tour.by</a></p>
        <p class="department">Online продажи: <a href="mailto:support@tez-tour.by">support@tez-tour.by</a></p>
        <p class="department">Отдел рекламы и PR: <a href="mailto:reklama@tez-tour.by">reklama@tez-tour.by</a></p>
        <p class="department">MICE отдел: <a href="mailto:mice@tez-tour.by">mice@tez-tour.by</a></p>
    </div>
</body>
</html>',NULL,1);
INSERT INTO "push_subscriptions" ("id","user_id","endpoint","p256dh_key","auth_key","user_agent","created_at","last_used","is_active") VALUES (326,1,'https://fcm.googleapis.com/wp/fvqnswzqp24:APA91bHYE60ExCzGk-OG3oHnPw28zD-NdBs0_-ngOY0E-kIW-Dud2O1chc5ZCMZpue0XJWBToOlk1gcnHrNpewGBZyf-0K3-fddRiQJR8JbbI9Bb01gAAJ2kSiUuQ1Pumgrk3KrcOsvr','BFWgFoxolMNDgB7qa7iyzYq6jcgoAGdsdt8_ND8FhJpdUkRhb4L3ImGaGGm_rg7h042pwnnOgV7P6bsrNFoJDIw','d8tc3HHnARfJPbHjdeipow','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36','2025-05-30 20:02:42.148010','2025-05-30 20:02:56.591595',0);
INSERT INTO "push_subscriptions" ("id","user_id","endpoint","p256dh_key","auth_key","user_agent","created_at","last_used","is_active") VALUES (327,1,'https://fcm.googleapis.com/wp/dvSMg4EvAcw:APA91bFjcHSOkyUzPo8KJee2V5K2fQM5MFuTsOoZaj2idkC9pGDjDZG3RAJyXwwFwzlKWctuPr0npdBYmHJDlPhh96shzC33V-8P1U0O84Vzr_LF4jz2zqiIz0jRwYM6UF3bwflrluEp','BHBfty7X-kKhk2iCNHrtukjieR-RpWQlbXT2_DTGqK81UpP7JI8JzfYNMIWFR6dKKAqEbjWHIIHK5mblhts3iuA','5l8sDiOSNE1yFCLPb-gM3A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36','2025-05-30 20:03:14.160005','2025-05-30 20:03:34.816388',1);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (1,'y.varslavan','ВАРСЛАВАН ЮРИЙ ЯНОВИЧ','Srw$523U$','y.varslavan@tez-tour.com','Офис в Москве','2025-06-01 02:14:43.543643','Служба техподдержки','Руководитель службы техподдержки','1081','9cb4d293702379b3c8e0.JPG',1,'<Дата не определена>',1,0,1,7,1,1,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (2,'n.predkina','ПРЕДКИНА НАТАЛЬЯ АЛЕКСАНДРОВНА','kvdwfTKC8','n.predkina@tez-tour.com','Офис в Москве','2024-04-02 20:06:08.192448','Отдел продукта','Менеджер','1041','fdd10448ed58bbf18202.jpg',1,'2024-07-28 00:00:00',0,0,1,380,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (3,'d.gavrishin','ГАВРИШИН ДМИТРИЙ АЛЕКСАНДРОВИЧ','kve4SWDU6','d.gavrishin@tez-tour.com','Офис в Москве','2025-06-01 02:16:48.322951','Отдел системной интеграции','Специалист технической поддержки','1012','d0caf6cf7a08094d4808.jpg',1,'<Дата не определена>',1,1,1,23,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (4,'k.m.kazieva','КАЗИЕВА КАМИЛА МАГОМЕДОВНА','qWpftLBXX','k.kazieva@tez-tour.com','Офис в Москве','2024-04-25 23:17:08.185971','Отдел развития агентской сети','Менеджер по работе с агентствами','2170','a32ee98d9a06bb39ea33.png',1,'2024-03-23 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (5,'Evitch','ЕВИЧ ПОЛИНА ЮРЬЕВНА','xRLEHP2Mt','p.evich@tez-tour.com','Офис в Москве','2025-06-01 02:16:21.170972','Отдел контроля качества','Руководитель отдела по контролю за качеством','1047','User 05.jpg',1,'2024-11-30',0,0,0,4,0,1,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (6,'a.pavlov','ПАВЛОВ АНДРЕЙ СЕРГЕЕВИЧ','Cr6X8bBQB','a.pavlov@tez-tour.com','Офис в Москве','2024-04-17 14:42:46.613045','Отдел программных разработок','Специалист технической поддержки','4415','png-transparent-businessperson-computer-icons-avatar-passport-miscellaneous-purple-heroes.png',1,'2025-03-17 00:00:00',0,0,1,21,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (7,'m.martynov','МАРТЫНОВ МАКСИМ ОЛЕГОВИЧ','EX4HPpr','m.martynov@tez-tour.com','Офис в Москве','2024-04-27 18:57:42.384898','Отдел программных разработок','Специалист технической поддержки','1049','User 17.jpg',1,'2025-03-17 00:00:00',0,0,1,97,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (8,'a.atemasov','АТЕМАСОВ АНАТОЛИЙ ВАЛЕРЬЕВИЧ','QZfVbFwvM','a.atemasov@tez-tour.com','Офис в Москве','2024-04-25 22:36:42.118707','Отдел программных разработок','Программист','1428','User 18.jpg',1,'<Дата не определена>',0,0,1,33,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (9,'Hodakov','ХОДАКОВ АЛЕКСЕЙ СЕРГЕЕВИЧ','dBjZPgqU8','a.hodakov@tez-tour.com','Офис в Москве','2024-11-01 15:55:11.295484','Исполнительный департамент','И.о. руководителя','1042','User 01.jpg',1,'2025-02-28',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (10,'e.danilov','ДАНИЛОВ ЕГОР СЕРГЕЕВИЧ','WNAYnmTb8','egor@teztour.com.md','Офис в Кишиневе','2025-04-14 16:16:59.270060','Отдел бронирования ','Менеджер по бронированию',NULL,'1d0c48a10d45d4fab374.jpg',1,'2024-10-21 00:00:00',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (11,'Sannikov','САННИКОВ ЕВГЕНИЙ','3Qru9re7a','e.sannikov@teztour.lt','Офис в Вильнюсе','2024-04-26 12:05:57.999721','IT отдел','Руководитель IT-отдела ','7434','2048x1404-px-colorful-glasses-1192242.jpg',1,'2024-07-31 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (12,'e.shmidt','ДОРОШИНА ЕЛЕНА ВИКТОРОВНА','mnexYP6VV','e.shmidt@kras.tez-tour.com','Офис в Красноярске','2024-12-20 12:50:00.671765','Отдел продаж и бронирования','Менеджер','1094','User 19.jpg',1,'2024-07-14 00:00:00',1,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (13,'l.vlaskin','ВЛАСКИН ЛЕОНИД АНАТОЛЬЕВИЧ','$Sun7sz','l.vlaskin@tez-tour.com','Офис в Москве','2024-04-27 13:30:18.546483','Отдел Web-разработок','Аналитик','1430','415502db09ca5c3e80ab.png',1,'2024-11-01 00:00:00',0,0,1,5,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (14,'z.kabalina','КАБАЛИНА ЖАННА АЛЕКСАНДРОВНА','vcFTpgKgt','j.kabalina@kras.tez-tour.com','Офис в Красноярске','2024-04-28 00:14:02.744104','Руководство','Руководитель офиса','1095','unnamed.jpg',1,'2024-07-21 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (15,'i.petrova','ГРИБАНОВА(ПЕТРОВА) ИРИНА ОРЕСТОВНА','Ak7aDMxp2','i.petrova@tez-tour.com','Офис в Москве','2024-04-26 08:57:36.134180','Отдел Web-разработок','Редактор (контент-менеджер)','1435','1646494997_39-kartinkin-net-p-krasivie-kartinki-na-avu-dlya-zhenshchin-51.jpg',1,'2024-11-01 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (16,'o.rasko','РАСЬКО ОЛЬГА ФРАНЦЕВНА','hPobQkmro','o.rasko@minsk.tez-tour.com','Офис в Минске','2024-08-28 20:57:20.244692','Отдел по работе с корпоративными клиентами','Ведущий специалист по обслуживанию корпоративных клиентов','2614','I7GkwTCXWxQ.jpg',1,'2024-12-31',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (17,'a.tskhai','ЦХАЙ АЛЛА СЕРГЕЕВНА','tzEuQN3BL','a.tskhai@nsk.tez-tour.com','Офис в Новосибирске ','2025-03-13 12:33:35.396223','Отдел продаж и бронирования','Менеджер по бронированию','4405','User 19.jpg',0,'<Дата не определена>',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (18,'o.a.bobkova','БОБКОВА ОЛЬГА АЛЕКСЕЕВНА','6wJ456xQa','o.a.bobkova@tez-tour.com','Офис в Москве','2024-09-23 19:19:46.301509','Отдел продаж','Оператор','1918','User 18.jpg',1,'2024-10-01 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (19,'e.zaripov','ЗАРИПОВ ЭДУАРД МИРАСОВИЧ','RNALHhjut','e.zaripov@ufa.tez-tour.com','Офис в Уфе','2024-04-26 09:02:18.906897','Отдел продаж и бронирования','Менеджер','3702','User 15.jpg',1,'2024-07-07 00:00:00',1,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (20,'m.malyutina','МАЛЮТИНА МАРИНА ВАЛЕРЬЕВНА','DkHPqEX3u1','m.malutina@tez-tour.com','Офис в Москве','2024-04-26 09:03:07.175396','Отдел продаж','Менеджер','1919','RF0Cd.jpg',1,'2024-10-01 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (21,'t.zvereva','ЗВЕРЕВА ТАТЬЯНА МИХАЙЛОВНА','Master99iI','t.zvereva@tez-tour.com','Офис в Москве','2025-01-28 08:57:19.355731','Отдел ценообразования','Специалист по ценообразованию','7724','risovanie-avatars-for-girls-pixelbox.ru-51.jpg',1,'2024-07-14 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (22,'i.nedostupova','НЕДОСТУПОВА ИННА ИВАНОВНА','zpqsTQFku1','i.nedostupova@tez-tour.com','Офис в Москве','2024-04-26 09:03:42.178554','Отдел продаж','Оператор','1908','User 12.jpg',1,'2024-10-01 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (23,'a.kovtun','КОВТУН АННА АЛЕКСАНДРОВНА','ueTTgMrKX1','a.kovtun@tez-tour.com','Офис в Москве','2024-04-26 09:03:54.253860','Отдел продаж','Менеджер','1945','risovanie-avatars-for-girls-pixelbox.ru-51.jpg',1,'2024-10-01 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (24,'d.garber','GARBER DMITRI','Home280282','dmitri@teztour.ee','Офис в Таллине','2025-04-08 09:50:10.887987','Отдел по работе с агентствами','Координатор по работе с агентствами','2500','3029316308145ff17b32.jpg',1,'2025-01-26 00:00:00',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (25,'Kolobov','КОЛОБОВ ОЛЕГ ВИКТОРОВИЧ','Kov371%as','o.kolobov@spb.tez-tour.com','Офис в Петербурге','2024-04-26 09:23:10.599554','Отдел бронирования','Ведущий менеджер','2826','User 03.jpg',0,'<Дата не определена>',1,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (26,'e.bolotova','БОЛОТОВА ЕЛЕНА ВЛАДИМИРОВНА','pkJjrFjVk','e.bolotova@tez-tour.com','Офис в Москве','2024-04-26 13:24:48.978077','Отдел ценообразования','Специалист по ценообразованию','4482','d74a806d932b8e4a263f.jpg',1,'2024-07-14 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (27,'m.kushukova','КУШУКОВА МАРИЯ НИКОЛАЕВНА','aWrCvFEbn','m.kushukova@samara.tez-tour.com','Офис в Самаре','2024-04-26 12:33:51.464145','Отдел продаж','Менеджер отдела продаж','3402','ava-vk-animal-91.jpg',1,'2024-06-23 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (28,'ma.pankova','ПАНКОВА МАРГАРИТА АНАТОЛЬЕВНА','cYaFHx6yk','m.pankova@spb.tez-tour.com','Офис в Петербурге','2024-04-26 09:39:48.956389','Отдел продаж','Старший менеджер','2834','risovanie-avatars-for-girls-pixelbox.ru-22.jpg',0,'<Дата не определена>',1,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (29,'a.ismailov','ИСМАИЛОВ АНАР РАФИК','#Juventus1','anar@tez-tour.ro','Офис в Бухаресте','2025-02-17 13:43:33.019596','Отдел по работе с агентствами','Руководитель','3316','3308f39bd54c2911ad4c.png',1,'2024-07-29 00:00:00',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (30,'a.latushkin','ЛАТУШКИН АЛЕКСАНДР ВЛАДИМИРОВИЧ','uKwvmL66X','a.latushkin@tez-tour.com','Офис в Москве','2024-09-16 18:43:50.926471','Отдел оперативно-технической безопасности','Специалист','1097','b29ac8b61d876b0ad1af.jpg',1,'<Дата не определена>',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (31,'s.gubanova','ГУБАНОВА СВЕТЛАНА ВЛАДИМИРОВНА','qUki77Mqm','s.gubanova@spb.tez-tour.com','Офис в Петербурге','2024-04-26 09:42:31.307024','Отдел продаж','Старший менеджер','2808','risovanie-avatars-for-girls-pixelbox.ru-22.jpg',0,'<Дата не определена>',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (32,'a.bubyreva','БУБЫРЕВА АЛЛА ЛЕОНИДОВНА','SLXFsy9ZM','a.bubyreva@belgorod.tez-tour.com','Офис в Белгороде','2024-04-30 22:11:14.396286','Руководство','Руководитель офиса','4434','242680fbb7b541068244.jpg',1,'2024-09-17 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (33,'Chernoglazova','ЧЕРНОГЛАЗОВА АНАСТАСИЯ ВЛАДИМИРОВНА','Chehol4ik','a.chernoglazova@tez-tour.com','Офис в Москве','2024-04-30 22:05:07.106468','Отдел продаж','Менеджер','1917','817039976bc943c8813d.jpg',1,'2024-10-01 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (34,'SKornienko','ШАМАНИНА-БЕЛАСИК СВЕТЛАНА ВЛАДИМИРОВНА','Rmh4cMH9','s.kornienko@spb.tez-tour.com','Офис в Петербурге','2024-04-26 09:52:32.078478','Отдел бронирования','Руководитель отдела','2819','8f3ff5df7c989c2fdd85.jpg',0,'<Дата не определена>',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (35,'r.khalimov','ХАЛИМОВ РУСЛАН КАМЕЛЕВИЧ','WbOznYndx45!','r.halimov@tez-tour.com','Офис в Москве','2024-04-26 10:24:06.561296','Отдел системной интеграции','Системный администратор','1005','bfb26360e1cb918667fb7d4d06be3639.jpeg',1,'<Дата не определена>',0,0,1,9,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (36,'fedorov.a','ФЕДОРОВ АРСЕНИЙ АНДРЕЕВИЧ','5UJDonFRi','a.a.fedorov@tez-tour.com','Офис в Москве','2024-04-26 10:29:24.330879','Отдел системной интеграции','Специалист технической поддержки','1045','User 06.jpg',1,'2024-09-17 00:00:00',0,0,1,395,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (37,'v.pavlov','ПАВЛОВ ВИКТОР ЮРЬЕВИЧ','PavlovV88','v.pavlov@tez-tour.com','Офис в Москве','2024-04-26 22:53:33.978515','Аналитический отдел','Аналитик','4425','f472979bda119ed4409b0628244bf9d4.jpeg',1,'2024-06-03 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (38,'Zhilkina','ЖИЛКИНА НАТАЛЬЯ ЕВГЕНЬЕВНА','z9DA4h9rz1','n.zhilkina@tez-tour.com','Офис в Москве','2024-04-27 12:08:32.727218','Отдел продаж','Менеджер','1915','96e6284182bb16d983437db799f90c9d.jpg',1,'2024-10-01 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (39,'ayman.osama','AYMAN OSAMA','C26ocG@@','ayman.osama@teztour.com','Офис в Каире','2024-04-28 06:50:07.326482','Отдел развития','Руководитель отдела развития','7709','WhatsApp_Image_2021-.jpg',1,'2024-05-26 00:00:00',0,0,1,58,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (40,'y.panchishin','ПАНЧИШИН ЮРИЙ АЛЕКСЕЕВИЧ','ZnLFkT6Lr','y.panchyshyn@teztour.com.ua','Офис в Киеве','2024-04-29 11:35:16.086214','Отдел продаж','Ведущий менеджер','4165','1680202366_pushinka.jpg',1,'2024-06-23 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (41,'e.vardanyan','ВАРДАНЯН ЭДГАР СОСОВИЧ','SXv4nGk7n','e.vardanyan@minsk.tez-tour.com','Офис в Минске','2024-04-30 08:05:04.369872','Отдел бронирования','Руководитель отдела бронирования','2650','avatar_w.jpg',1,'2024-07-28 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (42,'e.surimova','СУРИМОВА ЕКАТЕРИНА ФАРИДОВНА','hyGmQLWmN','e.surimova@ekb.tez-tour.com','Офис в Екатеринбурге','2024-05-13 08:33:51.240232','Отдел бронирования','Руководитель отдела бронирования','3284','62a7a13f73cf7fef90c6.jpg',1,'28.02.2025',1,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (43,'sukov.a','SUKOV ALEXANDER','UKTbmSSTV1','a.sukov@teztour.lt','Офис в Вильнюсе','2024-05-14 11:32:34.215222','Руководство','Директор','7411','avatar_4830521.png',1,'2024-07-31 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (44,'n.prokaeva','ПРОКАЕВА НАТАЛЬЯ АЛЕКСАНДРОВНА','SrUFpmmof','n.prokaeva@tez-tour.com','Офис в Москве','2024-05-14 14:08:01.868075','Отдел бронирования','Старший менеджер','1651','avatar-whatsapp-women-pixelbox.ru-61.jpg',1,'2024-05-26 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (45,'t.gerasimovich','ГЕРАСИМОВИЧ ТАТЬЯНА ЛЕОНИДОВНА','NSfVnHgfS','t.gerasimovich@minsk.tez-tour.com','Офис в Минске','2024-05-15 15:03:23.974368','Бухгалтерия ','Главный бухгалтер','2604','0ccec827e1813340ff12.jpg',0,'<Дата не определена>',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (46,'a.puzanov','ПУЗАНОВ АНДРЕЙ АЛЕКСАНДРОВИЧ','knFZFzUJW','a.puzanov@minsk.tez-tour.com','Офис в Москве','2024-05-22 17:55:08.039331','Отдел бизнес-анализа','Разработчик системы TBS','7703','User 17.jpg',0,'2023-03-19 00:00:00',0,0,1,393,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (47,'Zarkihs','ЖАРКИХ НИКОЛАЙ','pbZrixkmi','nikolajs@teztour.lv','Офис в Риге','2025-03-10 17:18:04.287917','Отдел ценообразования','Маркетолог','123','User 05.jpg',1,'2024-12-31 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (48,'v.sedova','СЕДОВА ВАЛЕРИЯ АЛЕКСАНДРОВНА','vHvjuFbCZ','v.sedova@spb.tez-tour.com','Офис в Петербурге','2025-04-11 12:43:33.850573','Руководство','Генеральный директор','1082','User 06.jpg',0,'2024-03-03 00:00:00',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (49,'Pedchenko','ПЕДЧЕНКО ДМИТРИЙ','KxVBtnrGU','d.pedchenko@tez-tour.com','Офис в Москве','2024-06-10 22:30:09.541127','Отдел бронирования','Старший менеджер','1676','0511b710ebe33fe01fc9.jpg',1,'2024-08-31 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (50,'i.gul','GUL INNARA','C4vadXKJk','innaragul@europeholiday.com.tr','Офис в Анталии','2024-07-12 22:08:49.507764','Отдел бронирования и ценообразования','Помощник руководителя отдела ценообразования','5462','eb98255619da938b0d19.png',1,'2024-08-31 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (51,'k.buzina','БУЗИНА КСЕНИЯ ПАВЛОВНА','Kse3133335','k.buzina@ufa.tez-tour.com','Офис в Уфе','2025-02-15 14:13:21.903210','Аналитический отдел','Маркетолог-аналитик','3703','f472979bda119ed4409b0628244bf9d4.jpeg',1,'2024-07-07 00:00:00',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (52,'s.maltsev','МАЛЬЦЕВ СЕРГЕЙ АЛЕКСАНДРОВИЧ','UUzyBmpvE','s.maltsev@tez-tour.com','Офис в Москве','2024-06-10 14:57:53.090986','Бухгалтерская служба','Бухгалтер','1316','0a175bebefb28201bef6.jpg',1,'2024-09-17 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (53,'i.kuran','КУРАН ИГОРЬ СЕРГЕЕВИЧ','qbo2wRQBH','i.kuran@tez-tour.com','Офис в Москве','2025-04-15 13:15:32.853831','Отдел PR и рекламы','Менеджер',NULL,'477276133eb63ef74b48.png',1,'31.12.2024',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (54,'d.fedotova','ФЕДОТОВА ДАРЬЯ ВИКТОРОВНА','AU4pc6wbG','d.fedotova@ekb.tez-tour.com','Офис в Екатеринбурге','2024-08-08 11:44:42.156951','Отдел продаж','Ведущий менеджер','3282','unnamed.jpg',1,'2024-08-31 00:00:00',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (55,'lepert','ЛЕПЕРТ МАКСИМ СЕРГЕЕВИЧ','rTpqrk5Xg','lepert@teztour.com.ua','Офис в Киеве','2025-02-13 12:19:42.343520','Отдел перевозок и выдачи документов','Менеджер по туризму','4126','png-clipart-computer-icons-user-profile-avatar-heroes-head.png',1,'2024-12-31 00:00:00',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (56,'a.arutyunyants','АРУТЮНЯНЦ АРТЁМ АЛЕКСАНДРОВИЧ','Shady551476','a.arutiuniants@teztour.com.md','Офис в Кишиневе','2025-02-18 14:22:52.364332','Отдел бронирования ','Менеджер по бронированию','+37368100131','png-transparent-businessperson-computer-icons-avatar-passport-miscellaneous-purple-heroes.png',0,'<Дата не определена>',0,1,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (57,'a.novash','НОВАШ АЛЕКСАНДРА ВЛАДИМИРОВНА','5k7VAK9hB','a.novash@tez-tour.by','Офис в Минске','2024-11-25 08:25:59.484774','Отдел онлайн продаж','Руководитель отдела','2613','User 16.jpg',0,'<Дата не определена>',0,0,0,4,0,0,0,0,NULL);
INSERT INTO "users" ("id","username","full_name","password","email","office","last_seen","department","position","phone","image_file","vpn","vpn_end_date","vacuum_im_notifications","online","is_redmine_user","id_redmine_user","is_admin","can_access_quality_control","browser_notifications_enabled","can_access_contact_center_moscow","last_notification_check") VALUES (58,'e.anisimova','АНИСИМОВА ЕКАТЕРИНА АЛЕКСЕЕВНА','iCnHedyxx','ekaterina@tez-tour.com','Офис в Москве','2025-02-05 12:54:19.426357','Отдел интернет-продаж','Менеджер по работе с частными лицами','1931','User 09.jpg',1,'2025-07-31 00:00:00',0,1,0,4,0,0,0,0,NULL);
CREATE INDEX IF NOT EXISTS "idx_push_subscriptions_active" ON "push_subscriptions" (
	"is_active"
);
CREATE INDEX IF NOT EXISTS "idx_push_subscriptions_user_active" ON "push_subscriptions" (
	"user_id",
	"is_active"
);
CREATE INDEX IF NOT EXISTS "idx_push_subscriptions_user_id" ON "push_subscriptions" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "idx_user_department" ON "users" (
	"department"
);
CREATE INDEX IF NOT EXISTS "idx_user_dept_pos" ON "users" (
	"department",
	"position"
);
CREATE INDEX IF NOT EXISTS "idx_user_email" ON "users" (
	"email"
);
CREATE INDEX IF NOT EXISTS "idx_user_username" ON "users" (
	"username"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_AGENCY_ID" ON "T_CALL_INFO" (
	"AGENCY_ID"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_AGENCY_MANAGER" ON "T_CALL_INFO" (
	"AGENCY_MANAGER"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_AGENCY_NAME" ON "T_CALL_INFO" (
	"AGENCY_NAME"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_CURRATOR" ON "T_CALL_INFO" (
	"CURRATOR"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_PHONE_NUMBER" ON "T_CALL_INFO" (
	"PHONE_NUMBER"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_REGION" ON "T_CALL_INFO" (
	"REGION"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_THEME" ON "T_CALL_INFO" (
	"THEME"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_TIME_BEGIN" ON "T_CALL_INFO" (
	"TIME_BEGIN"
);
CREATE INDEX IF NOT EXISTS "ix_T_CALL_INFO_TIME_END" ON "T_CALL_INFO" (
	"TIME_END"
);
CREATE UNIQUE INDEX IF NOT EXISTS "uq_idx_add_notes_full_duplicate" ON "notifications_add_notes" (
	"user_id",
	"issue_id",
	"author",
	"notes",
	"date_created"
);
CREATE UNIQUE INDEX IF NOT EXISTS "uq_idx_notifications_full_duplicate" ON "notifications" (
	"user_id",
	"issue_id",
	"old_status",
	"new_status",
	"old_subj",
	"date_created"
);
COMMIT;
