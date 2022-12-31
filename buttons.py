from discord.ui import Button, View, button
from discord import ButtonStyle
from discord.ext import commands
import discord
import random

import context_dialog_manager as dialog
import mapparser
import player


class WhoamiCommandView(View):
    def __init__(self, map: mapparser.Map, player: player.Player, ctx: commands.Context):
        super().__init__(timeout=10.0)
        self.map = map
        self.player = player
        self.ctx = ctx

    @button(label="Персонаж", 
            custom_id="player", 
            style=ButtonStyle.blurple, 
            emoji=random.choice(["🤔", "😐", "🤡"]))
    async def player_button_callback(self, interaction: discord.Interaction, button: Button):
        for childButton in self.children:
            childButton.style = ButtonStyle.green if childButton != button else ButtonStyle.blurple
        await interaction.response.edit_message(view=self, content=dialog.get_player_info(self.map, self.player))

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

    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True
        await self.message.edit(view=self)
        return

    async def on_error(self, interaction: discord.Interaction, error: Exception, item)-> None:
        await interaction.response.send_message(f"An error had occured: {str(error)}")

# class InventoryButton(Button):
#     def __init__(self, player: player.Player):
#         super().__init__(
#             style=ButtonStyle.green,
#             label="Инвентарь",
#             custom_id="inventory",
#             emoji="📦"
#         )
#         self.player = player

#     async def callback(self, interaction: discord.Interaction):
#         await interaction.edit_original_response(content=dialog.send_inventory(self.player))

# class AbilitiesButton(Button):
#     def __init__(self, player: player.Player):
#         super().__init__(
#             style=ButtonStyle.green,
#             label="Abilities",
#             custom_id="abilities",
#             emoji="🔶"
#         )
#         self.player = player

#     async def callback(self, interaction: discord.Interaction):
#         await interaction.edit_original_response(content=dialog.send_abilities(self.player))