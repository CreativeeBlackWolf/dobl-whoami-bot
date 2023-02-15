from typing import Union
from discord.ui import Button, View, button
from discord import ButtonStyle
import discord
import random

import dialog_manager as dialog
import mapparser
import player


class WhoamiCommandView(View):
    def __init__(
            self,
            game_map: mapparser.Map,
            player: player.Player,
            author: discord.User,
            is_whereami_first: bool = False
        ):
        super().__init__(timeout=60.0)
        self.map = game_map
        self.player = player
        self.author = author
        self.message: discord.Message = None

        player_button = Button(
            label="Персонаж",
            custom_id="player",
            style=ButtonStyle.blurple if not is_whereami_first else ButtonStyle.green,
            emoji=random.choice(["🤔", "😐", "🤡"]),
        )
        player_button.callback = self.player_button_callback
        self.add_item(player_button)

        inventory_button = Button(label="Инвентарь", custom_id="inventory",
                                  style=ButtonStyle.success, emoji="📦")
        inventory_button.callback = self.inventory_button_callback
        self.add_item(inventory_button)

        abilities_button = Button(label="Навыки", custom_id="abilities",
                                  style=ButtonStyle.success, emoji="🔶")
        abilities_button.callback = self.abilities_button_callback
        self.add_item(abilities_button)

        whereami_button = Button(
            label="Где я",
            custom_id="whereami",
            style=ButtonStyle.blurple if is_whereami_first else ButtonStyle.green,
            emoji="🗺️"
        )
        whereami_button.callback = self.whereami_button_callback
        self.add_item(whereami_button)

        close_button = Button(label="Закрыть меню", custom_id="close", \
                              style=ButtonStyle.red, emoji="❌")
        close_button.callback = self.close_button_callback
        self.add_item(close_button)

    def change_active_button_color(self, button_id: str):
        for child_button in self.children:
            if child_button.custom_id != "close":
                child_button.style = ButtonStyle.green if child_button.custom_id != button_id \
                                else ButtonStyle.blurple

    async def player_button_callback(self, interaction: discord.Interaction):
        self.change_active_button_color("player")
        await interaction.response.edit_message(view=self, content=dialog.get_player_info_string(self.map, self.player))

    async def inventory_button_callback(self, interaction: discord.Interaction):
        self.change_active_button_color("inventory")
        inv = dialog.get_inventory_string(self.player)
        if len(inv) >= 2000:
            await interaction.response.edit_message(
                view=self,
                content="```Твой инвентарь слишком большой для отображения в одном сообщении... Используй команду .покажи инвентарь```"
            )
        else:
            await interaction.response.edit_message(view=self, content=inv)

    async def abilities_button_callback(self, interaction: discord.Interaction):
        self.change_active_button_color("abilities")
        abilities = dialog.get_abilities_string(self.player)
        if len(abilities) >= 2000:
            await interaction.response.edit_message(
                view=self,
                content="```Твои навыки не помещаются в одно сообщение... Используй команду .покажи навыки```")
        else:
            await interaction.response.edit_message(view=self, content=abilities)

    async def whereami_button_callback(self, interaction: discord.Interaction):
        self.change_active_button_color("whereami")
        if self.player.isDead:
            await interaction.response.edit_message(view=self, content="```Ты мёртв```")
            return
        await interaction.response.edit_message(
            view=self,
            content=dialog.get_player_position_string(self.map, self.player)
        )

    async def close_button_callback(self, interaction: discord.Interaction):
        await self.message.delete()

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user == self.author:
            return True
        return False

    async def on_timeout(self) -> None:
        try:
            await self.message.delete()
        except discord.errors.NotFound:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item)-> None:
        await interaction.response.send_message(f"An error had occured: {str(error)}")


class VoteCommandView(View):
    def __init__(
        self,
        title: str,
        timeout: float = 300,
        can_revote: bool = False,
        admin_id: int = None,
        anonymous: bool = False,
        force_stop: bool = False,
        voting_users: list[discord.Member] = []):
        super().__init__(timeout=timeout)
        self.message: discord.Message = None
        self.__title = title
        self.__admin_id: int = admin_id
        self.__variants: dict[str, dict] = {}
        self.__can_revote = can_revote
        self.__anonymous = anonymous
        self.__force_stop_by_admin = force_stop
        self.__voting_users = voting_users
        self.__voting_users_names = [i.display_name for i in self.__voting_users]

    @property
    def variants(self):
        """
        Represents the variants of voting in a dictionary like:
        ```
        {
            "variant": {
                "votes": int,
                "voted": list[str], # voted users
            }
        }
        ```
        """
        return self.__variants

    @staticmethod
    def __plural_votes(amount: int) -> str:
        if all((amount % 10 == 1, amount % 100 != 11)):
            return "голос"
        elif all((2 <= amount % 10 <= 4,
             any((amount % 100 < 10, amount % 100 >= 20)))):
            return "голоса"
        return "голосов"

    async def __disable_all_buttons(self):
        for but in self.children:
            but.disabled = True
        await self.message.edit(view=self)

    def __construct_voting_variants_str(self):
        votes_count = self.count_votes()
        variants_str = ""
        for variant, data in self.__variants.items():
            variants_str += f'{variant}: {data["votes"]} {self.__plural_votes(data["votes"])} ({data["votes"]/(votes_count or 1)*100}%)'
            if not self.__anonymous:
                variants_str += f'\nПроголосовавшие: {", ".join(data["voted"])}'
            variants_str += "\n"
        return variants_str

    def __find_user(self, username: str) -> Union[dict, None]:
        """
        Finds the user that voted
        :param username: `discord.User.display_username` str
        :return: variant data
        """
        for data in self.__variants.values():
            if username in data["voted"]:
                return data

    def get_most_voted_variant(self) -> list[str, dict]:
        """
        Get the most voted variant
        :return: [variant_name, variant_data]
        """
        max_votes = 0
        most_voted = ["", {}]
        for variant, data in self.__variants.items():
            if data["votes"] >= max_votes:
                max_votes = data["votes"]
                most_voted[0] = variant
                most_voted[1] = data
        return most_voted

    def count_votes(self) -> int:
        """Counts amount of votes"""
        votes = 0
        for data in self.__variants.values():
            votes += data["votes"]
        return votes

    def get_voting_message_str(self) -> str:
        votes_count = self.count_votes()
        voting_params_str = "Переголосовать можно" if self.__can_revote else "Переголосовать нельзя"
        voting_params_str += ", анонимное голосование" if self.__anonymous else ", публичное голосование"
        voting_params_str += f", {self.timeout} секунд"
        voting_params_str += f", админ может досрочно закончить голосование" if self.__force_stop_by_admin else ""

        return f"""{self.__title}
```ansi
{voting_params_str}
{'Пользователи, которые не голосовали: ' + ", ".join(self.__voting_users_names)
 if self.__voting_users_names else ""}

{self.__construct_voting_variants_str()}
Всего проголосовало: {votes_count}
```"""

    async def edit_voting_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=self.get_voting_message_str())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.__admin_id and self.__force_stop_by_admin:
            return True
        if self.__voting_users and interaction.user not in self.__voting_users:
            return False
        search_result = self.__find_user(interaction.user.display_name)
        if not self.__can_revote and search_result is not None:
            await interaction.user.send("Ты уже отдал свой голос в этом голосовании.")
            return False
        if search_result is not None:
            search_result["votes"] -= 1
            search_result["voted"].remove(interaction.user.display_name)
        return True

    def add_item(self, vote_button: Button, force_stop_variant: bool = False):
        async def voting_button_callback(interaction: discord.Interaction):
            if self.__force_stop_by_admin and interaction.user.id == self.__admin_id:
                await interaction.response.defer()
                await self.__disable_all_buttons()
                await self.message.channel.send(
                    f"Админ принудительно завершил голосование `{self.__title}` с результатом `{vote_button.label}`."
                )
                await self.message.unpin()
                self.stop()
                return

            self.__variants[vote_button.label]["votes"] += 1
            self.__variants[vote_button.label]["voted"].append(interaction.user.display_name)

            if interaction.user.display_name in self.__voting_users_names:
                self.__voting_users_names.remove(interaction.user.display_name)

            await self.edit_voting_message(interaction)

            if force_stop_variant:
                await self.__disable_all_buttons()
                await self.message.channel.send(
                    f"Голосование `{self.__title}` завершено досрочно.\n" +
                    f"{interaction.user.display_name} проголосовал `{vote_button.label}`"
                )
                await self.message.unpin()
                self.stop()
                return

            if self.__voting_users and not self.__voting_users_names and \
               not self.__can_revote:
                await self.__disable_all_buttons()
                votes_count = self.count_votes()
                most_voted = self.get_most_voted_variant()
                await self.message.channel.send(
                    f"Голосование `{self.__title}` завершено досрочно (все проголосовали).\n" +
                    f"Победил вариант `{most_voted[0]}` ({most_voted[1]['votes'] / (votes_count or 1) * 100}%)"
                )
                await self.message.unpin()
                self.stop()
                return

        self.__variants[vote_button.label] = {"votes": 0, "voted": []}
        vote_button.callback = voting_button_callback
        return super().add_item(vote_button)

    async def on_timeout(self) -> None:
        await self.__disable_all_buttons()

        votes_count = self.count_votes()
        most_voted = self.get_most_voted_variant()
        await self.message.channel.send(f"""Голосование `{self.__title}` завершено по времени.
Победил вариант `{most_voted[0]}` ({most_voted[1]['votes'] / (votes_count or 1) * 100}%)
""")
        await self.message.unpin()
