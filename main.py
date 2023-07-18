import discord
from discord.ext import commands

import sqlite3

import sys
import json
import random
import datetime

intents = discord.Intents.default()
intents.message_content = True

TOKEN = "INSERT TOKEN HERE" 
bot = commands.Bot(command_prefix='!', intents=intents)

# globals
quotes = []
conn, cur = None, None

def get_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def load_quotes():
    with open('quotes.json', 'r') as file:
        data = json.load(file)
    return data['messages']

@bot.event
async def on_ready():
    global quotes, conn, cur
    print(f'Bot connected as {bot.user.name}')

    print('Loading quotes JSON...')
    quotes = load_quotes()
    print('Quotes loaded.')

    print('Loading voting database...')
    conn = sqlite3.connect('voting.db')
    cur = conn.cursor()
    print('Voting database loaded.')

@bot.command()
async def commands(ctx):
    embed = discord.Embed(
        title="List of commands",
        description='''
            `!quote` generate a random quote
            `!rating [message_id]` output the rating for a message
            ''',
        color=discord.Color.light_gray()
    )
    await ctx.send(embed=embed)

@bot.command()
async def quote(ctx):
#async def tquote(ctx):
    timestamp = get_time()
    print(f"[{timestamp}] User {ctx.author.name} called '!quote'")

    # extract message from random quote
    random_message = random.choice(quotes)
    content = '' 
    attachment_urls = []
    if random_message['content']:
        content = random_message['content']
    if random_message['attachments']:
        attachment_urls = [attachment['url'] for attachment in random_message['attachments']]
        content += '\n'.join(attachment_urls)
        '''
        for i in range(len(random_message['attachments'])):
            if i != 0 or content:
                content += '\n'
            attachment = random_message['attachments'][i]['url']
            content += f'{attachment}'
            attachment_urls.append(attachment)
        '''

    if content:
        # extract votes from message_id
        message_id = random_message['id']
        cur.execute('''
            SELECT 
                upvotes, downvotes
            FROM
                messages
            WHERE
                message_id = ?
        ''', (message_id,))
        row = cur.fetchone()
        
        # extract upvotes/downvotes from the fetched row
        upvotes, downvotes = 0, 0
        if row:
            upvotes = len(row[0].split(',') if row[0] else [])
            downvotes = len(row[1].split(',') if row[1] else [])

        # build quote embed
        submitted_by = random_message['author']['name']
        date = random_message['timestamp'].split('T')[0] 

        embed = discord.Embed(
            title=f"Submitted by {submitted_by} on {date}",
            description=content,
            color=discord.Color.random()
        )
        embed.add_field(
            name="Rating",
            value=f"**{upvotes-downvotes}** ({upvotes}🔺 {downvotes}🔻)"
        )
        embed.set_footer(text=f"ID: {message_id}")
        if attachment_urls:
            embed.set_image(url=attachment_urls[0])

        # send message
        message = await ctx.send(embed=embed)

        # add voting reacts
        await message.add_reaction('🔺')
        await message.add_reaction('🔻')
        await message.add_reaction('🚫')
    else:
        print("Error")
        await ctx.send("Error retrieving quote, ping pingo")

@bot.command()
async def rating(ctx, message_id=None):
    if message_id is None:
        await ctx.send("Usage: `!rating [message ID]`")
        return
    
    try:
        message_id = int(message_id)
    except ValueError:
        await ctx.send("Invalid message ID `{message_id}`")
        return
    
    # extract votes from message_id
    cur.execute('''
        SELECT 
            upvotes, downvotes
        FROM
            messages
        WHERE
            message_id = ?
    ''', (message_id,))
    row = cur.fetchone()

    if row is None:
        await ctx.send("No ratings found for the message ID `{message_id}`")
        return
    
    # extract upvotes/downvotes from the fetched row
    upvotes = len(row[0].split(',') if row[0] else [])
    downvotes = len(row[1].split(',') if row[1] else [])
    
    embed = discord.Embed(
        description=f"**{upvotes-downvotes}** ({upvotes}🔺 {downvotes}🔻)",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Rating for ID: {message_id}")
    
    message = await ctx.send(embed=embed)

@bot.event
async def on_reaction_add(reaction, user):
    # don't check for bot reactions
    if user.bot:
        return
    
    # check for reactions to bot messages
    if reaction.message.author == bot.user:
        message_id = None
        # check for reactions to quote messages
        if len(reaction.message.embeds) != 0:
            print(reaction.message.embeds)
            embed_footer = reaction.message.embeds[0].footer.text
            message_id = int(embed_footer.split(' ')[-1])
        else:
            return

        timestamp = get_time()
        print(f"[{timestamp}] '{user.name}' reacted {reaction.emoji} to message {reaction.message.id}")

        # select row based on message_id
        cur.execute('''
            SELECT 
                upvotes, downvotes
            FROM
                messages
            WHERE
                message_id = ?
        ''', (message_id,))
        row = cur.fetchone()
        
        if row is None:
            # if row does not exist, initialize with empty lists
            upvotes = []
            downvotes = []
        else:
            # extract upvotes/downvotes from the fetched row
            upvotes = row[0].split(',') if row[0] else []
            downvotes = row[1].split(',') if row[1] else []
        
        # update row only if user_id is not present
        # user_id can only belong to either upvote/downvote
        user_id = str(user.id)
        if reaction.emoji == '🔺' and user_id not in upvotes:
            if user_id in downvotes:
                downvotes.remove(user_id)
            upvotes.append(user_id)

        elif reaction.emoji == '🔻' and user_id not in downvotes:
            if user_id in upvotes:
                upvotes.remove(user_id)
            downvotes.append(user_id)

        elif reaction.emoji == '🚫':
            # remove vote from user
            if user_id in upvotes:
                upvotes.remove(user_id)
            elif user_id in downvotes:
                downvotes.remove(user_id)

        # update database
        cur.execute('''
            INSERT OR REPLACE INTO
                messages (message_id, upvotes, downvotes)
            VALUES
                (?, ?, ?)
        ''', (message_id, ','.join(upvotes), ','.join(downvotes)))
        conn.commit()

bot.run(TOKEN)
'''
try:
    bot.run(TOKEN)
except KeyboardInterrupt:
    print("Shutting down...")

    # close voting database
    cur.close()
    conn.close()
    
    sys.exit(0)
'''
