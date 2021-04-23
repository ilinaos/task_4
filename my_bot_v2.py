import telebot
import requests
from config import tg_key

bot = telebot.TeleBot(tg_key, parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
	id = message.from_user.id
	data = {
		"id": id
	}
	url = "http://127.0.0.1:5000/users"
	requests.post(url, json=data)
	bot.send_message(message.from_user.id, 'Я могу предложить новости. Доступные команды:\n'
										   'просмотр категорий - /view_cat\n'
										   'добавить категорию - /add_cat название\n'
										   'удалить категорию - /delete_cat название\n'
										   'просмотр ключевых слов - /view_key\n'
										   'добавить ключевое слово - /add_key название\n'
										   'удалить ключевое слово - /delete_key название\n'
										   'просмотреть последние новости - /news')

@bot.message_handler(commands=['view_cat'])
def handle_view_category(message):
	id = message.from_user.id
	data = {
		"id": id,
		"command":'view'
	}
	url = "http://127.0.0.1:5000/subscriptions/categories"
	result=requests.post(url, json=data)
	bot.send_message(message.from_user.id, 'Вы подписаны на каатегории: '+result.json()['answer'][:-2])

@bot.message_handler(commands=['add_cat'])
def handle_add_category(message):
	id = message.from_user.id
	if len(message.text.split()) <= 1:
		bot.send_message(message.from_user.id, f'''Беда! Вы не указали категорию. Введите команду в формате /add_cat название_категории.\n
		Доступные категории: business, entertainment, general, health, science, sports, technology''')
	else:
		data = {
			"id": id,
			"command":'add',
			"category":message.text.lower().split()[1]
		}
		url = "http://127.0.0.1:5000/subscriptions/categories"
		result=requests.post(url, json=data)
		bot.send_message(message.from_user.id, result.json()['answer'][:-2])

@bot.message_handler(commands=['delete_cat'])
def handle_delete_category(message):
	id = message.from_user.id
	if len(message.text.split()) <= 1:
		bot.send_message(message.from_user.id, 'Беда! Вы не указали категорию. Введите команду в формате /delete_cat название_категории')
	else:
		data = {
			"id": id,
			"command":'delete',
			"category": message.text.lower().split()[1]
		}
		url = "http://127.0.0.1:5000/subscriptions/categories"
		result=requests.post(url, json=data)
		bot.send_message(message.from_user.id, result.json()['answer'][:-2])

@bot.message_handler(commands=['view_key'])
def handle_view_keywords(message):
	id = message.from_user.id
	data = {
		"id": id,
		"command": 'view'
	}
	url = "http://127.0.0.1:5000/subscriptions/keywords"
	result = requests.post(url, json=data)
	bot.send_message(message.from_user.id, 'Вы подписаны на ключевые слова: ' + result.json()['answer'][:-2])

@bot.message_handler(commands=['add_key'])
def handle_add_keyword(message):
	id = message.from_user.id
	if len(message.text.split()) <=1:
		bot.send_message(message.from_user.id, 'Беда! Вы не указали ключевое слово. Введите команду в формате /add_key ключевое_слово')
	else:
		data = {
			"id": id,
			"command": 'add',
			"key":message.text.lower().split()[1]
		}
		url = "http://127.0.0.1:5000/subscriptions/keywords"
		result = requests.post(url, json=data)
		bot.send_message(message.from_user.id, result.json()['answer'][:-2])

@bot.message_handler(commands=['delete_key'])
def handle_delete_keyword(message):
	id = message.from_user.id
	if len(message.text.split()) <= 1:
		bot.send_message(message.from_user.id, 'Беда! Вы не указали ключевое слово. Введите команду в формате /delete_key ключевое_слово')
	else:
		data = {
			"id": id,
			"command": 'delete',
			"key": message.text.lower().split()[1]
		}
		url = "http://127.0.0.1:5000/subscriptions/keywords"
		result = requests.post(url, json=data)
		bot.send_message(message.from_user.id, result.json()['answer'][:-2])

@bot.message_handler(commands=['news'])
def handle_view_news(message):
	id = message.from_user.id
	data = {
		"id": id
	}
	url = "http://127.0.0.1:5000/news"
	result=requests.post(url, json=data)
	text=''
	for i in result.json():
		text+=i+'\n'+result.json()[i]+'\n\n'
	bot.send_message(message.from_user.id, text)

@bot.message_handler(func=lambda message: True)
def handle_another(message):
	bot.send_message(message.from_user.id, 'Хотелось бы поболтать, но я не умею =( Воспользуйтесь командой /help, чтобы узнать, что я могу')

bot.polling()