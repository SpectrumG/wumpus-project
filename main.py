import asyncio
import os
import random
import sqlite3

import discord
from discord import Embed, Member
from discord.ext import commands
from discord.ext.menus import MenuPages, ListPageSource
from discord.ext.commands import Cog, command, CommandNotFound


intents = discord.Intents(messages=True, guilds=True)


#import files
os.chdir("import downloaded DB")

#todo
#Eco bot
#Help (wip)

#bot
token = 'token'
bot = commands.Bot(command_prefix='w', intents=discord.Intents.all())

#connecting to database

# list of banned words
filtered_words = ['bad word filter']

@bot.event
async def on_ready():
    print("Hello I am online and ready!")
    print(f'Wumpus bot is currently in {len(bot.guilds)} server(s)')
    #Bot status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"you use whelp"))

#disable key commands here
bot.remove_command('help')
bot.remove_command('level')


#Attempt re-write of all of the bot

class general_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ['c', 'clear'])
    @commands.has_permissions(manage_messages = True)
    async def clean(self, ctx, amount: int):
        amount += 1
        await ctx.channel.purge(limit = amount)
        amount -= 1
        msg = f"You've deleted {amount} messages"
        await ctx.send(msg, delete_after = 5)

    @commands.command(aliases=['h', 'help'])
    async def info(self, ctx):
        author = ctx.message.author

        embed = discord.Embed(
            colour = discord.Colour.blue()
        )
        embed.set_author(name=f'Thank for using wumpus bot! {author}')
        embed.add_field(name='Join our discord!', value = 'You can join here! > (https://discord.gg/mSjtEzUJ75)')
        embed.add_field(name='help', value='Sends the help command to the user.', inline=False)
        embed.add_field(name='clear', value='Aliases: c, clean. Deleted a specified number of messages in the chat history.', inline=False)
        embed.add_field(name='rank', value='Aliases: lvl, level. Displays server leaderboard. (WIP).', inline=False)

        await author.send(embed=embed)

    @commands.command()
    async def shutdown(self, ctx):
        if ctx.message.author.id == 110890004959469568:
            print("shutdown")
            try:
                await self.bot.logout()
            except:
                print("EnvironmentError")
                self.bot.clear()
        else:
            await ctx.send("You do not own this bot!")

class events(commands.Cog):
    def __init__(self , bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.id != 835676293625282601:
            author = message.author
            del_msg = await message.channel.send(":eyes:")
            await asyncio.sleep(1)
            await del_msg.delete()

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot:
            return
        else:
            for word in filtered_words:
                if word in ctx.content:
                    await ctx.delete()
            await bot.process_commands(ctx)

            #random xp gain

            xp_inc = random.randrange(8, 17, 1)

            #connecting to database

            db = sqlite3.connect('xpdata.db')
            cursor = db.cursor()

            user_id = int(ctx.author.id)
            guild_id = ctx.guild.id

            insert_if_new = (f"INSERT OR IGNORE INTO xpdata(user_id,guild_id, xp, level,xp_time) VALUES({user_id}, {guild_id}, {xp_inc}, 0, datetime('now'))")
            cursor.execute(insert_if_new)
            db.commit()

            #Check for cooldown
            select = (f"SELECT julianday('now') - julianday(xp_time) FROM xpdata")
            cursor.execute(select)

            select = (f'SELECT * FROM xpdata WHERE user_id = {user_id} AND guild_id = {guild_id}')
            cursor.execute(select)
            for row in cursor.fetchall():
                lvl_grab = row[3]
                xp_grab = row[2]

            xp_update = (f"UPDATE xpdata SET xp = {xp_grab} + {xp_inc} WHERE user_id = {user_id} AND guild_id = {guild_id} AND strftime('%s',xp_time) < strftime('%s','now','-59 seconds')")
            cursor.execute(xp_update)

            lvl_end = int(((xp_grab+xp_inc)//42) ** 0.55)

            time_update = (f"UPDATE xpdata SET xp_time = datetime('now') WHERE user_id = {user_id} AND guild_id = {guild_id} AND strftime('%s',xp_time) < strftime('%s','now','-59 seconds')")
            cursor.execute(time_update)
            if lvl_grab < lvl_end:
                await ctx.channel.send('{} has leveled up to level {}'.format(ctx.author.mention, lvl_end))
                xp_update = 'UPDATE xpdata SET level = ? WHERE user_id = ? AND guild_id = ?'
                val = (lvl_end, user_id, guild_id)
                cursor.execute(xp_update, val)
                db.commit()
            else:
                pass

            db.commit()

#Utility/Helpfull commands

# class utility():
#     def __init__(self, ctx):
#         self.PREFIX = bot
#         self.ctx = ctx
#
#     async def on_error(self, err, *args, **kwargs):
#         if err == "on_command_error":
#             await args[0].send("Something went wrong")
#
#         channel = self.ctx.channel.id
#         await channel.send("An error occoured.")
#         raise
#
#
#
#     async def on_command_error(self, ctx, exc):
#         if isinstance(exc, CommandNotFound):
#             pass
#
#         else:
#             raise exc.original

#### Leader Boards ####
#the xp ranking menu

class HelpMenu(ListPageSource):
    def __init__(self, ctx, data):
        self.ctx = ctx
        super().__init__(data, per_page = 10)

    async def write_page(self, menu, fields=[]):
         offset = (menu.current_page * self.per_page) + 1
         len_data = len(self.entries)

         embed = Embed(title="Server XP Leaderboard",
                       colour=self.ctx.author.colour)
         embed.set_thumbnail(url = self.ctx.guild.icon_url)
         embed.set_footer(text = f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} members.")

         for name, value in fields:
             embed.add_field(name=name, value=value, inline=False)
         return embed

    async def format_page(self, menu, entries):
        fields = []

        table = ("\n".join(f'{idx + 1}. {self.ctx.guild.get_member(entry[0])} (XP: {entry[1]} | Level: {entry[2]} \n'
                for idx, entry in enumerate(entries)))

        fields.append(("Ranks", table))

        return await self.write_page(menu, fields)


class Exp(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(aliases = ['lvl', 'level'])
    async def rank(self, ctx):

        db = sqlite3.connect('xpdata.db')
        cursor = db.cursor()

        guild_id = ctx.guild.id

        cursor.execute(f'SELECT user_id, xp, level FROM xpdata WHERE guild_id = {guild_id} ORDER BY xp DESC')
        xp_ranking = cursor.fetchall()

        #menu
        ranking_menu = MenuPages(source=HelpMenu(ctx, xp_ranking))
        await ranking_menu.start(ctx)

bot.add_cog(Exp(bot))
bot.add_cog(general_commands(bot))
bot.add_cog(events(bot))

bot.run(token)