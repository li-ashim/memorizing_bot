"""Bot's callback functions."""
from datetime import timedelta

from db import (create_db, save_entry, get_all_entries, delete_entry_from_db, 
                get_entry_to_remind)
from utils import compute_reminder_time, parse_markdown_v2

from telegram.ext import ConversationHandler
from telegram import (ReplyKeyboardMarkup, InlineKeyboardMarkup,
                      InlineKeyboardButton, ParseMode)


# Conversation states global variables
SUBJECT, DESCRIPTION, SAVE = range(3)
DELETE = 0

# Callbacks
def start(update, context):
    """Shows all bot's comands and usage instructions."""
    text = '''
    I will help you to remember things using _spaced repetition technique_\.
  *Use*:
    — */start\_memorizing* for starting the remembering process
    — */stop\_memorizing* for stoping the remembering process
    — */show\_my\_list* for showing all things in your remembering process
    '''
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

def start_memorizing(update, context):
    """Starts remembering process."""
    update.message.reply_text('Please, type in subject')
    return SUBJECT
    
def set_subject(update, context):
    """Sets information to set reminder on."""

    subject = update.message.text
    context.user_data['subject'] = subject

    reply_keyboard = ReplyKeyboardMarkup([['/skip']], one_time_keyboard=True,
                                         resize_keyboard=True)
    update.message.reply_text('Please, type in short description or\nskip it',
                              reply_markup=reply_keyboard)
    return DESCRIPTION

def set_description(update, context):
    """Sets optional explanatory information and offers to save the record."""

    subject = context.user_data['subject']
    description = update.message.text
    description = parse_markdown_v2(description, 'escape')
    
    if len(description) >= 200:
        description = description[190:]+'\.\.\.'
        
    context.user_data['description'] = description
    reply_keyboard = [['/save'], ['/cancel']]
    update.message.reply_text(f'*{subject}* \n{description} \n_Save?_', 
            parse_mode=ParseMode.MARKDOWN_V2, reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
    return SAVE

def skip_description(update, context):
    """Offers to save the record."""
    subject = context.user_data['subject']

    reply_keyboard = [['/save', '/cancel']]
    update.message.reply_text(f'*{subject}* \n_Save?_', 
            parse_mode=ParseMode.MARKDOWN_V2, reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
    return SAVE

def save(update, context):
    """Saves entry in database. Creates initial job."""

    subject = context.user_data['subject']
    try:
        description = context.user_data['description']
    except KeyError:
        description = ''
    user_id = update.message.from_user.id
    
    rem_time = compute_reminder_time(1)
    context.job_queue.run_once(remind, rem_time, 
            context={'user_id': user_id, 'subject': subject,
                     'rem_number': 1}, name=subject)

    context.user_data[f'{subject}_jq'] = context.job_queue

    save_entry(subject, user_id, description)

    # Cleans description so future entries with empty description
    # won't enharit it.
    context.user_data['description'] = ''

    update.message.reply_text('Reminder is set')
    return ConversationHandler.END

def remind(context):
    """Sends reminder. Creates new job"""
    job = context.job
    subject = job.context['subject']
    user_id = job.context['user_id']
    rem_number = job.context['rem_number'] + 1

    entry = get_entry_to_remind(subject, user_id)
    # If description was provided display InlineButton that shows it.
    if entry[1]:
        if rem_number == 7:
            text = (f'*{entry[0]}*\nI hope you remembered it  : \)\n' + 
                     'I won\'t remind you about it anymore\.')
            context.bot.send_message(user_id, text=text,
                                     parse_mode=ParseMode.MARKDOWN_V2)
        else:
            button = InlineKeyboardButton(text='show more',
                                          callback_data=subject)
            context.bot.send_message(user_id, text=f'*{entry[0]}*',
                    parse_mode=ParseMode.MARKDOWN_V2, 
                    reply_markup=InlineKeyboardMarkup.from_button(button))
    else:
        if rem_number == 7:
            text = (f'*{entry[0]}*\nI hope you remembered it  : \)\n' + 
                     'I won\'t remind you about it anymore\.')
            context.bot.send_message(user_id, text=text,
                                     parse_mode=ParseMode.MARKDOWN_V2)
        else:
            context.bot.send_message(user_id, text=f'*{entry[0]}*',
                                 parse_mode=ParseMode.MARKDOWN_V2)
        
    current_jq = job.job_queue
    rem_time = compute_reminder_time(rem_number)
    print(rem_time)
    if rem_time == None:
        job.schedule_removal()
        delete_entry_from_db(subject, user_id)
    else:
        current_job = current_jq.run_once(remind, rem_time, 
                                          context={'user_id': user_id,
                                                   'subject': subject,
                                                   'rem_number': rem_number},
                                          name=subject)

def show_more(update, context):
    """Shows description when button is activated."""
    subject = update.callback_query.data
    user_id = update.callback_query.from_user.id
    try:
        description = get_entry_to_remind(subject, user_id)[1]
    except IndexError:
        update.callback_query.answer('Entry was deleted')
    else:
        description = parse_markdown_v2(description, 'convert_back')
        update.callback_query.answer(description, show_alert=True)

def stop_memorizing(update, context):
    """Shows all user's entries and allows to pick one to delete."""
    all_entries = get_all_entries(update.message.from_user.id)
    if all_entries:
        reply_keyboard = []
        for i in range(0, len(all_entries), 2):
            try:
                reply_keyboard.append([all_entries[i], all_entries[i+1]])
            except IndexError:
                reply_keyboard.append([all_entries[i]])
        
        update.message.reply_text('Choose subject to delete',
                reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                one_time_keyboard=True, resize_keyboard=True))
    else:
        text = '''You have no entries in remembering process\.
Use */start\_memorizing* to add one\.'''
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    return DELETE

def delete_entry(update, context):
    """Deletes entry from db and deletes active job."""
    subject = update.message.text
    user_id = update.message.from_user.id

    jq = context.user_data[f'{subject}_jq']
    job = jq.get_jobs_by_name(subject)[0]
    job.schedule_removal()

    delete_entry_from_db(subject, user_id)
    
    update.message.reply_text('Entry deleted successfully!')
    
    return ConversationHandler.END

def show_my_list(update, context):
    """Shows all user entries."""
    all_entries = get_all_entries(update.message.from_user.id)
    print(all_entries)
    if not all_entries:
        update.message.reply_text('You have no entries added')
    else:
        all_entries_str = '\- '
        all_entries_str += '\n\- '.join(all_entries)
        update.message.reply_text(f'*All your entries:*\n{all_entries_str}',
                                  parse_mode=ParseMode.MARKDOWN_V2)

def cancel(update, context):
    """Cancels current remembering/forgeting process."""
    update.message.reply_text('Process canceled')
    return ConversationHandler.END