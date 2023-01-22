from discord.ui import Button, View, button
from discord import ButtonStyle
import discord
import random

import dialog_manager as dialog
import mapparser
import player


class WhoamiCommandView(View):
    def __init__(self, map: mapparser.Map, player: player.Player, author: discord.User):
        super().__init__(timeout=30.0)
        self.map = map
        self.player = player
        self.author = author

    @button(label="Персонаж", 
            custom_id="player", 
            style=ButtonStyle.blurple, 
            emoji=random.choice(["🤔", "😐", "🤡"]))
    async def player_button_callback(self, interaction: discord.Interaction, button: Button):
        for childButton in self.children:
            childButton.style = ButtonStyle.green if childButton != button else ButtonStyle.blurple
        await interaction.response.edit_message(view=self, content=dialog.get_player_info_string(self.map, self.player))

    @button(label="Инвентарь", custom_id="inventory", style=ButtonStyle.success, emoji="📦")
    async def inventory_button_callback(self, interaction: discord.Interaction, button: Button):
        for childButton in self.children:
            childButton.style = ButtonStyle.green if childButton != button else ButtonStyle.blurple
        await interaction.response.edit_message(view=self, content=dialog.get_inventory_string(self.player))

    @button(label="Навыки", custom_id="abilities", style=ButtonStyle.success, emoji="🔶")
    async def abilities_button_callback(self, interaction: discord.Interaction, button: Button):
        for childButton in self.children:
            childButton.style = ButtonStyle.green if childButton != button else ButtonStyle.blurple
        await interaction.response.edit_message(view=self, content=dialog.get_abilities_string(self.player))

    @button(label="Где я", custom_id="whereami", style=ButtonStyle.success, emoji="🗺️")
    async def whereami_button_callback(self, interaction: discord.Interaction, button: Button):
        for childButton in self.children:
            childButton.style = ButtonStyle.green if childButton != button else ButtonStyle.blurple
        if self.player.isDead:
            await interaction.response.edit_message(view=self, content="```Ты мёртв```")
            return
        await interaction.response.edit_message(view=self, content=
            f"""```ansi
{self.map.construct_ascii_room(self.player)}

{self.map.list_doors_string(self.player)}
```""")

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user == self.author:
            return True
        return False

    async def on_timeout(self) -> None:
        for butt in self.children:
            butt.disabled = True
        await self.message.edit(view=self)
        return

    async def on_error(self, interaction: discord.Interaction, error: Exception, item)-> None:
        await interaction.response.send_message(f"An error had occured: {str(error)}")
