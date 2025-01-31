#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

from archivist import Archivist
from speaker import Speaker

coloredlogsError = None
try:
    import coloredlogs
except ImportError as e:
    coloredlogsError = e

username = "CollyXBot"
speakerbot = None

logger = logging.getLogger(__name__)

# Enable logging
log_format = f"[{username.upper()}][%(asctime)s]%(name)s::%(levelname)s: %(message)s"

if coloredlogsError:
    logging.basicConfig(format=log_format, level=logging.INFO)
    logger.warning("Unable to load coloredlogs:")
    logger.warning(coloredlogsError)
else:
    coloredlogs.install(level=logging.INFO, fmt=log_format)

start_msg = "Hello there! Ask me for /help to see an overview of the available commands."

wake_msg = "Good morning. I just woke up"

help_msg = """I answer to the following commands:

/start - I say hi.
/about - What I'm about.
/explain - I explain how I work.
/help - I send this message.
/count - I tell you how many messages from this chat I remember.
/period - Change the frequency of my messages. (Maximum of 100000)
/adolf - Forces me to speak.
/answer - Change the probability to answer to a reply. (Decimal between 0 and 1).
/restrict - Toggle restriction of configuration commands to admins only.
/silence - Toggle restriction on mentions by the bot.
"""

about_msg = (
    "I am yet another Markov Bot experiment. I read everything you type to me and "
    "then spit back nonsensical messages that look like yours.\n\nYou can send /explain if you want further explanation."
)

explanation = (
    "I decompose every message I read in groups of 3 consecutive words, so for each "
    "consecutive pair I save the word that can follow them. I then use this to make my own messages. "
    "At first I will only repeat your messages because for each 2 words I will have very few possible following words.\n\n"
    "I also separate my vocabulary by chats, so anything I learn in one chat I will only say in that chat. For privacy, you know. "
    "Also, I save my vocabulary in the form of a JSON dictionary, so no logs are kept.\n\n"
    "My default frequency in private chats is one message of mine from each 2 messages received, "
    "and in group chats it's 10 messages I read for each message I send."
)


async def static_reply(update: Update, context: CallbackContext, text: str, format=None):
    await update.message.reply_text(text, parse_mode=format)


async def error_callback(update: object, context: CallbackContext):
    logger.warning(f"Update {update} caused error {context.error}")


async def stop(update: Update, context: CallbackContext):
    scribe = speakerbot.getScribe(update.message.chat.id)
    logger.warning(f"I got blocked by user {scribe.title()} [{scribe.cid()}]")


async def main():
    global speakerbot
    parser = argparse.ArgumentParser(description="A Telegram Markov bot.")
    parser.add_argument("token", metavar="TOKEN", help="The Bot Token for Telegram API")
    parser.add_argument(
        "admin_id", metavar="ADMIN_ID", type=int, help="The ID of the bot admin"
    )
    parser.add_argument(
        "-w", "--wakeup", action="store_true", help="Send a message to all chats on wakeup."
    )

    args = parser.parse_args()

    # Create the bot application
    application = Application.builder().token(args.token).build()

    archivist = Archivist(
        logger,
        chatdir="adolfbot/Adolf",
        chatext="loog.vls",
        admin=args.admin_id,
        filterCids=None,
        readOnly=False,
    )

    speakerbot = Speaker("collyX", "@" + username, archivist, logger, wakeup=args.wakeup)

    # Register command handlers
    application.add_handler(CommandHandler("start", lambda u, c: static_reply(u, c, start_msg)))
    application.add_handler(CommandHandler("about", lambda u, c: static_reply(u, c, about_msg)))
    application.add_handler(CommandHandler("explain", lambda u, c: static_reply(u, c, explanation)))
    application.add_handler(CommandHandler("help", lambda u, c: static_reply(u, c, help_msg)))
    application.add_handler(CommandHandler("count", speakerbot.getCount))
    application.add_handler(CommandHandler("period", speakerbot.freq))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("adolf", speakerbot.speak))
    application.add_handler(CommandHandler("answer", speakerbot.answer))
    application.add_handler(CommandHandler("restrict", speakerbot.restrict))
    application.add_handler(CommandHandler("silence", speakerbot.silence))
    application.add_handler(CommandHandler("who", speakerbot.who))
    application.add_handler(CommandHandler("where", speakerbot.where))

    # Message handler for reading input
    application.add_handler(
        MessageHandler(
            filters.TEXT | filters.Sticker | filters.ANIMATION, speakerbot.read
        )
    )

    # Log all errors
    application.add_error_handler(error_callback)

    if args.wakeup:
        await speakerbot.wake(application.bot, wake_msg)

    # Start the bot
    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
