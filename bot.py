import requests
import os
import json
import random
from flask import Flask, request
from dotenv import load_dotenv
from waitress import serve
from os.path import join, dirname
from pymongo import MongoClient


def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)


app = Flask(__name__)

mc = MongoClient(get_from_env("MONGO_LINK"))
db = mc['main']
tasks = db['tasks']
users = db['users']


def send_message(chat_id, text, mode=1):
    method = "sendMessage"
    token = get_from_env("TG_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"
    if mode == 1:
        data = {"chat_id": chat_id, "text": text,
                "reply_markup": json.dumps({"keyboard": [[{"text": "Посмотреть баллы"}, {"text": "Решить задачу"}]],
                                            "resize_keyboard": True, "one_time_keyboard": True})}
    elif mode == 2:
        data = {"chat_id": chat_id, "text": text,
                "reply_markup": json.dumps({"keyboard": [[{"text": "Ввести ответ"},
                                                          {"text": "Поменять задачу"}]],
                                            "resize_keyboard": True, "one_time_keyboard": True})}
    elif mode == 3 or mode == 5:
        data = {"chat_id": chat_id, "text": text}

    elif mode == 4:
        data = {"chat_id": chat_id, "text": text,
                "reply_markup": json.dumps({"keyboard": [[{"text": "Да"},
                                                          {"text": "Нет"}]],
                                            "resize_keyboard": True, "one_time_keyboard": True})}

    requests.post(url, data=data)


@app.route('/', methods=['POST'])
def handle_query():
    chat_id = request.json["message"]["chat"]["id"]
    user_text = request.json["message"]["text"]
    if user_text == "/start":
        if users.find_one({"chat_id": chat_id}) is None:
            count_tasks = tasks.count_documents({})
            users.insert_one({"chat_id": chat_id, "num_of_task": -1,
                              "mode": 5, "score": 0, "tries": 5, "problems": 0,
                              "unsolved": [i for i in range(count_tasks)]})
            send_message(chat_id, "Юный математик, тебя приветствует математический бот!\n"
                                  "Я буду выдавать тебе интересные задачки за решение которых ты сможешь получать "
                                  "баллы.\n"
                                  "Задачки могут иметь разную сложность и буду оцениваться по разному (от 1 балла)\n"
                                  "Каждая неверная попытка будет уменьшать число баллов, которые можно получить за "
                                  "задачу, поэтому пиши ответы, в которых уверен!!! \n"
                                  "Если захочешь поменять задачу, то потеряешь 0.5 баллов.\n"
                                  "Успехов!\n\n"
                                  "Введи свой nickname:", mode=5)
        else:
            send_message(chat_id, "Выбери:", mode=1)

        return {'ok': True}

    user_info = users.find_one({"chat_id": chat_id})
    user_mode = user_info["mode"]

    if user_mode == 1:
        if user_text == "Посмотреть баллы":
            score = user_info["score"]
            send_message(chat_id, "Твои баллы: " + str(score), mode=1)

        elif user_text == "Решить задачу":
            unsolved_tasks = user_info["unsolved"]
            if not unsolved_tasks:
                send_message(chat_id, "Ты просмотрел все задачи из базы:", mode=1)
                return {'ok': True}
            num_of_task = random.choice(unsolved_tasks)
            unsolved_tasks.remove(num_of_task)
            users.update_one({"chat_id": chat_id}, {'$set': {"unsolved": unsolved_tasks, "num_of_task": num_of_task,
                                                             "mode": 2}})
            now_task = tasks.find_one({"number": num_of_task})
            max_score = now_task["score"]
            text_of_task = now_task["text"]
            send_message(chat_id, "Максимальный балл за задачу: {}\n\n"
                                  "Задача:\n{}"
                         .format(max_score, text_of_task), mode=2)

        else:
            send_message(chat_id, "Не понимаю тебя, выбери:", mode=1)

    elif user_mode == 2:
        if user_text == "Ввести ответ":
            users.update_one({"chat_id": chat_id}, {'$set': {"mode": 3}})
            send_message(chat_id, "Ответ - число. Eсли получается нецелое, то вводить через точку\n"
                                  "Принимаю :)", mode=3)

        elif user_text == "Поменять задачу":
            users.update_one({"chat_id": chat_id}, {'$set': {"mode": 4}})
            send_message(chat_id, "Потеряешь 0.5 баллов и больше не сможешь решить эту задачу.\n "
                                  "Поменять?", mode=4)

        else:
            send_message(chat_id, "Не понимаю тебя, выбери:", mode=2)

    elif user_mode == 3:
        num_of_task = user_info["num_of_task"]
        num_of_tries = int(user_info["tries"])
        now_task = tasks.find_one({"number": num_of_task})
        answer = now_task["answer"]
        if str(answer) == user_text:
            addition_score = now_task["score"] * num_of_tries / 5
            score = user_info["score"] + addition_score
            users.update_one({"chat_id": chat_id}, {'$set': {"mode": 1, "score": score, "num_of_task": -1, "tries": 5}})
            send_message(chat_id, "Правильно! Молодец! \n"
                                  "Баллов получено: " + str(addition_score) + "\n"
                                  "Выбери:", mode=1)
        else:
            if num_of_tries != 1:
                num_of_tries -= 1
            score = now_task["score"] * num_of_tries / 5
            users.update_one({"chat_id": chat_id}, {'$set': {"mode": 2, "tries": num_of_tries}})
            send_message(chat_id, "Неверно.\n Попробуй еще раз\nПолучишь баллов, если решишь со следующей попытки: "
                         + str(score), mode=2)

    elif user_mode == 4:
        if user_text == "Да":
            user_info = users.find_one({"chat_id": chat_id})
            score = user_info["score"] - 0.5
            problems = user_info["problems"]
            if problems == 0:
                problems = [user_info["num_of_task"]]
            else:
                problems.append(user_info["num_of_task"])
            users.update_one({"chat_id": chat_id}, {'$set': {"mode": 1, "score": score, "tries": 5, "num_of_task": -1,
                                                             "problems": problems}})
            send_message(chat_id, "Печально, Твои баллы: " + str(score) + "\nВыбери:", mode=1)

        elif user_text == "Нет":
            users.update_one({"chat_id": chat_id}, {'$set': {"mode": 2}})
            send_message(chat_id, "Хороший выбор!", mode=2)

        else:
            send_message(chat_id, "Не понимаю тебя, выбери:", mode=2)

    elif user_mode == 5:
        users.update_one({"chat_id": chat_id}, {'$set': {"mode": 1, "username": user_text}})
        send_message(chat_id, "Зафиксировал, выбери:", mode=1)

    return {'ok': True}


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port='5000')
