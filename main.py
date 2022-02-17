import random
import re
import os


def make_questions_and_answers(dir):
    questions_and_answers = {}
    for file in os.listdir(dir):
        with open(f'{dir}/{file}', 'r', encoding='KOI8-R') as file: 
            file_contents = file.read().split('\n\n')

        questions = []
        answers = []
        for line in file_contents:
            if 'Вопрос' in line:
                question = line.split('Вопрос')
                question = re.sub('\d+:', '', question[1]).lstrip()
                questions.append(question)
            if 'Ответ' in line:
                answer = line.split('Ответ')
                answer = re.sub(':\n', '', answer[1])
                answers.append(answer)
        questions = [question.replace('\n', ' ') for question in questions]
        answers = [answer.replace('\n', ' ') for answer in answers]
        questions_and_answers_from_file = dict(zip(questions, answers))
        questions_and_answers = questions_and_answers | questions_and_answers_from_file
    return questions_and_answers


def get_question(questions_and_answers):
    keys = list(questions_and_answers.keys())
    question = random.choice(keys)
    answer = questions_and_answers[question]
    return question, answer



