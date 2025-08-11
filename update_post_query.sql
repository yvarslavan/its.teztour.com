UPDATE posts
SET content = '<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Обновление почтового домена - TEZ TOUR</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: ''Segoe UI'', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            padding: 20px;
        }

        .notification-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            padding: 30px;
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
            border: 1px solid #e9ecef;
        }

        .header {
            margin-bottom: 25px;
            border-bottom: 1px solid #e9ecef;
            padding-bottom: 20px;
        }

        .title {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
        }

        .subtitle {
            font-size: 14px;
            color: #6c757d;
        }

        .content {
            margin-bottom: 30px;
        }

        .main-message {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .main-message h3 {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
        }

        .main-message h3::before {
            content: ''📧'';
            margin-right: 10px;
            font-size: 20px;
        }

        .main-message p {
            font-size: 15px;
            line-height: 1.5;
            color: #495057;
            margin-bottom: 0;
        }

        .info-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }

        .info-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #dee2e6;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .info-card h4 {
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }

        .info-card h4::before {
            margin-right: 8px;
            font-size: 18px;
        }

        .info-card p {
            font-size: 14px;
            line-height: 1.4;
            color: #495057;
            margin-bottom: 0;
        }

        .domain-highlight {
            background: #007bff;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            font-family: ''Courier New'', monospace;
            font-size: 13px;
        }

        .warning-box {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }

        .warning-box h4 {
            font-size: 16px;
            font-weight: 600;
            color: #856404;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }

        .warning-box h4::before {
            content: ''⚠️'';
            margin-right: 8px;
            font-size: 18px;
        }

        .warning-box p {
            font-size: 14px;
            line-height: 1.4;
            color: #495057;
            margin-bottom: 0;
        }

        .footer {
            text-align: center;
            padding-top: 15px;
            border-top: 1px solid #dee2e6;
        }

        .footer p {
            font-size: 13px;
            color: #6c757d;
            font-style: italic;
        }

        .update-time {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 6px;
            padding: 12px;
            text-align: center;
            margin-bottom: 15px;
        }

        .update-time p {
            font-size: 13px;
            color: #155724;
            font-weight: 500;
            margin-bottom: 0;
        }

        @media (max-width: 768px) {
            .notification-container {
                padding: 20px;
                margin: 10px;
            }

            .title {
                font-size: 20px;
            }

            .info-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="notification-container">
        <div class="header">
            <h1 class="title">Обновление почтового домена</h1>
            <p class="subtitle">Важная информация для всех сотрудников</p>
        </div>

        <div class="content">
            <div class="main-message">
                <h3>Минский офис перешел на новый почтовый домен</h3>
                <p>В связи с изменением почтового адреса в карточке ERP на новый домен <span class="domain-highlight">tez-tour.by</span>, при подключении к вакууму необходимо будет указывать домен <span class="domain-highlight">tez-tour.by</span>.</p>
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <h4>🔧 Настройки подключения</h4>
                    <p>Если подключение не удается, в настройках указать адрес хоста: <span class="domain-highlight">xmpp.tez-tour.com</span></p>
                </div>

                <div class="info-card">
                    <h4>⟳ Обновление ростера</h4>
                    <p>Обновление ростера происходит раз в сутки в <strong>21:00</strong></p>
                </div>
            </div>

            <div class="update-time">
                <p>⏰ Время обновления: ежедневно в 21:00</p>
            </div>

            <div class="warning-box">
                <h4>Важно!</h4>
                <p>Пожалуйста, убедитесь, что все настройки подключения обновлены в соответствии с новыми требованиями.</p>
            </div>
        </div>

        <div class="footer">
            <p>С уважением,<br>Команда технической поддержки TEZ TOUR</p>
        </div>
    </div>
</body>
</html>'
WHERE id = 7;
