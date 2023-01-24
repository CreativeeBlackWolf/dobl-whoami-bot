from __future__ import annotations
import configparser
import discord


class Config:

    def __init__(self, filename: str):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(self.filename)

        self.Bot = self.Bot(
            token=self.config.get('bot', 'token'),
            prefix=self.config.get('bot', 'prefix', fallback="."),
            admins=self.config.get('bot', 'admins', fallback=[]),
            reaction_emoji_id=self.config.getint('bot', 'reaction_emoji_id', fallback=None),
            reaction_message_id=self.config.getint('bot', 'reaction_message_id', fallback=None),
            reaction_role_id=self.config.getint('bot', 'reaction_role_id', fallback=None),
        )

        self.Map = self.Map(
            path=self.config.get('map', 'path')
        )

    def set_bot_reaction_emoji_id(self, emoji: discord.Emoji):
        self.config.set("bot", "reaction_emoji_id", str(emoji.id))
        self.Bot.reaction_emoji_id = emoji.id

    def set_bot_reaction_message_id(self, message: discord.Message):
        self.config.set("bot", "reaction_message_id", str(message.id))
        self.Bot.reaction_message_id = message.id

    def set_bot_reaction_role_id(self, role: discord.Role):
        self.config.set("bot", "reaction_role_id", str(role.id))
        self.Bot.reaction_role_id = role.id

    def write_config(self):
        with open(self.filename, "w") as f:
            self.config.write(f)

    class Bot:
        def __init__(self, 
                     token: str, 
                     prefix: str, 
                     admins: list[str],
                     reaction_emoji_id: int,
                     reaction_message_id: int,
                     reaction_role_id: int):
            self.token: str = token
            self.prefix: str = prefix
            self.admins: list[str] = admins
            self.reaction_emoji_id: int = reaction_emoji_id
            self.reaction_message_id: int = reaction_message_id
            self.reaction_role_id: int = reaction_role_id

            if not self.token:
                raise ValueError("Token must be specified in configuration file.")

    class Map:
        def __init__(self, path: str):
            self.path: str = path

            if not self.path:
                raise ValueError("Path must be specified in configuration file.")
