import configparser
import logging

config = configparser.RawConfigParser()
config.read("config.properties")
# application's secrets
SECRETS = "secrets"
TOKEN = config.get(SECRETS, "telegram.token")
TELEGRAM_DEVELOPER_CHAT_ID = config.get(SECRETS, "telegram.developer.chat.id")
# application's settings
APPLICATION = "application"
SEND_START_AND_STOP_MESSAGE = config.get(APPLICATION, "send.start.and.stop.message")
CMD_TIMEOUT = int(config.get(APPLICATION, "cmd.timeout"))
HTTP_VERSION = config.get(APPLICATION, "http.version")
AIO_RATE_LIMITER_MAX_RETRIES = 10
case = config.get(APPLICATION, "log.level")
if case == "info":
	LOG_LEVEL = logging.INFO
elif case == "debug":
	LOG_LEVEL = logging.DEBUG
elif case == "error":
	LOG_LEVEL = logging.ERROR
else:
	LOG_LEVEL = logging.DEBUG
# messages
STARTUP_MESSAGE = "TG_Remote_Bot started! "
STOP_MESSAGE = "TG_Remote_Bot stopped!"
VERSION_MESSAGE = " - more info on https://github.com/simon387/TG_Remote_Bot/blob/master/changelog.txt"
VALID_LINK_MESSAGE = "This is a valid page link! What do you want to do?"
ERROR_NO_GRANT_SHUTDOWN = "You can't shutdown the bot!"
ERROR_NO_GRANT_SEND = "You can't send this command!"
ERROR_PARAMETER_NEEDED_MESSAGE = "This command needs a parameter!"
MESSAGE_CMD_EXECUTED = "Command executed, no output"
ERROR_RUN_CMD = f"Error on running the command, return code={{ex.returncode}}"
ERROR_TIMEOUT_CMD = f"Command not executed, timeout reached! ({CMD_TIMEOUT}sec)"
ERROR_ON_SEND_MSG = f"Failed to send message: {{e}}"
# urls

# var
SPACE = " "
EMPTY = ""
UTF_8 = "utf-8"
