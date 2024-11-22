import telebot
import logging
from config import TOKEN
from telebot import types
from extensions import questions, answers

bot = telebot.TeleBot(TOKEN)

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Хранилище данных о пользователях и их состояниях
user_state = {}
pending_confirmation = {}

# Приветствие бота
@bot.message_handler(commands=['start'])
def greetings(message: telebot.types.Message):
    with open('images/moscow_zoo.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    text = (
        f"Здравствуйте!\n"
        "Добро пожаловать в викторину Московского зоопарка «Какое у вас тотемное животное?»! "
        "Мы поможем узнать, какое животное лучше всего отражает вашу личность, "
        "а также расскажем об интересной программе опеки животных в нашем зоопарке. "
        "Готовы пройти тест? Чтобы начать, просто нажмите на кнопку ниже."
    )
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(types.InlineKeyboardButton("🔍 Начать викторину", callback_data='start_quiz'),
                 types.InlineKeyboardButton("📋 Программа опеки", callback_data='/program'),
                 types.InlineKeyboardButton("✉️ Оставить отзыв", callback_data='feedback'),
                 types.InlineKeyboardButton("📖 Список команд", callback_data='help'))
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

# Обработка начала викторины
@bot.callback_query_handler(func=lambda call: call.data == '/start_quiz')
def start_quiz(call: telebot.types.CallbackQuery):
    user_id = call.message.chat.id
    user_state[user_id] = {"points": 0, "questions": iter(questions.items())}
    pending_confirmation[user_id] = False
    logger.info(f"User {user_id} started the quiz.")
    send_next_question(call.message)

# Обработка "Программа опеки"
@bot.callback_query_handler(func=lambda call: call.data == '/program')
def program(call: telebot.types.CallbackQuery):
    bot.send_message(call.message.chat.id, "📋 Программа опеки Московского зоопарка:\n"
                                           "Вы можете узнать больше и стать опекуном, перейдя по ссылке:\n"
                                           "https://moscowzoo.ru/about/guardianship")

# Обработка "Оставить отзыв"
@bot.callback_query_handler(func=lambda call: call.data == 'feedback')
def feedback(call: telebot.types.CallbackQuery):
    bot.send_message(call.message.chat.id, "✉️ Мы будем рады вашим отзывам!\n"
                                           "Перейдите по ссылке, чтобы оставить отзыв: mailto:ayana.20000329@gmail.com?subject=Отзыв")

# Обработка "Список команд"
@bot.callback_query_handler(func=lambda call: call.data == 'help')
def help(call: telebot.types.CallbackQuery):
    bot.send_message(call.message.chat.id,"**Полный список команд:**\n"
                     "/start - Запуск бота\n"
                     "/help - Список команд\n"
                     "/start_quiz - Начать викторину\n"
                     "/program - Информация о программе опеки\n"
                     "/feedback - Оставить отзыв о зоопарке")

# Отправка следующего вопроса
def send_next_question(message):
    user_id = message.chat.id
    if user_id not in user_state:
        return
    try:
        question, answers_data = next(user_state[user_id]["questions"])
        logger.info(f"Sending question to user {user_id}: {question}")
        keyboard = types.InlineKeyboardMarkup()
        # Обработка каждого ответа
        for answer, callback in answers_data.items():
            button = types.InlineKeyboardButton(text=answer, callback_data=callback)
            keyboard.add(button)
        bot.send_message(message.chat.id, question, reply_markup=keyboard)
    except StopIteration:
        logger.info(f"User {user_id} completed all questions.")
        show_results(message)  # Вызываем функцию для отображения результата

# Обработка ответа пользователя
@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call: telebot.types.CallbackQuery):
    user_id = call.message.chat.id
    callback = call.data
    # Добавляем баллы на основе выбранного ответа
    if callback in answers:
        user_state[user_id]["points"] += answers[callback]
        logger.info(f"User {user_id} answered: {callback}. Points: {answers[callback]}")
    else:
        logger.warning(f"Callback {callback} not found in answers for user {user_id}.")
    send_next_question(call.message)

# Показ результатов
def show_results(message):
    user_id = message.chat.id
    if user_id not in user_state:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте снова начать викторину.")
        return
    total_points = user_state[user_id]["points"]
    logger.info(f"User {user_id} finished the quiz. Total points: {total_points}")

    # Определяем животное
    if total_points <= 10:
        result = ("Вам подходит - Европейский волк! (Серый волк!) 🐺\n\n"
                  "Серый волк — символ верности, выносливости и силы. Эти величественные хищники живут в стаях, "
                  "которые представляют собой крепкие семьи. Волки известны своим острым умом и умением работать сообща, "
                  "что позволяет им охотиться даже на более крупных животных.\n\n"
                  "В Московском зоопарке серые волки находятся в просторных вольерах, где они могут бегать, играть и "
                  "исследовать окружающую среду. Сотрудники зоопарка внимательно следят за их состоянием, обеспечивают "
                  "сбалансированный рацион и добавляют элементы обогащения, чтобы поддерживать их активность и природное поведение.\n\n"
                  "Серый волк — ключевой вид в своей экосистеме. Ты можешь стать другом одного из этих удивительных животных, "
                  "поддерживая программу опеки Московского зоопарка. Узнай больше и помоги нашим волкам! https://moscowzoo.ru/animals/kinds/evropeyskiy_volk")
        image = 'images/european_wolf.jpg'
    elif 11 <= total_points <= 17:
        result = ("Вам подходит - Степной орел! 🦅n\n"
                  "Степной орел — символ величия, независимости и стремления к высотам. Эти величественные птицы славятся "
                  "своим зорким зрением и способностью парить высоко над землей. Они всегда знают, куда направить свои силы, и не "
                  "боятся новых вызовов.\n\n"
                  "В Московском зоопарке степные орлы обитают в просторных вольерах, где они могут проявлять своё природное поведение. "
                  "Мы обеспечиваем их необходимым питанием и создаем условия для их активности и здоровья. Сотрудники зоопарка тщательно "
                  "следят за их состоянием и организуют образовательные программы, рассказывая посетителям об этих потрясающих птицах.\n\n"
                  "Степной орел является охраняемым видом, и Московский зоопарк активно участвует в его сохранении. Стань опекуном степного орла "
                  "и помоги сохранить этого величественного хищника! https://moscowzoo.ru/animals/kinds/stepnoy_orel")
        image = 'images/steppe_eagle.jpg'
    elif 18 <= total_points <= 23:
        result = ("Вам подходит - Азиатский слон! 🐘\n\n"
                  "Азиатский слон — символ мудрости, терпения и заботы. Эти умные и социальные животные живут в стадах, где старшие помогают "
                  "младшим, а матери всегда заботятся о своих детях. Слоны известны своей выдающейся памятью и способностью к обучению.\n\n"
                  "В Московском зоопарке азиатские слоны находятся под постоянной заботой сотрудников. Мы создали для них большие вольеры, "
                  "где они могут свободно перемещаться, купаться и играть. Их рацион включает фрукты, овощи и даже специальный корм, "
                  "обеспечивающий необходимое количество витаминов и минералов. Каждый день для слонов организуются игры и упражнения, чтобы "
                  "они оставались активными и довольными.\n\n"
                  "Азиатский слон находится под угрозой исчезновения, и Московский зоопарк ведет активную работу по их сохранению. Ты можешь "
                  "помочь этим удивительным гигантам, став их опекуном. Подробности ты найдешь на нашем сайте! https://moscowzoo.ru/animals/kinds/aziatskiy_slon")
        image = 'images/asian_elephant.jpg'
    else:
        result = ("Вам подходит - Амурский тигр! 🐅\n\n"
        "Тигр — символ силы, смелости и уверенности. Амурский тигр, крупнейший представитель семейства кошачьих, "
        "обитает в суровых условиях Дальнего Востока. Его густой мех защищает от лютого мороза, а невероятная выносливость "
        "позволяет преодолевать огромные расстояния в поисках пищи.\n\n"
        "В Московском зоопарке амурские тигры находятся под пристальным вниманием. Мы создали для них просторные вольеры, "
        "приближенные к естественным условиям, и обеспечиваем их разнообразным рационом, включающим всё необходимое для здоровья "
        "и активности. Сотрудники зоопарка ежедневно следят за состоянием тигров, обогащают их среду новыми игрушками и элементами, "
        "помогающими им оставаться активными и довольными.\n\n"
        "Амурский тигр находится под угрозой исчезновения, и Московский зоопарк активно участвует в международных программах "
        "по его сохранению. Ты можешь внести свой вклад, став опекуном этого великолепного хищника. "
        "Переходи на сайт зоопарка, чтобы узнать подробности и поддержать нашего тигра! https://moscowzoo.ru/animals/kinds/amurskiy_tigr")
        image = 'images/amur_tiger.jpg'

    with open(image, 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    bot.send_message(message.chat.id, result)

    # Очистка данных пользователя
    del user_state[user_id]
    logger.info(f"User {user_id}'s state cleared after results.")

    # Кнопка для перезапуска викторины
    restart_button = types.InlineKeyboardButton("Попробовать ещё раз?", callback_data='start_quiz')
    keyboard = types.InlineKeyboardMarkup().add(restart_button)
    bot.send_message(message.chat.id, "Хотите пройти викторину ещё раз?", reply_markup=keyboard)

 # Подтверждение перезапуска викторины
    @bot.callback_query_handler(func=lambda call: call.data == 'restart_quiz')
    def restart_confirmation(call: telebot.types.CallbackQuery):
        user_id = call.message.chat.id
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ Да", callback_data="restart_yes"),
            types.InlineKeyboardButton("❌ Нет", callback_data="restart_no")
        )
        bot.send_message(call.message.chat.id, "Вы уверены, что хотите перезапустить викторину?", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == 'restart_yes')
    def restart_quiz(call: telebot.types.CallbackQuery):
        user_id = call.message.chat.id
        logger.info(f"User {user_id} confirmed quiz restart.")
        # Очищаем состояние пользователя и начинаем викторину заново
        del user_state[user_id]
        del pending_confirmation[user_id]
        start_quiz(call)

    @bot.callback_query_handler(func=lambda call: call.data == 'restart_no')
    def cancel_restart(call: telebot.types.CallbackQuery):
        bot.send_message(call.message.chat.id, "Вы отменили перезапуск викторины.")

# Обработка кнопки для перезапуска викторины
@bot.callback_query_handler(func=lambda call: call.data == 'start_quiz')
def restart_quiz(call: telebot.types.CallbackQuery):
    start_quiz(call)  # Просто перезапускаем викторину

# Обработка ошибок
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.reply_to(message, "Извините, я не понял ваш запрос. Пожалуйста, используйте команды!")

bot.polling()
