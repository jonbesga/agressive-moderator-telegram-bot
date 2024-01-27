from openai import AsyncOpenAI

import json
from telegram.ext import (
    MessageHandler,
    ApplicationBuilder,
    ContextTypes,
)
from telegram import Update, Message, Bot
import os
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
I'm going to share with you a message and a reply to that message. Your task is to return a JSON object where there are 2 keys "justification" and "grade".

"grade" is a float number between 0 and 1 judging how much the reply makes no sense as a reply to the original message. 1 means that the reply makes sense within the context of the message. 0 is gibberish. 0.5 could be a reply that sits in between. Some criteria regarding grading:

* Increase grading if the reply is positive and supporting the original message.
* Increase grading even if the reply is negative but is well argumented.

"justification" is a very brief answer explaining why you graded the reply with that number.

"""

MESSAGE_TEMPLATE = """
Message: {message}

Reply: {reply}
"""

async def delete_message(bot: Bot, chat_id, message_id):
    await bot.delete_message(chat_id, message_id)

# async def ban_user_from_chat_and_channel(bot: Bot, chat_id, user_id):
#     await bot.ban_chat_member(chat_id, user_id)
#     await bot.ban_chat_member("@superchannel", user_id)

async def get_criteria(message, reply, model="gpt-3.5-turbo-1106"):
    completion = await client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        ({"role": "user", "content": MESSAGE_TEMPLATE.format(message=message, reply=reply)})
    ], max_tokens=750, response_format={"type": "json_object"},)

    answer = completion.choices[0].message.content
    try:
        return json.loads(answer)
    except json.JSONDecodeError as exc:
        print("Error decoding JSON", answer)
        raise

async def handle_reply_to_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(update)
    reply: Message = update.message
    original_message: Message = reply.reply_to_message
    if not original_message:
        return

    if original_message.sender_chat.id not in [-1002058119580, -1001371888016]:
        return

    answer = await get_criteria(original_message.text, reply.text)
    print(answer)
    if answer["grade"] <= 0.5:
        await delete_message(context.bot, reply.chat_id, reply.message_id)
        # await ban_user_from_chat_and_channel(context.bot, original_message.chat.id, reply.from_user.id)

def main():
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(MessageHandler(None, handle_reply_to_channel_message))
    application.run_polling()

if __name__ == "__main__":
    main()
