import os
import sys
import asyncio
import datetime
from datetime import timedelta
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', owner_id = OWNER_ID, intents=intents)

@bot.event
async def on_ready():
    print(f'\nLogged in as {bot.user} (ID: {bot.user.id})')

    print(f'\n{bot.user} is connected to the following guilds:')
    for guild in bot.guilds:
        print(f'- {guild.name} ({guild.id})')
    print()

@bot.event
async def on_command_error(ctx, exception):
    if isinstance(exception, commands.errors.CommandNotFound):
        await error(ctx, "Command not found.")
    elif isinstance(exception, commands.errors.MissingRequiredArgument):
        await error(ctx, f'`{exception.param}` is a required argument that is missing.')
    elif isinstance(exception, commands.errors.NotOwner):
        await error(ctx, 'You do not have access to this command.')
    elif isinstance(exception, commands.errors.CheckFailure):
        await error(ctx, 'You do not have access to this command.')
    elif isinstance(exception, commands.errors.CommandOnCooldown):
        await error(ctx, f'Command is on cooldown.\nTry again <t:{round((datetime.datetime.now() + timedelta(seconds=exception.retry_after)).timestamp())}:R>.')
    elif isinstance(exception, commands.errors.CommandError):
        #await error(ctx, 'Something went wrong. That\'s all we know.')
        await error(ctx, exception)

@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx: commands.Context):
    async with ctx.channel.typing():
        with open("temp.txt", 'w') as sys.stdout:
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await bot.reload_extension(f'cogs.{filename[:-3]}')
                    except:
                        pass
    
    with open('temp.txt', 'r') as f:
        await ctx.reply(content="".join(f.readlines()))

    sys.stdout = sys.__stdout__
    os.remove('temp.txt')

@bot.command(hidden=True)
@commands.is_owner()
async def kill(ctx: commands.Context):
    await ctx.send(content="👋")
    sys.exit(0)

async def error(ctx: commands.Context, description: str):
    embed = discord.Embed(title="Woops...", description=description)
    embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embed)

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    # create missing directories
    for directory in ["json", "downloads"]:
        if not os.path.exists(directory):
            os.mkdir(directory)

    # load cogs
    await load()

    # start bot
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
