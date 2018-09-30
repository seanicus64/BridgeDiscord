#!/usr/bin/env python3
import socket
import select
import json
class Event:
    def __init__(self, event_dict):
        for key, value in event_dict.items():
            setattr(self, key, value)


class User:
    def __init__(self, api, nick, user, host, real, link_id=None, alien=None):
        """Represents an IRC user."""
        #TODO: make a linked_user and unlinked_user class instead
        self.api = api
        self.nick = nick
        self.user = user
        self.host = host
        self.real = real
        self.link_id = link_id
        self.alien = alien
    def join(self, channel):
        self.api.join(self, channel)
    def privmsg(self, recipient, message):
        if type(recipient) is Channel:
            #TODO: recipient is a user?
            self.api.privmsg_channel(self, recipient, message)

    def part(self, channel, message=""):
        self.api.part(self, channel, message)
    def quit(self, message=""):
        self.api.quit(self, message)
    def __repr__(self):
        string = "({}!{}@{}:{}{}{})".format(self.nick, self.user, self.host, self.real, \
            "||alien<{}>".format(self.alien) if self.alien else "", "||link_id<{}>".format(self.link_id) if self.link_id else "")
        return string
class Message:
    def __init__(self, user, message):
        self.user = user
        self.message = message
class Channel:
    """Represents an IRC channel."""
    # TODO: make unlinked_channel and linked_channel objects instead
    # TODO: generators for parsing through joins/parts, messages, etc, or ALL of them
    # for event in chan.get_events(): if event.type == join: (etc)
    def __init__(self, name, users, topic="", link_id=None, alien_name=None):
        self.name = name
        self.users = users
        self.topic = topic
        self.users = users
        self.link_id = link_id
        self.alien_name = alien_name
        self.messages = []
    def __repr__(self):
        return self.name
    def get_messages(self):
        messages = self.messages
        for m in messages:
            yield m
        self.messages = []
        return  

class API:
    def __init__(self):
        self.s = socket.socket()
        self.event_queue = []
        self._users = []
        self._channels = []
        self._slots = {}
    def get_user(self, alien):
        all_users = []
        for user in self._users:
            if user.alien == alien:
                all_users.append(user)
#                return user
        if all_users:
            return all_users
        raise KeyError
    def connect(self, host, port):
        """Connects to BridgeServ and sends initial requests along."""
        self.s.connect((host, port))
        self._query_users()
        self._query_chans()
        self.update()
    def _query_users(self):
        """An initial request to get all the users the IRC server knows about."""
        data = {}
        data["command"] = "get_users"
        self.send_command(data)
    def _query_chans(self):
        """An initial request to get all the channels the IRC server knows about."""
        data = {}
        data["command"] = "get_channels"
        self.send_command(data)
    def join(self, user, channel):
        """Joins the linked user to a channel."""
        data = {}
        data["command"] = "join"
        data["channel_link_id"] = channel.link_id
        data["user_link_id"] = user.link_id
        self.send_command(data)
    def part(self, user, channel, message=""):
        """Parts a linked user from a channel."""
        data = {}
        data["command"] = "part"
        data["channel_link_id"] = channel.link_id
        data["user_link_id"] = user.link_id
        data["message"] = message
        self.send_command(data)
    def quit(self, user, message):
        """Quits a user from the server altogether."""
        data = {}
        data["command"] = "quit"
        data["user_link_id"] =  user.link_id
        data["message"] = message
        self.send_command(data)
        # if for whatever reason there is more than one of that user, delete all of them
        if user in self._users:
            while True:
                try:
                    self._users.remove(user)
                except:
                    break

    def privmsg_channel(self, user, channel, message):
        """Sends a message from a user to a channel."""
        data = {}
        data["command"] = "privmsg_channel"
        data["channel_link_id"] = channel.link_id
        data["user_link_id"] = user.link_id
        data["message"] = message
        self.send_command(data)
    def register_user(self, nick, user, host, real, response_id, alien):
        """Creates a linked user by registering the user to the IRC network."""
        data = {}
        data["command"] = "register"
        data["nick"] = nick
        data["username"] = user
        data["hostname"] = host
        data["realname"] = real
        data["response_id"] = response_id
        self._slots[response_id] = alien
        self.send_command(data)
    def update(self):
        """Gets data from the server.  This method should be called very often."""
        #TODO: can't get a lot of data, for exampple, all_users if there are over 700 of them
        r, w, e = select.select([self.s], [], [], 0)
        buff = ""
        if r:
            
            data = self.s.recv(2048000)
            buff += data.decode("utf-8")
            
            while buff.find("\n") != -1:
                line, buff = buff.split("\n", 1)
                self.parse_line(line)
        return
    def parse_line(self, line):
        """For each type of event, do what needs to be done."""
        try:
            data = json.loads(line)
        except:
            print("Coudln't read line: {}".format(line))
            return
        if "type" not in data.keys():
            return
        if data["type"] == "event":
            event = Event(data)
            self.event_queue.append(event)
            if event.event == "privmsg":
                nick = event.nick
                channel_link_id = event.channel_link_id
                message = event.message
                for c in self._channels:
                    if c.link_id == channel_link_id:
                        channel = c
                        break
                channel.messages.append(Message(nick, message))
                
            if event.event == "uid":
                user = User(self, event.nick, event.username, event.hostname, event.realname)
                self._users.append(user)
        if data["type"] == "response":
            event = Event(data)
            if event.command == "register":
                response_id = event.response_id
                try:
                    alien = self._slots[response_id]
                except:
                    pass
                    
                del self._slots[response_id]
                user = User(self, event.nick, event.username, event.hostname, event.realname, event.link_id, alien)
                self._users.append(user)
            if event.command == "get_users":
                #must be run before get_channels
                self._users = []
                for user in event.all_users:
                    user = User(self, user[0], user[1], user[2], user[3], user[4])
                    self._users.append(user)
            if event.command == "get_channels":
                self._channels = []
                event = Event(data)
                for chan in event.all_channels:
                    name, topic, users, link_id, alien_name = chan
                    user_objs = []
                    for u in self._users:
                        for u2 in users:
                            if u.nick == u2:
                                user_objs.append(u)
                    channel = Channel(name, user_objs, topic, link_id, alien_name)
                    self._channels.append(channel)
                    

    def send_command(self, command):
        """Sends a command to BridgeServ"""
        command = json.dumps(command)
        self.s.send(command.encode() + "\n".encode())
