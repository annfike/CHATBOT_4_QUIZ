import os
import re

import redis
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from thefuzz import fuzz
import json
from utils import get_question, make_questions_and_answers


CHOOSING = range(1)
start_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]


def start(update: Update, context: CallbackContext):
    update.message.reply_text(text='Привет! Я бот для викторин.', 
        reply_markup=ReplyKeyboardMarkup(start_keyboard, resize_keyboard=True, one_time_keyboard=True))
    return CHOOSING
        

def handle_new_question_request(update: Update, context: CallbackContext):
    user = update.message.chat_id
    questions_and_answers  = context.bot_data['questions_and_answers']
    question_and_answer = get_question(questions_and_answers)
    question = question_and_answer[0]
    answer = question_and_answer[1]
    r = context.bot_data['redis']
    r.set(user, question)
    r.set(question, answer)
    update.message.reply_text(question)
    return CHOOSING


def handle_solution_attempt(update: Update, context: CallbackContext):
    user = update.message.chat_id
    user_answer = update.message.text
    r = context.bot_data['redis']
    question = r.get(user)
    right_answer = r.get(question)
    right_answer = re.split(r'[.(]',right_answer)[0]
    match = fuzz.WRatio(user_answer, right_answer) 
    if match > 70:
        update.message.reply_text(text='Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"', 
                reply_markup=ReplyKeyboardMarkup(start_keyboard, resize_keyboard=True, one_time_keyboard=True))
    else:
        update.message.reply_text(text='Неправильно… Попробуешь ещё раз?', 
            reply_markup=ReplyKeyboardMarkup(start_keyboard, resize_keyboard=True, one_time_keyboard=True))
        return CHOOSING


def handle_give_up(update: Update, context: CallbackContext):
    user = update.message.chat_id
    r = context.bot_data['redis']
    question = r.get(user)
    right_answer = r.get(question)
    update.message.reply_text(f'Правильный ответ: {right_answer}')
    handle_new_question_request(update, context)

 
def main() -> None:
    load_dotenv()
    tg_token = os.getenv('TG_BOT_TOKEN')
    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')
    redis_password = os.getenv('REDIS_PASSWORD')

    r = redis.StrictRedis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        charset='utf-8',
        decode_responses=True
        )

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['redis'] = r

    questions_and_answers = make_questions_and_answers('quiz-questions')
    dispatcher.bot_data['questions_and_answers'] = questions_and_answers

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                    MessageHandler(Filters.regex('^Новый вопрос$'),
                                   handle_new_question_request),
                    MessageHandler(Filters.regex('^Сдаться$'),
                                   handle_give_up),
                    MessageHandler(Filters.text & ~Filters.command,
                        handle_solution_attempt)
                ],
        },
        fallbacks=[ConversationHandler.END],
        allow_reentry=True,
        )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()