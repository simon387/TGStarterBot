import html
import json
import logging as log
import os
import signal
import subprocess
import sys
import time as time_os
import traceback
from logging.handlers import RotatingFileHandler
import platform

import telegram
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, Application, ContextTypes, ApplicationBuilder, AIORateLimiter, CommandHandler

import Constants
from BotApp import BotApp

log.basicConfig(
	handlers=[
		RotatingFileHandler(
			'_TG_Remote_Bot.log',
			maxBytes=10240000,
			backupCount=5
		),
		log.StreamHandler()
	],
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=Constants.LOG_LEVEL
)

if Constants.LOG_LEVEL <= log.INFO:
	log.getLogger('httpx').setLevel(log.WARNING)


async def send_cmd(update: Update, context: CallbackContext):
	log_bot_event(update, 'send_cmd')
	if update.effective_user.id != int(Constants.TELEGRAM_DEVELOPER_CHAT_ID):
		return await context.bot.send_message(chat_id=update.effective_chat.id, text=Constants.ERROR_NO_GRANT_SEND)
	cmd = Constants.SPACE.join(context.args).strip()
	if Constants.EMPTY == cmd:
		return await context.bot.send_message(chat_id=update.effective_chat.id, text=Constants.ERROR_PARAMETER_NEEDED_MESSAGE)
	try:
		is_sudo = False
		if cmd.startswith("sudo "):
			is_sudo = True
			cmd.lstrip("sudo ")
			sudo_command = ['sudo', '-S'] + cmd.split()
			process = subprocess.Popen(sudo_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
			password = f"{Constants.REMOTE_SUDO_PASSWORD}\n"
			process.stdin.write(password)
			process.stdin.flush()
			#
			output, error = process.communicate()
		else:
			output = subprocess.check_output(cmd, shell=True, timeout=Constants.CMD_TIMEOUT)
		if output != b'' and output != '':
			if is_sudo:
				return await send_msg_w(update, context, output)
			return await send_msg_w(update, context, output.decode(Constants.UTF_8, errors='ignore'))
		return await context.bot.send_message(chat_id=update.effective_chat.id, text=Constants.MESSAGE_CMD_EXECUTED)
	except subprocess.CalledProcessError as ex:
		await context.bot.send_message(chat_id=update.effective_chat.id, text=Constants.ERROR_RUN_CMD.format(ex=ex))
		if ex.output != b'':
			await send_msg_w(update, context, ex.output.decode(Constants.UTF_8, errors='ignore'))
	except subprocess.TimeoutExpired:
		await context.bot.send_message(chat_id=update.effective_chat.id, text=Constants.ERROR_TIMEOUT_CMD)


# send message wrapper, use it to managae long messages
async def send_msg_w(update: Update, context: CallbackContext, text: str, markdown=True):
	try:
		if markdown:
			await context.bot.send_message(chat_id=update.effective_chat.id, text=to_code_block(text), parse_mode=ParseMode.MARKDOWN_V2)
		else:
			await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
	except telegram.error.BadRequest as e:
		if "Message is too long" in str(e):
			# Split the message into smaller chunks
			max_length = 4096  # Maximum allowed length for a message
			chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
			# Send each chunk as a separate message
			for chunk in chunks:
				if markdown:
					await context.bot.send_message(chat_id=update.effective_chat.id, text=to_code_block(chunk), parse_mode=ParseMode.MARKDOWN_V2)
				else:
					await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk)
		else:
			if "Can't parse entities:" in str(e):
				await send_msg_w(update, context, text, False)
			else:
				# Handle other BadRequest errors
				log.error(Constants.ERROR_ON_SEND_MSG.format(e=str(e)))


def to_code_block(text: str):
	return f"```\n{text}\n```"


async def send_version(update: Update, context: CallbackContext):
	log_bot_event(update, 'send_version')
	await context.bot.send_message(chat_id=update.effective_chat.id, text=get_version() + Constants.VERSION_MESSAGE)


async def send_shutdown(update: Update, context: CallbackContext):
	log_bot_event(update, 'send_shutdown')
	if update.effective_user.id == int(Constants.TELEGRAM_DEVELOPER_CHAT_ID):
		os.kill(os.getpid(), signal.SIGINT)
	else:
		await context.bot.send_message(chat_id=update.effective_chat.id, text=Constants.ERROR_NO_GRANT_SHUTDOWN)


async def post_init(app: Application):
	version = get_version()
	log.info(f"Starting TGDownloaderBot, {version}")
	if Constants.SEND_START_AND_STOP_MESSAGE == 'true':
		await app.bot.send_message(chat_id=Constants.TELEGRAM_GROUP_ID, text=Constants.STARTUP_MESSAGE + version, parse_mode=ParseMode.HTML)
		await app.bot.send_message(chat_id=Constants.TELEGRAM_DEVELOPER_CHAT_ID, text=Constants.STARTUP_MESSAGE + version, parse_mode=ParseMode.HTML)


async def post_shutdown(app: Application):
	log.info(f"Shutting down, bot id={str(app.bot.id)}")


# v1.0, highest
def log_bot_event(update: Update, method_name: str):
	msg = '>>No message<<'
	if update.message is not None:
		msg = update.message.text
	user = update.effective_user.first_name
	uid = update.effective_user.id
	log.info(f"[method={method_name}] Got this message from {user} [id={str(uid)}]: {msg}")


# Log the error and send a telegram message to notify the developer. Attemp to restart the bot too
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
	# Log the error before we do anything else, so we can see it even if something breaks.
	log.error(msg="Exception while handling an update:", exc_info=context.error)
	# traceback.format_exception returns the usual python message about an exception, but as a
	# list of strings rather than a single string, so we have to join them together.
	tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
	tb_string = "".join(tb_list)
	# Build the message with some markup and additional information about what happened.
	update_str = update.to_dict() if isinstance(update, Update) else str(update)
	await context.bot.send_message(chat_id=Constants.TELEGRAM_DEVELOPER_CHAT_ID, text=f"An exception was raised while handling an update")
	await send_error_message(context, f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>")
	await send_error_message(context, f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>")
	await send_error_message(context, f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>")
	await send_error_message(context, f"<pre>{html.escape(tb_string)}</pre>")
	# Restart the bot
	time_os.sleep(5.0)
	os.execl(sys.executable, sys.executable, *sys.argv)


async def send_error_message(context: ContextTypes.DEFAULT_TYPE, message):
	max_length = 4096  # Maximum allowed length for a message
	chunks = [message[i:i + max_length] for i in range(0, len(message), max_length)]
	# Send each chunk as a separate message
	for chunk in chunks:
		if not chunk.startswith('<pre>'):
			chunk = '<pre>' + chunk
		if not chunk.endswith('</pre>'):
			chunk += '</pre>'
		# Finally, send the message
		await context.bot.send_message(chat_id=Constants.TELEGRAM_DEVELOPER_CHAT_ID, text=chunk, parse_mode=ParseMode.HTML)


def get_version():
	with open("changelog.txt") as f:
		firstline = f.readline().rstrip()
	return firstline


if __name__ == '__main__':
	log.info(f'python version: {platform.python_version()}')
	application = ApplicationBuilder() \
		.token(Constants.TOKEN) \
		.application_class(BotApp) \
		.post_init(post_init) \
		.post_shutdown(post_shutdown) \
		.rate_limiter(AIORateLimiter(max_retries=Constants.AIO_RATE_LIMITER_MAX_RETRIES)) \
		.http_version(Constants.HTTP_VERSION) \
		.get_updates_http_version(Constants.HTTP_VERSION) \
		.build()
	application.add_handler(CommandHandler('version', send_version))
	application.add_handler(CommandHandler('shutdown', send_shutdown))
	application.add_handler(CommandHandler('send', send_cmd))
	application.add_error_handler(error_handler)
	application.run_polling(allowed_updates=Update.ALL_TYPES)
	
