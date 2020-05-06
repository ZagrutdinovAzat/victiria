from flask import Flask, request
import json
import random
import wikipedia

app = Flask(__name__)
wikipedia.set_lang("ru")

questions = {'Будапешт': ['Этот город в Венгрии был образован в результате слияния 3-х городов в 1873.', wikipedia.summary('Будапешт', sentences=2)],
             'Дербент': ['Самый старый город Росии населенный уже около 5 тыс. лет.', wikipedia.summary('Дербент', sentences=7)],
             'Иерихон': ['Самый древний город в мире, существующим в настоящее время, появившийся еще в медном веке, а это 9000 лет до н.э.', wikipedia.summary('Иерихон', sentences=6)],
             'Пятигорск': ['Город, который в русском жестовом языке можно показать как два пистолета, которые смотрят друг на друга. Это олицетворение дуэли Лермонтова и Мартынова.', wikipedia.summary('Пятигорск', sentences=3)],
             'Брест': ['Во Франции и в Беларуси есть города с одинаковым названием. Любопытно, что их освободили от нацистов в один день — 28 июля 1944 года.', wikipedia.summary('Брест', sentences=2)],
             'Рим': ['Первый город, численность населения которого достигла миллиона?', wikipedia.summary('Рим', sentences=5)],
             'Мурманск': ['Самым крупным городом России и всего мира из числа расположенных за Полярным кругом является...', wikipedia.summary('Мурманск', sentences=1)],
             'Шанхай': ['Самый густо населенный город в мире это?', wikipedia.summary('Шанхай', sentences=2)],
             'Оймякон': ['Самый холодный город в мире - ... он же Полюс холода, а также самое холодное место на Земле, где есть постоянное население.', wikipedia.summary('Оймякон', sentences=2)],
             'Хум': ['Самый маленький город в мире. Его население колеблется от 17 до 25 человек.', wikipedia.summary('Хум_(Бузет)', sentences=4)],
             'Мехико': ['Самый большой по протяженности город. Что бы преодолеть его по прямой придется пройти более 200 километров.', wikipedia.summary('Мехико', sentences=7)],
             'Бангкок': ['Этот город имеет самое длинное название, однако имеется и короткое - ...', wikipedia.summary('Бангкок', sentences=2)],
             'Стокгольм': ['Единственная столица над которой раздрешено летать на воздушных шарах - ...', wikipedia.summary('Стокгольм', sentences=3)]}

cities = ['Оймякон', 'Шанхай', 'Мурманск', 'Рим', 'Брест', 'Москва', 'Рим', 'Будапешт', 'Берлин', 'Казань', 'Милан',
          'Мадрид', 'Амстердам', 'Дербент', 'Иерихон', 'Пятигорск', 'Мюнхен', 'Братислава', 'Зальцбург', 'Хум',
          'Мехико',
          'Дублин', 'Антверпен', 'Афины', 'Краков', 'Познань', 'Цюрих', 'Виши', 'Прага']

correct = ['Правильно! Попробуйте ответить на следующий вопрос:', 'Это правильный ответ! Давайте дальше:',
           'Верно! Следующий вопрос:', 'Вы правы! Попробуйте ответить на следующий вопрос:',
           'В точку! Но дальше сложнее:']
incorrect = ['Это неправильный ответ. Попробуйте ответить на следующий вопрос:',
             'К сожалению, неверно. Попробуйте ответить на следующий вопрос:',
             'Увы, но нет. Уверена, теперь вы справитесь:',
             'Нет, неверно. Может, ответите на следующий вопрос:']

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    global q
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    dialog(response, request.json)
    return json.dumps(response)


def dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Сейчас мы сыграем в викторину, где тебе предстоит отгадать город по факту о нем. Напиши "Начать" для начала игры.'
        res['response']['buttons'] = [{'title': 'Начать', 'hide': True}]
        sessionStorage[user_id] = {
            'game_started': False,
            'count': 0,
            'guessed': list(questions.keys()),
            'prev': None
        }

    elif sessionStorage[user_id]['game_started']:

        if sessionStorage[user_id]['game_started'] and req['request']['command'] == 'Помощь':
            res['response']['text'] = '''Список дополнительных команд:\n\n
                                        Статистика - показывает кол-во пройденных вопросов.\n
                                        Заново - обнуление статистики и начало новой игры.\n
                                        Подробнее - краткая информация о последнем отгаданном городе\n
                                        Что бы продолжить игру ответь на предыдущий вопрос.'''

        elif sessionStorage[user_id]['game_started'] and req['request']['command'] == 'Статистика':
            res['response']['text'] = f'''Вы ответили правильно на {sessionStorage[user_id]['count'] - 1}
                                        из {len(questions.keys())}'''

        elif sessionStorage[user_id]['game_started'] and req['request']['command'] == 'Заново':
            sessionStorage[user_id]['guessed'] = list(questions.keys())
            sessionStorage[user_id]['count'] = 0
            question, answer, answers = generate_question(sessionStorage[user_id]['guessed'])
            res['response']['text'] = f''
            sessionStorage[user_id]['count'] += 1
            sessionStorage[user_id]['question'] = question
            sessionStorage[user_id]['answer'] = answer
            sessionStorage[user_id]['answers'] = answers
            res['response']['buttons'] = [{'title': f'{ans}', 'hide': True} for ans in
                                          sessionStorage[user_id]['answers']]
            res['response']['text'] = f'''Вы начали новую игру. Первый вопрос:\n\n
                                                        {sessionStorage[user_id]["question"]}'''

        elif sessionStorage[user_id]['game_started'] and req['request']['command'] == 'Подробнее':
            if sessionStorage[user_id]['prev'] is None:
                res['response']['text'] = 'Сначала ответьте правильно хотя бы на один вопрос.'
            else:
                res['response']['text'] = f'{questions[sessionStorage[user_id]["prev"]][1]}'

        elif req['request']['command'].capitalize() not in sessionStorage[user_id]['answers']:
            res['response'][
                'text'] = f'''Кажется, такого ответа нет в списке. Выберите один из предложенных ответов.\n\n
                                            {sessionStorage[user_id]["question"]}'''
            res['response']['buttons'] = [{'title': f'{ans}', 'hide': True} for ans in
                                          sessionStorage[user_id]['answers']]
            res['response']['buttons'].append({'title': 'Помощь', 'hide': True})

        elif req['request']['command'].capitalize() != sessionStorage[user_id]['answer']:
            question, answer, answers = generate_question(sessionStorage[user_id]['guessed'])
            sessionStorage[user_id]['question'] = question
            sessionStorage[user_id]['answer'] = answer
            sessionStorage[user_id]['answers'] = answers
            res['response']['text'] = f'''{random.choice(incorrect)}\n\n
                                            {sessionStorage[user_id]["question"]}'''
            res['response']['buttons'] = [{'title': f'{ans}', 'hide': True} for ans in
                                          sessionStorage[user_id]['answers']]
            res['response']['buttons'].append({'title': 'Помощь', 'hide': True})

        elif req['request']['command'].capitalize() == sessionStorage[user_id]['answer'] and len(sessionStorage[user_id]['guessed']) > 1:
            sessionStorage[user_id]['prev'] = sessionStorage[user_id]['answer']
            sessionStorage[user_id]['guessed'].remove(sessionStorage[user_id]['answer'])
            question, answer, answers = generate_question(sessionStorage[user_id]['guessed'])
            sessionStorage[user_id]['count'] += 1
            sessionStorage[user_id]['question'] = question
            sessionStorage[user_id]['answer'] = answer
            sessionStorage[user_id]['answers'] = answers
            res['response']['text'] = f'''{random.choice(correct)}\n\n
                                            {sessionStorage[user_id]["question"]}'''
            res['response']['buttons'] = [{'title': f'{ans}', 'hide': True} for ans in
                                          sessionStorage[user_id]['answers']]
            res['response']['buttons'].append({'title': 'Помощь', 'hide': True})

        elif req['request']['command'].capitalize() == sessionStorage[user_id]['answer'] and len(
                sessionStorage[user_id]['guessed']) == 1:
            sessionStorage[user_id]['guessed'].remove(sessionStorage[user_id]['answer'])
            res['response']['text'] = '''Поздравляем, вы ответили правильно на все вопросы!\n
                                                   Если хотите сыграть еще раз, введите "Заново"'''

        else:
            res['response']['text'] = '''Поздравляем, вы ответили правильно на все вопросы!\n
                                       Если хотите сыграть еще раз, введите "Заново"'''

    elif sessionStorage[user_id]['game_started'] is False and req['request']['command'].lower() == 'начать':
        sessionStorage[user_id]['game_started'] = True
        question, answer, answers = generate_question(sessionStorage[user_id]['guessed'])
        res['response']['text'] = question
        sessionStorage[user_id]['count'] += 1
        sessionStorage[user_id]['question'] = question
        sessionStorage[user_id]['answer'] = answer
        sessionStorage[user_id]['answers'] = answers
        res['response']['buttons'] = [{'title': f'{ans}', 'hide': True} for ans in sessionStorage[user_id]['answers']]
        res['response']['buttons'].append({'title': 'Помощь', 'hide': True})

    else:
        res['response']['text'] = 'Жду, когда вы напишите "Начать" для начала игры'
        res['response']['buttons'] = [{'title': 'Начать', 'hide': True}]


def generate_question(quests):
    answer = random.choice(quests)
    answers = []
    city = random.choice(cities)
    while len(answers) < 3:
        while city in answers or city == answer:
            city = random.choice(cities)
        answers.append(city)
    answers.insert(random.randint(0, 3), answer)
    question = f'{questions[answer][0]}\n\n1) {answers[0]}\n2) {answers[1]}\n3) {answers[2]}\n4) {answers[3]}'
    return question, answer, answers


if __name__ == '__main__':
    app.run()
