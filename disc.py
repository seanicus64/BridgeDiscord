#!/usr/bin/env python3
import asyncio
import configparser
import discord
import api
my_api = api.API()
client = discord.Client()
config = configparser.ConfigParser()
config.read("bot.conf")
host = config["DEFAULT"]["host"]
port = int(config["DEFAULT"]["port"])
token = config["DEFAULT"]["discord_token"]
my_api.connect(host, port)

def wait_until_registered():
    length = len(my_api._slots)
    while my_api._slots:
        my_api.update()

async def my_background_task():
    """Constantly checks for incoming information from IRC."""
    while True:
        my_api.update()
        for ch in my_api._channels:
            discord_channel = None
            for d in client.get_all_channels():
                if d.name == ch.alien_name:
                    discord_channel = d
            for m in ch.messages:
                to_be_sent = "**<{}>** : {}".format(m.user, m.message)
                if m.message.startswith("\u0001"):
                    _message = m.message.strip("\u0001")
                    _message = _message.strip("ACTION")
                    to_be_sent = "*{} {}*".format(m.user, _message)

                await client.send_message(discord_channel, to_be_sent)
            ch.messages = []
        await asyncio.sleep(.01)

@client.event
async def on_member_join(member):
    nick = member.nick if member.nick else member.display_name
    my_api.register_user(nick, str(member).replace("#", "_"), "discord", member.display_name, "{}_{}".format(member.server.id, member.id), member)
    wait_until_registered()
    IRC_users = my_api.get_user(member)
    for u in IRC_users:
        for ch in my_api._channels:
            u.join(ch)
        

@client.event
async def on_member_remove(member):
    for u in my_api._users:
        nick, user, host, real, link, alien = u.nick, u.user, u.host, u.real, u.link_id, u.alien
        if alien == member:
            my_api.quit(u, "Left discord")
            break

@client.event
async def on_message(message):
    """What happens when the bot sees a new message on Discord
    (Sends it to BridgeServ)"""
    content = message.clean_content
    nick = message.author.display_name
    ident = message.author.id
    if message.author == client.user:
        return
    # Find which IRC channel the discord channel is linked to.
    channel = None
    for ch in my_api._channels:
        if message.channel.name == ch.alien_name:
            channel = ch
            break
    # Find which user the discord user is linked to.
    user = None
    for u in my_api._users:
        if u.alien == message.author:
            user = u
            break
    if (not user and channel):
        return
    user.privmsg(channel, content)

    
@client.event
async def on_ready():
    channels = list(client.get_all_channels())
    members = list(client.get_all_members())

    for m in members:
        # Not all discord users have a nick set.
        nick = m.nick if m.nick else m.display_name
        my_api.register_user(nick, str(m).replace("#", "_"), "discord", m.display_name, str(m.server.id) + "_" + str(m.id), m)
    wait_until_registered()

    for user in my_api._users:
        if not user.link_id:
            continue
        for ch in my_api._channels:
            user.join(ch)
# Create a while loop that always checks for updates.
client.loop.create_task(my_background_task())

client.run(token)
