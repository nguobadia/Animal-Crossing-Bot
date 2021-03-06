import discord
import datetime
import json
import sys
import re
import random

from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import CommandNotFound
from scripts.FriendCodeHelper import *
from scripts.TurnipHelper import *
from scripts.PlayerProfile import *

INFO = str(open('config/config.txt', 'r+').read()).split('\n')
TOKEN = INFO[0]
PREFIX = INFO[1]


client = commands.Bot(command_prefix = PREFIX)
start_time = datetime.datetime.utcnow()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print('------')
    await client.change_presence(activity=discord.Game(name='Animal Crossing New Horizons', type=1))


@client.command(name='ping',
                description='pong')
async def ping(ctx):
    await ctx.send('pong')
    

@client.command(name='uptime',
                description='Returns how long the bot has been running for.')
async def uptime(ctx):
    '''
    Source: https://stackoverflow.com/questions/52155265/my-uptime-function-isnt-able-to-go-beyond-24-hours-on-heroku
    '''
    now = datetime.datetime.utcnow() # Timestamp of when uptime function is run
    delta = now - start_time
    
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    if days:
        time_format = "**{d}** days, **{h}** hours, **{m}** minutes, and **{s}** seconds."
        
    else:
        time_format = "**{h}** hours, **{m}** minutes, and **{s}** seconds."
        
    uptime_stamp = time_format.format(d=days, h=hours, m=minutes, s=seconds)
    await ctx.send('{} has been up for {}'.format(client.user.name, uptime_stamp))
 

@client.command(name='info',
                description='Returns information about the bot',
                aliases=['botinfo', 'bot_info'])
async def bot_info(ctx):
    with open('media/isabelle_urls.json') as f:
        isabelle_urls = json.load(f)["isabelle_urls"]
        
    embed = discord.Embed(
        title='Animal Crossing Bot',
        description='Utility bot for Animal Crossing users'
    )
    
    embed.set_footer(text='You can view my code here: https://github.com/nguobadia/Animal-Crossing-Bot')
    embed.set_image(url=random.choice(isabelle_urls))
    
    await ctx.send(embed=embed)
 
 
 
'''FRIEND CODES'''

@client.command(name='add',
                description='Adds information to the database',
                aliases=['addfc'])
async def add_fc(ctx, *arg):
    ''' Currently adds user to friend code database.
    
    ![add|addfc] [friend code|fc] SW-XXXX-XXXX-XXXX
    
    Note: if you use !addfc then there's no need to include 'friend code' or 'fc'
    
    Examples:
        !add fc SW-XXXX-XXXX-XXXX
        !addfc SW-XXXX-XXXX-XXXX
        !add friend code SW-XXXX-XXXX-XXXX
    '''
    if arg[0] == 'fc' or arg[:2] == ('friend', 'code'):
        user_id = ctx.message.author.id
        if arg[:2] == ('friend', 'code'):
            ret = set_friend_code(user_id, arg[2])
        else:
            ret = set_friend_code(user_id, arg[1])
            
        
        if not ret:
            # instantiate_user_in_database(get_friend_code(user_id), ctx.message.author)
            await ctx.send('Added {} successfully'.format(ctx.message.author))
        elif ret == -1:
            await ctx.send('Invalid friend code. Nintendo friend codes follow the pattern: SW-XXXX-XXXX-XXXX.')


@client.command(name='get',
                description='Gets information from the database',
                aliases=['getfc'])
async def get_fc(ctx, *arg):
    ''' Currently retrieves user's friend code from database.
    
    ![get|getfc] [friend code|fc] @User
    
    Note: if you use !getfc then there's no need to include 'friend code' or 'fc'
    
    Examples:
        !get fc @Chonnasorn
        !getfc @Chonnasorn
        !get friend code @Chonnasorn
    '''
    mentioned_user_id = ctx.message.mentions[0].id
    friend_code = get_friend_code(mentioned_user_id)
    
    if friend_code == -1:
        await ctx.send('User not found.')
    else:
        await ctx.send(friend_code)



''' TURNIPS '''
@client.command(name='turnip',
                description='Turnip commands.')
async def turnip(ctx, *arg):
    ''' Used to calculate turnip price trends. The two websites used are https://turnipprophet.io/ and https://ac-turnip.com/. To use this command:
    !turnip [prophet|ac-turnip] [-b] p1 p2 p3 ... pn
    
                OR
                
    !turnip [prophet|ac-turnip]
    
    prophet: brings you to https://turnipprophet.io/ 
    ac-turnip: brings you to https://ac-turnip.com/. This will also show a thumbnail of the graph
    -b: flag showing whether or not you're including the buying price. if not, ignore the flag
    p1 p2 ... pn: prices going Monday AM, Monday PM, ..., Saturday PM. entering a price of 0 indicates that you missed that day.
    
    Examples:
        !turnip ac-turnip
        !turnip prophet
        !turnip prophet -b 101 78 94 65 0 44 
        !turnip ac-turnip 87 65 107 113 120 119 110 90
        !turnip prophet 0 0 0 0 90 0 56
    '''
    if len(arg) == 1:
        if arg[0] == 'prophet':
            await ctx.send('https://turnipprophet.io/')
        
        elif arg[0] == 'ac-turnip':
            await ctx.send('https://ac-turnip.com/')
            
    else:
        is_buying_price = arg[1] == '-b'
        try:
            if not is_buying_price:
                int(arg[1])
                
        except ValueError:
            pass
            
        else:
            link = ''
            cmd = arg[0]
            
            if is_buying_price:
                arg = [int(i) for i in arg[2:]]
            else:
                arg = [int(i) for i in arg[1:]]
                
            embed = None
            if cmd == 'prophet':
                link = generate_turnip_prophet_link(arg, is_buying_price)
            elif cmd == 'ac-turnip':
                link, img_link = generate_turnip_ac_turnip_link(arg, is_buying_price)
                print(img_link)
                embed = discord.Embed(title='Turnip Price Trend',
                                      description=link)
                embed.set_image(url=img_link)
            if embed:
                await ctx.send(embed=embed)
            elif link:
                await ctx.send(link)
  
  
 
  
''' PLAYER PROFILE'''
@client.command(name='profile', 
                description='Gets a players profile')
async def profile(ctx, *args):
    '''
    This command gives general information about a player's town. These commands will only work if you've added your friend code to the bot. This information is entered in by the user:
    
    !profile @User - returns an embed with general information about the user's town
    !profile add [fruit|flower] item - adds/changes the user's fruit or flower to the specified item
    
    Examples:
    !profile @User
    !profile add fruit Peaches
    !profile add flower Roses
    '''
    mentioned_user = None
    player_name = 'player_name'
    island_fruit = 'island_fruit'
    island_flowers = 'island_flowers'
    friend_code = None
    
    if ctx.message.mentions:
        mentioned_user = ctx.message.mentions[0]
        friend_code = get_friend_code(mentioned_user.id)
        profile = query_profile(friend_code)
        
        if friend_code == -1 or profile == -1:
            await ctx.send('Player not found.')
        
        else:    
            embed = discord.Embed(title='Player Profile')
            embed.add_field(name='Player name', value=profile[player_name], inline=True)
            embed.add_field(name='Friend code', value=friend_code, inline=True)
            embed.set_thumbnail(url=mentioned_user.avatar_url)
            
            if island_fruit in list(profile.keys()):
                embed.add_field(name='Island fruit', value=profile[island_fruit], inline=False)
                
            if island_flowers in list(profile.keys()):
                embed.add_field(name='Island flowers', value=profile[island_flowers], inline=True)
                
            await ctx.send(embed=embed)
        
    elif args[0] == 'add':
        author = ctx.message.author
        ret = add_to_profile(args, author)
        
        if ret == -1:
            await ctx.send('No target specified. Possible tags are `fruit` or `flower`')
            
        elif ret == -2:
            await ctx.send('Player not found. You must add your friend code to the bot to use this feature. For help using this feature, type `!help add`')
        
        else:
            await ctx.send('{} was updated successfully.'.format(ctx.message.author)) 
            
    else:
        await ctx.send('Command not recognized. For help using the `profile` command, type `!help profile`')
            
            

client.run(TOKEN)