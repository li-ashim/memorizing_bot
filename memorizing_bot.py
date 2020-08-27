"""
Telegram bot which helps to remember different information
using spaced repetition technique.

Repetition intervals: 
1) 1 hour
2) 1 day
3) 3 days
4) 1 week
5) 2 weeks
6) 4 weeks
"""
from db import create_db
from callbacks import *

from decouple import config
from telegram.ext import (Updater, CommandHandler, MessageHandler,
        ConversationHandler, CallbackQueryHandler, Filters)


def main():
    """Main bot function.""" 
    BOT_TOKEN = config('BOT_TOKEN')
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handlers
    start_handler = CommandHandler(['start', 'help'], start)
    set_reminder_handler = ConversationHandler(
        entry_points=[CommandHandler('start_memorizing', start_memorizing)],
        states={
            SUBJECT: [MessageHandler(Filters.text & ~Filters.command,
                                     set_subject)],

            DESCRIPTION: [CommandHandler('skip', skip_description),
                          MessageHandler(Filters.text & ~Filters.command, 
                                         set_description)],
            SAVE: [CommandHandler('save', save)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    show_more_handler = CallbackQueryHandler(show_more)
    stop_memorizing_handler = ConversationHandler(
        entry_points=[CommandHandler('stop_memorizing', stop_memorizing)],
        states={
            DELETE: [MessageHandler(Filters.text & ~Filters.command,
                                    delete_entry)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    show_my_list_handler = CommandHandler('show_my_list', show_my_list)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(show_more_handler)
    dispatcher.add_handler(set_reminder_handler)
    dispatcher.add_handler(stop_memorizing_handler)
    dispatcher.add_handler(show_my_list_handler)

    create_db()

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()