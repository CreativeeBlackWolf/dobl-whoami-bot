from __future__ import annotations
import configparser
import json
import os
from typing import Union

class Config:

    def __init__(self, filename: str):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(self.filename)

        self.Bot = self.Bot(
            token=self.config.get('bot', 'token'),
            prefix=self.config.get('bot', 'prefix', fallback="."),
            admins=self.config.get('bot', 'admins', fallback=[]),
            reaction_data_filename=self.config.get('bot', 'reaction_data', fallback="reaction_data.json")
        )

        self.Map = self.Map(
            path=self.config.get('map', 'path')
        )

    def set_bot_reaction_data(
        self,
        reaction_emoji_id: int,
        reaction_role_id: int,
        reaction_message_id: int,
        message_on_reaction: str):
        # [{"message_id": [{"emoji_id": "role_id", "message": message_on_reaction}]}, {"message_id_2": [...]}]
        search_result = self.search_reaction_data_message(reaction_message_id)
        if search_result is None:
            data = {
                str(reaction_message_id): [
                    {
                        str(reaction_emoji_id): reaction_role_id,
                        "message": message_on_reaction
                    }
                ]
            }
            self.Bot.reaction_data.append(data)
        else:
            search_result[list(search_result.keys())[0]].append(
                {
                    str(reaction_emoji_id): reaction_role_id,
                    "message": message_on_reaction
                }
            )
        self.config.set("bot", "reaction_data", str(self.Bot.reaction_data))

    def search_reaction_data_message(self, message_id: int) -> Union[dict, None]:
        """
        Search for reaction data for a given message
        :param message_id: discord message id
        :return: reaction_data message or `None` if not found
        """
        for val in self.Bot.reaction_data:
            if str(message_id) in val:
                return val
        return None

    @staticmethod
    def search_reaction_data_message_emoji(
        message_dict: dict,
        emoji_id: int) -> Union[dict, None]:
        """
        Search emoji_id in reaction_data message
        :param message_dict: reaction_data message
        :param emoji_id: emoji id
        :return: emoji dict or `None` if not found
        """
        for _, val in message_dict.items():
            for emoji_value in val:
                if str(emoji_id) in emoji_value:
                    return emoji_value
        return None

    def write_config(self):
        with open(self.filename, "w") as f:
            self.config.write(f)

    def write_reaction_data_file(self):
        with open(self.Bot.reaction_data_filename, "w", encoding="utf-8") as f:
            json.dump(self.Bot.reaction_data, f, indent=2, ensure_ascii=False)

    class Bot:
        def __init__(self,
                     token: str,
                     prefix: str,
                     admins: list[str],
                     reaction_data_filename: str):
            self.token: str = token
            self.prefix: str = prefix
            self.admins: list[str] = admins
            self.reaction_data_filename: str = reaction_data_filename
            if not self.token:
                raise ValueError("Token must be specified in configuration file.")

            if not os.path.exists(self.reaction_data_filename):
                with open(self.reaction_data_filename, "w", encoding="utf-8") as f:
                    f.write("[]")

            with open(self.reaction_data_filename, "r", encoding="utf-8") as f:
                self.reaction_data = json.load(f)

    class Map:
        def __init__(self, path: str):
            self.path: str = path

            if not self.path:
                raise ValueError("Path must be specified in configuration file.")
