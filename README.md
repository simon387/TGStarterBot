# TG_Remote_Bot

Telegram bot used to manage programs on remote GNU/Linux servers

## Dev's Setup

+ ```pip install python-telegram-bot --upgrade``` or ```pip install python-telegram-bot -U --pre```
+ ```pip install python-telegram-bot[rate-limiter]```
+ Create the ```config.properties``` file in the project's directory, and put this content:

```
[secrets]
telegram.token=XXX
telegram.group.id=YYY
telegram.developer.chat.id=WWW
[application]
# log.level = info | debug | error
log.level=info
send.start.and.stop.message=false
cmd.timeout=16
# 1.1 | 2
http.version=1.1
```

### Setup BotFather

1. ```/setcommands```
2. ```@TG_Remote_Bot```
3. Copy paste this:

```
version - show bot's version
shutdown - shutdown the bot
send - es: /send ls
```

## TODO

+ ~~cmd with spaces~~
+ ~~stop cmd loop~~
+ ~~telegram.error.BadRequest: Message is too long~~
+ ~~custom timeout in properties~~
+ ~~better string message management~~
+ sudo su
