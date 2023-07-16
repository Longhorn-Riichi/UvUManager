from typing import Callable
from discord import ui, ButtonStyle, Interaction, Embed
import asyncio
from modules.mahjongsoul.contest_manager import EAST, SOUTH, WEST, NORTH
from modules.pymjsoul.channel import GeneralMajsoulError

# the wind indices for TableView.table
button_labels = ["EAST", "SOUTH", "WEST", "NORTH"]
TABLE_SIZE = 4 # e.g., 3 for sanma
default_embed = Embed(description=(
    "East: None\n"
    "South: None\n"
    "West: None\n"
    "North: None"
))

class Player:
    def __init__(self, mjs_account_id: int, mjs_nickname: str, discord_name: str, affiliation: str):
        self.mjs_account_id = mjs_account_id
        self.mjs_nickname = mjs_nickname
        self.discord_name = discord_name
        self.affiliation = affiliation

    def __str__(self) -> str:
        """
        used for rendering the TableView; does not display the Mahjong Soul account id.
        """
        return f"{self.discord_name} (MJS: {self.mjs_nickname}) [{self.affiliation}]"

    def __repr__(self) -> str:
        return self.__str__()

class TableView(ui.View):
    """
    an interactive Discord message to seat everyone accordingly.
    Allows starting the game when all seats are filled in a valid way.

    NOTE: this only ensures that there are 2 players from each team
    sitting opposite each other; it doesn't ensure that they follow the
    same seating arrangement as their previous game or that a different
    team starts East compared with their previous game.
    """
    def __init__(self, look_up_player: Callable[[str], Player], start_game: Callable[[int, int, int, int], None], original_interaction: Interaction, timeout: float=300):
        super().__init__(timeout=timeout)
        self.look_up_player = look_up_player
        self.start_game = start_game

        # TOTHINK: fetch and save the InteractionMessage instead?
        self.original_interaction = original_interaction

        self.table: list[Player] = [None]*TABLE_SIZE
        self.table_lock = asyncio.Lock()

    async def on_timeout(self):
        await self.original_interaction.delete_original_response()

    """
    =====================================================
    HELPER FUNCTIONS
    =====================================================
    """

    def set_button_disabled(self, button_label: str, disabled: bool):
        """
        find and flip a button given a button label
        """
        for child in self.children:
            if type(child) == ui.Button and child.label == button_label:
                child.disabled = disabled
                break
    
    def get_up_if_possible(self, discord_name: str) -> Player | None:
        """
        returns the Player object if got up successfully,
        otherwise None (the player wasn't sitting before)

        NOTE: should be called while holding a lock
        """
        for i in range(TABLE_SIZE):
            cached_player = self.table[i]
            if cached_player is not None and cached_player.discord_name == discord_name:
                self.table[i] = None
                # enable the button of the now available seat;
                # update will be reflected in the next message edit
                self.set_button_disabled(button_labels[i], False)
                return cached_player
        return None

    def generate_table_description(self):
        """
        NOTE: should be called while holding a lock
        """
        return (
            f"East: {self.table[EAST]}\n"
            f"South: {self.table[SOUTH]}\n"
            f"West: {self.table[WEST]}\n"
            f"North: {self.table[NORTH]}"
        )
    
    async def update_embed(self, description):
        await self.original_interaction.edit_original_response(
            embed=Embed(description=description),
            view=self
        )

    async def sit(self, interaction: Interaction, button: ui.Button, seat: int):
        await interaction.response.defer()
        discord_name = interaction.user.name
        async with self.table_lock:
            if self.table[seat] is not None:
                # somehow tried to sit in an occupied seat; ignore request
                return
            player = self.get_up_if_possible(discord_name)

            if player is None:
                # player wasn't at the table, so try to fetch info of player
                # I want to put this part outside of the lock... but how?
                player = self.look_up_player(discord_name)
                if player is None:
                    # player info doesn't exist
                    await interaction.followup.send(
                        content="You are not a registered player. Register with `/register`",
                        ephemeral=True
                    )
                    return
        
            self.table[seat] = player
            description = self.generate_table_description()

        # disable the button for the current seat
        button.disabled = True
        
        await self.update_embed(description=description)
    
    """
    =====================================================
    BUTTONS
    =====================================================
    """

    @ui.button(label=button_labels[EAST], style=ButtonStyle.blurple, row=0)
    async def east_button(self, interaction: Interaction, button: ui.Button):
        await self.sit(interaction, button, EAST)
    
    @ui.button(label=button_labels[SOUTH], style=ButtonStyle.blurple, row=0)
    async def south_button(self, interaction: Interaction, button: ui.Button):
        await self.sit(interaction, button, SOUTH)

    @ui.button(label=button_labels[WEST], style=ButtonStyle.blurple, row=0)
    async def west_button(self, interaction: Interaction, button: ui.Button):
        await self.sit(interaction, button, WEST)

    @ui.button(label=button_labels[NORTH], style=ButtonStyle.blurple, row=0)
    async def north_button(self, interaction: Interaction, button: ui.Button):
        await self.sit(interaction, button, NORTH)

    @ui.button(label="GET UP", style=ButtonStyle.gray, row=1)
    async def get_up_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        async with self.table_lock:
            player = self.get_up_if_possible(interaction.user.name)
            if player is None:
                return
            description = self.generate_table_description()
        
        await self.update_embed(description=description)
    
    @ui.button(label="CANCEL", style=ButtonStyle.red, row=1)
    async def cancel_button(self, interaction: Interaction, button: ui.Button):
        """
        can only be used by the creator. Delete the message.
        (admin should be able to delete the message without using this button)
        """
        if interaction.user.name != self.original_interaction.user.name:
            await interaction.response.send_message(
                content="Only the table creator may cancel this table",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        await self.original_interaction.delete_original_response()

    @ui.button(label="START", style=ButtonStyle.green, row=1)
    async def start_button(self, interaction: Interaction, button: ui.Button):
        """
        First, check if the seating arrangement is valid.
        If valid, try to start a game via Contest Manager
        If the game is started correctly, call the clean-up function,
        otherwise respond with an error message

        TODO: make sure that only players sitting at table can use this button
        """
        async with self.table_lock:
            for player in self.table:
                if player is None:
                    await interaction.response.send_message(
                        content="Not all seats are filled!",
                        ephemeral=True
                    )
                    return
                
            east_player = self.table[EAST]
            south_player = self.table[SOUTH]
            west_player = self.table[WEST]
            north_player = self.table[NORTH]
            
            if (east_player.affiliation != west_player.affiliation
                or south_player.affiliation != north_player.affiliation
                or east_player.affiliation == south_player.affiliation):
                await interaction.response.send_message(
                    content="2 players from each team must sit opposite each other!",
                    ephemeral=True
                )
                return
        
            try:
                await self.start_game([
                    east_player.mjs_account_id,
                    south_player.mjs_account_id,
                    west_player.mjs_account_id,
                    north_player.mjs_account_id
                ])
            except GeneralMajsoulError as error:
                await interaction.response.send_message(
                    content=f"Failed to start a game. Did everyone hit `Prepare for match` on Mahjong Soul?"
                )
                # raise the error nonetheless
                raise error
        
        await interaction.response.send_message(
            content="GAME STARTING!",
            delete_after=3
        )
        
        # delete after sending the GAME STARTING message. Otherwise would
        # result in an error if the table creator used the `START` button.
        await self.original_interaction.delete_original_response()
            
    # @ui.button(label="START_WITH_AI", style=ButtonStyle.green)
    # async def start_with_ai_button(self, interaction: Interaction, button: ui.Button):
    # TODO: add a button to start the game with AI
    