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
            reaction_data_filename=self.config.get(
                'bot', 'reaction_data', fallback="reaction_triggers.json"
            )
        )

        self.Map = self.Map(
            path=self.config.get('map', 'path')
        )

    
    def write_config(self):
        with open(self.filename, "w") as f:
            self.config.write(f)

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
            self.__reaction_triggers: list[ReactionTrigger] = []

            if not self.token:
                raise ValueError("Token must be specified in configuration file.")

            if not os.path.exists(self.reaction_data_filename):
                with open(self.reaction_data_filename, "w", encoding="utf-8") as f:
                    f.write("[]")

            with open(self.reaction_data_filename, "r", encoding="utf-8") as f:
                raw_triggers: list[dict[str, list[dict]]] = json.load(f)

            # serialize reaction triggers
            for trigger in raw_triggers:
                message_id, raw_emoji_list = list(trigger.items())[0]
                emoji_list: list[str] = []
                role_ids:   list[int] = []
                messages:   list[str] = []
                for emoji in raw_emoji_list:
                    emoji_data = list(emoji.items())
                    emoji_str, role_id = emoji_data[0]
                    _, message = emoji_data[1]
                    emoji_list.append(emoji_str)
                    role_ids.append(role_id)
                    messages.append(message)
                self.__reaction_triggers.append(ReactionTrigger(
                    message_id=int(message_id),
                    emojis=emoji_list,
                    role_ids=role_ids,
                    messages=messages
                ))

        @property
        def reaction_triggers(self) -> list[ReactionTrigger]:
            """
            List of reaction triggers
            """
            return self.__reaction_triggers

        def set_reaction_trigger(
            self,
            reaction_message_id: int,
            reaction_emoji: str,
            reaction_role_id: int,
            message_on_reaction: str):
            """
            Creates new reaction trigger or updates existing
            :param reaction_message_id: discord message id
            :param reaction_emoji: Unicode or custom emoji
            :param reaction_role_id: discord role id
            :param message_on_reaction: message on subscription and unsubscribtion 
            separated with `/`
            """
            search_trigger = self.search_reaction_trigger(reaction_message_id)
            if search_trigger is not None:
                search_trigger.set_reaction_emoji(
                    emoji=reaction_emoji,
                    role_id=reaction_role_id,
                    message=message_on_reaction
                )
            else:
                self.__reaction_triggers.append(ReactionTrigger(
                    message_id=reaction_message_id,
                    emojis=[reaction_emoji],
                    role_ids=[reaction_role_id],
                    messages=[message_on_reaction]
                ))


        def search_reaction_trigger(self, message_id: int) -> Union[ReactionTrigger, None]:
            """
            Search for reaction data for a given message
            :param message_id: discord message id
            :return: `ReactionTrigger` object or `None` if not found
            """
            for trigger in self.__reaction_triggers:
                if trigger.message_id == message_id:
                    return trigger
            return None 

        def write_reaction_triggers_file(self):
            data_to_write = []
            for trigger in self.__reaction_triggers:
                data_to_write.append(trigger.dump_trigger_data())
            with open(self.reaction_data_filename, "w", encoding="utf-8") as f:
                json.dump(data_to_write, f, indent=2, ensure_ascii=False)

    class Map:
        def __init__(self, path: str):
            self.path: str = path

            if not self.path:
                raise ValueError("Path must be specified in configuration file.")


class ReactionTrigger:
    def __init__(
        self,
        message_id: int,
        emojis: list[str],
        role_ids: list[int],
        messages: list[str]):
        self.__message_id = message_id
        self.__emojis = emojis
        self.__role_ids = role_ids
        self.__messages = messages

    def __repr__(self):
        return str(self.__message_id)

    @property
    def message_id(self) -> int:
        """
        Message ID associated with this reaction trigger
        """
        return self.__message_id

    @property
    def emojis(self) -> list[str]:
        """
        List of emojis and custom emoji ids.
        """
        return self.__emojis

    def set_reaction_emoji(self, emoji: str, role_id: int, message: str):
        """
        Set or update the emoji, role and message
        """
        if emoji in self.__emojis:
            index = self.__emojis.index(emoji)
            self.__role_ids[index] = role_id
            self.__messages[index] = message
        else:
            self.__emojis.append(emoji)
            self.__role_ids.append(role_id)
            self.__messages.append(message)

    def get_data_by_emoji(self, emoji: str) -> Union[tuple[int, str], None]:
        """
        Get role assignment data for a given emoji

        :returns: role id and assign/deassign message
        """
        if emoji not in self.__emojis:
            return None
        index = self.__emojis.index(emoji)
        return (self.__role_ids[index], self.__messages[index])

    def dump_trigger_data(self) -> dict:
        """
        Dumps the trigger data to a dictionary like:
        `{"message_id": [{"emoji_id_1": role_id, "message": "sub/unsub"}, ...]}`
        """
        dump = {str(self.__message_id): []}
        for index, value in enumerate(self.__emojis):
            dump[str(self.__message_id)].append(
                {
                    value: self.__role_ids[index],
                    "message": self.__messages[index]
                }
            )
        return dump


if __name__ == '__main__':
    config = Config("botconfig.cfg")
    print(config.Bot.reaction_triggers)
