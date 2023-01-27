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
        self.message: discord.Message = None

    def change_active_button_color(self, button: Button):
        for child_button in self.children:
            if child_button.custom_id != "close":    
                child_button.style = ButtonStyle.green if child_button != button \
                                else ButtonStyle.blurple

    @button(label="Персонаж", 
            custom_id="player", 
            style=ButtonStyle.blurple, 
            emoji=random.choice(["🤔", "😐", "🤡"]))
    async def player_button_callback(self, interaction: discord.Interaction, button: Button):
        self.change_active_button_color(button)
        await interaction.response.edit_message(view=self, content=dialog.get_player_info_string(self.map, self.player))

    @button(label="Инвентарь", custom_id="inventory", style=ButtonStyle.success, emoji="📦")
    async def inventory_button_callback(self, interaction: discord.Interaction, button: Button):
        self.change_active_button_color(button)
        await interaction.response.edit_message(view=self, content=dialog.get_inventory_string(self.player))

    @button(label="Навыки", custom_id="abilities", style=ButtonStyle.success, emoji="🔶")
    async def abilities_button_callback(self, interaction: discord.Interaction, button: Button):
        self.change_active_button_color(button)
        await interaction.response.edit_message(view=self, content=dialog.get_abilities_string(self.player))

    @button(label="Где я", custom_id="whereami", style=ButtonStyle.success, emoji="🗺️")
    async def whereami_button_callback(self, interaction: discord.Interaction, button: Button):
        self.change_active_button_color(button)
        if self.player.isDead:
            await interaction.response.edit_message(view=self, content="```Ты мёртв```")
            return
        await interaction.response.edit_message(view=self, content=
            f"""```ansi
{self.map.get_floor_string(player)}

{self.map.construct_ascii_room(self.player)}

{self.map.list_doors_string(self.player)}
```""")

    @button(label="Закрыть меню", custom_id="close", style=ButtonStyle.red, emoji="❌")
    async def close_button_callback(self, interaction: discord.Interaction, button: discord.Button):
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
