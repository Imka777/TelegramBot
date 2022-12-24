# TelegramBot

### Особенности сборки:
Создаем webhook:
ngrok http 5000
curl --location --request POST 'https://api.telegram.org/bot5695797600:AAE1xFaFM_B99YKRuYTspYXDs1ILYgNrkDA/setWebhook' --header 'Content-Type: application/json' --data-raw '{"url": "<HTTPS адрес ngrok>"}'


Запускаем бота:
docker-compose build
docker-compose up -d

### Описание бота:

Бот представляет собой сборник математических задач (писал для младшего брата, поэтому задачки простые)

Бот обрабатывает пользователей с помощью mongoDB, находящемся в облаке.

Каждая задача из базы данных имеет свое число баллов, которое можно за нее получить. После каждой неверной попытки пользователя число баллов, которые можно получить за задачу уменьшается вплоть до пятой части от максимума. Пользователь имеет возможность поменять задачу с потерей баллов, при это в базу данных записываются для каждого пользователя задачи, вызвавшие трудности. 

Бот выбирает следующую задачу для каждого пользователя рандомна из списка еще не решенных. Имеет интуитивный интерфейс благодаря клавиатрнуым кнопкам.
