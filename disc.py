#!/usr/bin/env python3
import asyncio
import configparser
import discord
import api
my_api = api.API()
my_api.connect("127.0.0.1", 5959)
client = discord.Client()
config = configparser.ConfigParser()
config.read("bot.conf")
token = config["DEFAULT"]["discord_token"]

def wait_until_registered():
    print("registering users with IRC.")
    length = len(my_api._slots)
    while my_api._slots:
        my_api.update()
    print("done registering")

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
                print("Channel: {} Nick: {} Message: {} discord_chan: {}".format(ch, m.user, m.message, discord_channel))

                await client.send_message(discord_channel, "**<{}>**: {}".format(m.user, m.message))
            ch.messages = []
        await asyncio.sleep(.01)

@client.event
async def on_message(message):
    """What happens when the bot sees a new message on IRC
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
        my_api.register_user(nick, m.id, "discord", m.display_name, m.id, m)
    wait_until_registered()

    for user in my_api._users:
        if not user.link_id:
            continue
        for ch in my_api._channels:
            user.join(ch)
    
# Create a while loop that always checks for updates.
client.loop.create_task(my_background_task())

client.run(token)
