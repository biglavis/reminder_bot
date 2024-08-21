import random
import json
import asyncio

import discord
import discord.colour
from discord.ext import commands

JSON_PATH = 'json//benchmarks.json'

def get_leaderboard() -> dict:
    try:
        with open(JSON_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

class Button(discord.ui.Button):
    def __init__(self, label: str = "\u200b", style: discord.ButtonStyle = discord.ButtonStyle.grey, custom_id: str = None, disabled: bool = False, row: int = None):
        super().__init__(label=label, style=style, custom_id=custom_id, disabled=disabled, row=row)
        self.value = None

    async def callback(self, interaction: discord.Interaction):
        await self.view.interacted(button=self, interaction=interaction)

# Chimp Test
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

class ChimpView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.controller: Chimp = None
        self.message: discord.Message = None

    async def on_timeout(self):
        await self.controller.completed()

    def generate(self, rows: int, columns: int, values: list[int]):
        '''
        Adds buttons and assigns numbers.
        '''
        self.remove_all()

        for i in range(rows):
            for j in range(columns):
                self.add_item(Button(disabled=True, row=i))

        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

    async def reveal(self):
        '''
        Reveals the numbers.
        '''
        button: Button
        for button in self.children:
            if button.value != None:
                button.style = discord.ButtonStyle.blurple
                button.label = str(button.value + 1) 
                button.disabled = False
            else:
                button.style = discord.ButtonStyle.grey
                button.label = "\u200b"
                button.disabled = True

        await self.message.edit(content=f"`Level: {self.controller.level}   Lives: {'♥'*self.controller.lives}`", embed=None, view=self)

    async def hide(self):
        '''
        Hides the numbers.
        '''
        button: Button
        for button in self.children:
            button.label = "\u200b"

        await self.message.edit(embed=None, view=self)

    def remove_all(self):
        '''
        Removes all children from this view.
        '''
        while self.children:
            self.remove_item(self.children[0])

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return
        
        await self.controller.interacted(button=button, interaction=interaction)

class Chimp():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.view: ChimpView

        self.level = 0
        self.stage = 0
        self.lives = 3

    async def start(self):
        '''
        Start the Chimp test.
        '''
        description = "Click the squares in order according to their numbers.\nThe test will get progressively harder."
        embed = discord.Embed(title="Are You Smarter Than a Chimpanzee?", description=description)

        self.view = ChimpView(ctx=self.ctx)
        self.view.controller = self
        self.view.add_item(Button(label="Start", style=discord.ButtonStyle.green))
        
        self.view.message = await self.ctx.send(embed=embed, view=self.view)

    async def scramble(self):
        '''
        Adds buttons and scrambles numbers.
        '''
        values = list(range(self.level)) + [None] * (25 - self.level)
        random.shuffle(values)
        
        self.view.generate(rows=5, columns=5, values=values)

        await self.view.reveal()

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if self.level == 0:
            await interaction.response.defer()
            self.level = 4
            await self.scramble()
            return

        if button.value != self.stage:
            button.style = discord.ButtonStyle.red
            b: Button
            for b in self.view.children:
                b.disabled = True
            await interaction.response.edit_message(view=button.view)
            await asyncio.sleep(1)
            await self.failed()
            return
        
        self.stage += 1
        
        if self.stage == self.level:
            button.style = discord.ButtonStyle.green
            button.disabled = True
            await interaction.response.edit_message(view=button.view)
            await asyncio.sleep(1)
            await self.passed()
            return
        
        if self.level > 4 and self.stage == 1:
            await self.view.hide()

        button.style = discord.ButtonStyle.grey
        button.label = "\u200b"
        button.disabled = True

        await interaction.response.edit_message(view=button.view)

    async def passed(self):
        '''
        User passed the level.
        '''
        self.level += 1
        self.stage = 0

        if self.level > 25:
            await self.completed()
        else:
            await self.scramble()

    async def failed(self):
        '''
        User failed the level.
        '''
        self.lives -= 1
        self.stage = 0

        if self.lives == 0:
            await self.completed()
        else:
            await self.scramble()

    async def completed(self):
        '''
        User completed the test / striked out.
        '''
        if self.level == 4:
            score = 0
        else:
            score = self.level - 1

        leaderboard = get_leaderboard()

        if 'chimp' not in leaderboard:
            leaderboard['chimp'] = {}

        # if user not in leaderboard or user has new highscore
        if str(self.ctx.author.id) not in leaderboard['chimp'] or (score > 0 and score > leaderboard['chimp'][str(self.ctx.author.id)]):
            leaderboard['chimp'][str(self.ctx.author.id)] = score

        # sort leaderboard
        leaderboard['chimp'] = dict(sorted(leaderboard['chimp'].items(), key=lambda item: item[1], reverse=True))
        if len(leaderboard['chimp']) > 5:
            leaderboard['chimp'] = leaderboard['chimp'][:5]

        # save leaderboard
        with open(JSON_PATH, 'w') as f:
            json.dump(leaderboard, f, indent=4, default=str)

        description="**Leaderboard**"
        for id in leaderboard['chimp']:
            description += f"\n**{leaderboard['chimp'][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>"

        embed = discord.Embed(title=f"Your Score: {score}", description=description)

        await self.view.message.edit(content=None, embed=embed, view=None)
        self.view.stop()

# Visual Memory
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

class SquaresView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.controller: Squares = None
        self.message: discord.Message = None

    async def on_timeout(self):
        await self.controller.completed()

    async def generate(self, rows: int, columns: int, values: list[int]):
        '''
        Adds buttons and assigns squares.
        '''
        self.remove_all()

        for i in range(rows):
            for j in range(columns):
                self.add_item(Button(disabled=True, row=i))

        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

        if self == self.controller.views[0]:
            await self.message.edit(content=f"`Level: {self.controller.level}   Lives: {'♥'*self.controller.lives}`", embed=None, view=self)
        elif self.children:
            await self.message.edit(embed=None, view=self)

    async def reveal(self):
        '''
        Reveals the squares.
        '''
        if not self.children:
            return
        
        button: Button
        for button in self.children:
            if button.value:
                button.style = discord.ButtonStyle.blurple
            button.disabled = True

        await self.message.edit(embed=None, view=self)

    async def hide(self):
        '''
        Hides the squares.
        '''
        if not self.children:
            return
        
        button: Button
        for button in self.children:
            button.style = discord.ButtonStyle.grey
            button.disabled = False

        await self.message.edit(embed=None, view=self)

    def remove_all(self):
        '''
        Removes all children from this view.
        '''
        while self.children:
            self.remove_item(self.children[0])

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return
        
        await self.controller.interacted(button=button, interaction=interaction)

class Squares():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.views: list[SquaresView] = None
        self.level = 0
        self.stage = 0
        self.lives = 3
        self.strikes = 0

    async def start(self):
        '''
        Start the visual memory test.
        '''
        self.views = [SquaresView(ctx=self.ctx), SquaresView(ctx=self.ctx)]

        self.views[0].controller = self
        self.views[1].controller = self

        embed = discord.Embed(title="Visual Memory Test", description="Memorize the squares.")
        self.views[0].add_item(Button(label="Start", style=discord.ButtonStyle.green))

        self.views[0].message = await self.ctx.send(embed=embed, view=self.views[0])
        self.views[1].message = await self.ctx.send(content="\u200b")

    async def scramble(self):
        '''
        Add buttons and scramble squares.
        '''
        if self.level < 3:
            grid = [3, 3]
        elif self.level < 6:
            grid = [4, 4]
        elif self.level < 10:
            grid = [5, 5]
        elif self.level < 15:
            grid = [5, 7]
        else:
            grid = [5, 10]

        values = [True]*(self.level + 2) + [False]*(grid[0]*grid[1] - (self.level + 2))
        random.shuffle(values)

        await self.views[0].generate(rows=min(5, grid[1]), columns=grid[0], values=values[:grid[0]*min(5, grid[1])])
        await self.views[1].generate(rows=max(0, grid[1]-5), columns=grid[0], values=values[grid[0]*min(5, grid[1]):])

        await asyncio.sleep(1)

        for view in self.views:
            await view.reveal()

        await asyncio.sleep(2)

        for view in self.views:
            await view.hide()

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if self.level == 0:
            await interaction.response.defer()
            self.level += 1
            await self.scramble()
            return
        
        if not button.value:
            self.strikes += 1

            button.style = discord.ButtonStyle.red
            button.disabled = True

            if self.strikes < 3:
                await interaction.response.edit_message(view=button.view)
                return

            await interaction.response.defer()
            await self.failed()
            return

        self.stage += 1

        if self.stage == self.level + 2:
            await interaction.response.defer()
            await self.passed()
            return

        button.style = discord.ButtonStyle.blurple
        button.disabled = True

        await interaction.response.edit_message(view=button.view)

    async def passed(self):
        '''
        User passed the level.
        '''
        self.level += 1
        self.stage = 0
        self.strikes = 0

        for view in self.views:
            button: Button
            for button in view.children:
                if button.value:
                    button.style = discord.ButtonStyle.green
                button.disabled = True

        for view in self.views:
            if view.children:
                await view.message.edit(embed=None, view=view)
        
        await asyncio.sleep(1)

        if self.level > 23:
            await self.completed()
        else:
            await self.scramble()

    async def failed(self):
        '''
        User failed the level.
        '''
        self.stage = 0
        self.lives -= 1
        self.strikes = 0

        for view in self.views:
            button: Button
            for button in view.children:
                if button.disabled:
                    button.style = discord.ButtonStyle.red
                button.disabled = True

        for view in self.views:
            if view.children:
                await view.message.edit(embed=None, view=view)

        await asyncio.sleep(1)

        if self.lives == 0:
            await self.completed()
        else:
            await self.scramble()

    async def completed(self):
        '''
        User completed the test / striked out.
        '''
        score = self.level - 1
        leaderboard = get_leaderboard()

        if 'squares' not in leaderboard:
            leaderboard['squares'] = {}

        # if user not in leaderboard or user has new highscore
        if str(self.ctx.author.id) not in leaderboard['squares'] or (score > 0 and score > leaderboard['squares'][str(self.ctx.author.id)]):
            leaderboard['squares'][str(self.ctx.author.id)] = score

        # sort leaderboard
        leaderboard['squares'] = dict(sorted(leaderboard['squares'].items(), key=lambda item: item[1], reverse=True))
        if len(leaderboard['squares']) > 5:
            leaderboard['squares'] = leaderboard['squares'][:5]

        # save leaderboard
        with open(JSON_PATH, 'w') as f:
            json.dump(leaderboard, f, indent=4, default=str)

        description="**Leaderboard**"
        for id in leaderboard['squares']:
            description += f"\n**{leaderboard['squares'][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>"

        embed = discord.Embed(title=f"Your Score: {score}", description=description)

        await self.views[1].message.delete()
        await self.views[0].message.edit(content=None, embed=embed, view=None)
        
        for view in self.views:
            view.stop()
