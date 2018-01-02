#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.
This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineQueryResultArticle, InputTextMessageContent, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
import logging
import dataset
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

db = dataset.connect('sqlite:///todo.db')


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
HELP_TEXT = """`/gitname github username` to set your username
`/todo topicname` to add a new task
`/done topicname` to add a finished task
`@gsctbot <space>` to mark tasks as finished
"""

commands = ['none', 'todo', 'done','start']
reply_keyboard = [['/todo', '/done'],['/leaderboard','/help']]
cur_command = 'none'
from datetime import date, timedelta

users = db['users']
tasks = db['tasks']

def addToDo(user, task):
    tasks.insert(dict(user_id = user.id, text = task, finished = False, daystarted = date.today().isoformat()))


def addDone(user, task):
    tasks.insert(dict(user_id = user.id, text = task, finished = True, daystarted = date.today().isoformat(), dayfinished = date.today().isoformat()))

def getTasks(user):
    its = []
    for task in tasks:
        if(task['user_id'] ==  user.id):
            its += [task['text']]
            print task['text']
    return its

def start(bot, update):
    """Send a message when the command /start is issued."""
    user = update.message.from_user
    update.message.reply_text('_Dear {}_,\n\n *Welcome to GetSetCode* 💻 ,\n\nStart by setting your github username using /gitname <space> _username_.'.format(user.first_name.title()),
     parse_mode = 'MarkDown',reply_markup=ReplyKeyboardRemove())

def gitname(bot, update):
    user = update.message.from_user
    git_name = update.message.text.replace('/gitname','')
    git_name = git_name.replace(' ','')
    if(len(git_name) < 3):
        update.message.reply_text('🙌 Invalid github username, try again.')
    else:
        print('git name: {}'.format(git_name))
        if(users.count(user_id=user.id) > 0):
            users.update(dict(user_id=user.id, username=user.username, gitname=git_name), ['user_id'])
        else:
            users.insert(dict(user_id=user.id, username=user.username, gitname=git_name, score=0))
        update.message.reply_text('🐙 Git username successfully set,\n use /help to continue. Don\'t forget to join our group @gsc_tdc')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(HELP_TEXT, parse_mode = 'MarkDown',
        reply_markup=ReplyKeyboardRemove())


def todo(bot, update):
    """Send a message when the command /help is issued."""
    task = update.message.text[6:]
    print('task : ' + task)
    user = update.message.from_user
    if(task == ''):
        update.message.reply_text('💡 The format is /todo <space> Taskname ')    
    else:
        addToDo(user, task)
        update.message.reply_text('🚣‍ @{} added task : {}.\n ({} pending tasks)'.format(user.username, task, str(tasks.count(user_id = user.id,finished = False))))

def done(bot, update):
    """Send a message when the command /help is issued."""
    task = update.message.text[6:]
    print('done task : ' + task)
    if(task == ''):
        update.message.reply_text('💡 The format is /done <space> _Taskname_')    
    else:
        user = update.message.from_user
        addDone(user, task)
        cur_score = users.find_one(user_id = user.id)['score']
        cur_score += 10
        users.update(dict(user_id = user.id, score = cur_score), ['user_id'])
        update.message.reply_text('🚀 @{} finished task : {}.\n ({} pending tasks)'.format(user.username, task, str(tasks.count(user_id = user.id,finished = False))))


def leaderboard(bot, update):
    """Send a message when the command /help is issued."""
    delta = timedelta(days = 1)
    enddate = date.today()
    uss = []
    my_score = 0
    for user in users:
        total_score = user['score'] #+ streak_score
        statement = 'SELECT  count(dayfinished) as count FROM (SELECT DISTINCT dayfinished FROM tasks WHERE user_id={});'.format(user['user_id'])
        streak = db.query(statement)
        for row in streak:
            streak_score = row['count']
            break
        streak_score = int((streak_score*(streak_score + 1))/2)
        uss.append([user['gitname'], total_score, streak_score])
        if user['user_id'] == update.message.from_user.id:
            my_score = total_score
    uss.sort(key = lambda x : (-x[1],-x[2]))
    lb = " 🏆 Leaderboard \n\n"
    i = 0
    for u in uss:
        i += 1
        lb += ('{}. {} - {} \n').format(i, u[0], u[1])
    lb += "\n\n Your score : {}".format(str(my_score))
    reply = '🏆\n*Leaderboard will be available soon!* \n\n'
    update.message.reply_text(lb)


def tasks_(bot, update):
    reply = 'Your tasks are\n\n'
    user = update.message.from_user
    tasks2 = tasks.find(user_id = user.id)
    for task in tasks2:
        reply += '• {}'.format(task['text'])
        if task['finished']:
            reply += ' - ✅ \n'
        else:
            reply += ' - ⭕ /finished{}\n'.format(str(task['id']))
    update.message.reply_text(reply, parse_mode = 'MarkDown')



def echo(bot, update):
    """Echo the user message."""
    user = update.message.from_user
    #print(update.message.text[:10])
    update.message.reply_text('🙌 Sorry, didnt get you, /help for list of commands')

def inlinequery(bot, update):
    """Handle the inline query."""
    query = update.inline_query.query.lower()
    user = update.inline_query.from_user
    tasks2 = tasks.find(finished = False)
    results = []
    #print(query)
    for task in tasks2:
        if task['user_id'] == user.id and task['finished'] == False:
            results.append(InlineQueryResultArticle(
                id=str(task['id']),
                title=task['text'],
                description='⏳ Ongoing',
                #description= '✅ Finished' if task['finished'] else '⏳ Ongoing',
                input_message_content=InputTextMessageContent('/completed {}'.format(task['id']))))
    update.inline_query.answer(results, cache_time=0, is_personal= True)

def streak(bot, update):
    user = update.message.from_user
    statement = 'SELECT  count(dayfinished) as count FROM (SELECT DISTINCT dayfinished FROM tasks WHERE user_id={});'.format(user.id)
    streak = db.query(statement)
    for row in streak:
        streak_score = row['count']
        break
    update.message.reply_text('🔥 Your streak : {} days'.format(streak_score), parse_mode = 'MarkDown')
def completed(bot, update):
    user = update.message.from_user
    try:
        task_id = update.message.text.replace('/completed', '').strip()
        if(tasks.count(user_id = user.id, id=task_id, finished = False)> 0):
            tasks.update(dict(user_id = user.id, id=task_id, finished = True, dayfinished = date.today().isoformat()),['id','user_id'])
            cur_score = users.find_one(user_id = user.id)['score']
            cur_score += 10
            users.update(dict(user_id = user.id, score = cur_score), ['user_id'])
            reply = '🚀 @{} completed task : {}.\n ({} pending tasks)'.format(user.username, tasks.find_one(id=task_id)['text'], str(tasks.count(user_id = user.id,finished = False)))
            update.message.reply_text(reply, parse_mode = 'MarkDown')
        else:
            update.message.reply_text('💡 Unknown error occurred report @ir5had', parse_mode = 'MarkDown')
    except Exception as e:
        print(e)
        update.message.reply_text('👾 Unknown error occurred report the error @ir5had', parse_mode = 'MarkDown')
def error(bot, update, error):
    """Log Errors caused by Updates."""
    
    logger.warning('Update "%s" caused error "%s"', update, error)

def commandd(bot, update):
    if update.message.text[:9] == '/finished':
        try:
            task_id = update.message.text.split('d')[1]
            tasks.update(dict(id=task_id, finished=True), ['id'])
            reply = 'Task marked as finished.'
            update.message.reply_text(reply, parse_mode = 'MarkDown')
        except:
            update.message.reply_text('error occurred', parse_mode = 'MarkDown')
def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.

    updater = Updater("TOKEN")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gitname", gitname))
    #dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("todo", todo))
    dp.add_handler(CommandHandler("done", done))
    dp.add_handler(CommandHandler("completed", completed))
    dp.add_handler(CommandHandler("tasks", tasks_))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(CommandHandler("streak", streak))
    dp.add_handler(InlineQueryHandler(inlinequery))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    dp.add_handler(MessageHandler(Filters.command, commandd))
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
