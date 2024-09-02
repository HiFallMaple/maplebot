# 🤖 MapleBot (Discord Music Bot)
MapleBot is a simple music bot by discord.py.

## Requirements
+ Discord Bot Token Guide


## 🚀 Getting Started
### docker-compose
```docker-compose
services:
  maplebot:
    image: tony53517230/maplebot:latest
    container_name: maplebot
    restart: always
    environment:
     - DISCORD_TOKEN=XXXXXXXXXXXXX
     - LOCALE=zh_TW
```
