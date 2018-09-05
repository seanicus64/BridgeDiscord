BridgeDiscord is a client for the BridgeServ IRC service.  It uses the BridgeAPI to connect a Discord server to an IRC network.  The client:

* Joins Discord users directly to an IRC server
* Relays properly formatted messages to and from IRC
* Informs Discord users of changes made to the IRC side of the network

Installation
=======================
Prerequisites
-----------------------
* Python3
* [Discord.py](https://github.com/Rapptz/discord.py)
* ConfigParser
* asyncio
* [BridgeAPI](https://github.com/seanicus64/BridgeAPI)

You must have created a Discord Bot to get a token.  There's are a million tutorials how to do that online, but you need a valid Discord account to do it.

Configuration
-----------------------
First make a bot.conf file:

    cp example.conf bot.conf

And edit in your favorite text editor.

**host** should be the address of the BridgeServ service.  This should be on the same machine, so "localhost" should suffice.  
**port** is the listening port number of the aforementioned service.  
**discord_token** is the token for the Discord bot.  You can get this through: https://discordapp.com/developers/applications/

Running
-----------------------
Just type in 

    ./disc.py

in your terminal and it should connect to both the Discord and IRC servers and start relaying.
