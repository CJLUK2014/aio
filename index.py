import discord
from discord.ext import commands
import asyncio
import random
import urllib.parse
import aiohttp
from datetime import datetime, timedelta, timezone
import os

# Get the bot token from environment variables
BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
# Get the mod logs channel ID from environment variables
MOD_LOGS_CHANNEL_ID = os.environ.get('MOD_LOGS_CHANNEL_ID')

# We need to tell the bot what it's allowed to do!
intents = discord.Intents.default()
intents.message_content = True  # Make sure to add this if your bot reads messages!
intents.members = True # Make sure to add this if you want info about server members!

# Now we create the bot and give it the intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Let's store the time when the bot starts
startup_time = datetime.now(timezone.utc)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name='Made by Creative Vivo Designs'))

@bot.command(name='clear', help='Clears a specified number of messages.')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount > 0:
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'{amount} messages cleared by {ctx.author.mention}.', delete_after=3)
    else:
        await ctx.send('Please enter a number greater than 0 to clear messages.')

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Sorry, you don't have permission to use the `clear` command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please enter a valid number of messages to clear.")

@bot.command(name='ban', help='Bans a specified member from the server.')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if member == ctx.author:
        await ctx.send("You can't ban yourself!")
        return
    if member == bot.user:
        await ctx.send("I can't ban myself!")
        return

    confirmation_message = f"Are you SUPER sure you want to ban **{member.name}**? Reason: {reason if reason else 'No reason given.'} (Type `yes` to confirm)"
    await ctx.send(confirmation_message)

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() == 'yes'

    try:
        await bot.wait_for('message', check=check, timeout=15.0)
        await member.ban(reason=reason)
        await ctx.send(f"**{member.name}** has been BANNED! Reason: {reason if reason else 'No reason given.'}")

        if MOD_LOGS_CHANNEL_ID:
            mod_logs_channel = bot.get_channel(int(MOD_LOGS_CHANNEL_ID))
            if mod_logs_channel:
                log_message = f"🔨 **Ban Hammer Strikes!** {member.name} (`{member.id}`) banned by {ctx.author.name} (`{ctx.author.id}`). Reason: {reason if reason else 'No reason given.'}"
                await mod_logs_channel.send(log_message)
            else:
                await ctx.send("⚠️ **Warning:** The MOD_LOGS_CHANNEL_ID in the environment variables is not a valid channel ID.")
        else:
            await ctx.send("⚠️ **Warning:** Please set the `MOD_LOGS_CHANNEL_ID` environment variable to enable ban logging.")

    except asyncio.TimeoutError:
        await ctx.send("Ban confirmation timed out! NO BAN THIS TIME.")
    except discord.Forbidden:
        await ctx.send("Uh oh! I don't have the power to ban that member.")
    except discord.HTTPException:
        await ctx.send("Something went wrong with the ban! MY POWER FAILS!")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("WHOA THERE! You don't have the ban hammer for that!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You gotta tell me WHO to ban!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Hmm, I can't find that person!")

@bot.command(name='userinfo', help='Displays information about a specified user.')
async def userinfo(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    embed = discord.Embed(title=f"ALL ABOUT **{member.name}**!", color=discord.Color.blue())
    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Nickname", value=member.nick if member.nick else "No Nickname", inline=False)
    embed.add_field(name="Joined Server At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.add_field(name="Joined Discord At", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    roles = [role.name for role in member.roles if role != ctx.guild.default_role]
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "No Roles", inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='serverinfo', help='Displays information about the current server.')
async def serverinfo(ctx):
    embed = discord.Embed(title=f"**{ctx.guild.name}** - AMAZING DETAILS!", color=discord.Color.green())
    embed.add_field(name="Server ID", value=ctx.guild.id, inline=False)
    embed.add_field(name="Owner", value=ctx.guild.owner.mention, inline=False)
    embed.add_field(name="Member Count", value=ctx.guild.member_count, inline=False)
    embed.add_field(name="Created At", value=ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.add_field(name="Boost Level", value=ctx.guild.premium_tier, inline=False)
    embed.add_field(name="Boost Count", value=ctx.guild.premium_subscription_count, inline=False)
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed)

@bot.command(name='say', help='Repeats the message you provide.')
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command(name='flip', help='Flips a coin and shows the result.')
async def flip(ctx):
    outcome = random.choice(["**HEADS!**", "**TAILS!**"])
    await ctx.send(outcome)

@bot.command(name='roll', help='Rolls a specified number of dice with a specified number of sides.')
async def roll(ctx, num_dice: int = 1, num_sides: int = 6):
    if num_dice > 0 and num_sides > 0 and num_dice <= 10 and num_sides <= 100:
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        roll_text = ", ".join(map(str, rolls))
        await ctx.send(f'{ctx.author.mention} rolled {num_dice} dice with {num_sides} sides each! Results: **[{roll_text}]** (Total: **{sum(rolls)}**)')
    else:
        await ctx.send('WHOA THERE! Invalid number of dice or sides! Try again with 1-10 dice and 1-100 sides.')

@bot.command(name='8ball', help='Answers a yes/no question as an 8-ball would.')
async def _8ball(ctx, *, question):
    responses = [
        "It is **certain!**", "**Definitely** so!", "**Without a doubt!**", "**Yes** - absolutely!",
        "You may **rely on it!**", "**As I see it, yes!**", "**Most likely!**", "**Outlook good!**",
        "**YES!**", "**Signs point to yes!**", "Reply is a bit **hazy**, try again...", "Ask again **later!**",
        "Better not tell you **now!**", "Cannot predict **now!**", "Concentrate and ask again...",
        "**Don't count on it!**", "My reply is a big **NO!**", "My sources say **NO!**", "**Outlook not so good!**",
        "**Very doubtful!**"
    ]
    answer = random.choice(responses)
    await ctx.send(f'{ctx.author.mention} asked: {question}\n🎱 Answer: **{answer}**')

@bot.command(name='bold', help='Makes the given text appear in bold.')
async def bold(ctx, *, text):
    await ctx.send(f'**{text}**')

@bot.command(name='image', help='Searches for an image online based on your query.')
async def image(ctx, *, query):
    search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&tbm=isch"
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status == 200:
                html = await response.text()
                start = html.find('img src="') + len('img src="')
                end = html.find('"', start)
                if start != -1 and end != -1:
                    image_url = html[start:end]
                    await ctx.send(image_url)
                else:
                    await ctx.send("Hmm, I couldn't find an image for that!")
            else:
                await ctx.send("Oops! Something went wrong with the image search!")

@bot.command(name='remind', help='Sets a reminder for you after a specified time.')
async def remind(ctx, time_str, *, message):
    try:
        time_parts = time_str.lower().split()
        if len(time_parts) != 2:
            await ctx.send("Oops! Please use the format: `!remind <number> <unit> <message>` (e.g., `!remind 5 minutes Do homework`). Units can be seconds, minutes, or hours.")
            return

        value = int(time_parts[0])
        unit = time_parts[1]

        if unit.startswith("second"):
            wait_time = value
        elif unit.startswith("minute"):
            wait_time = value * 60
        elif unit.startswith("hour"):
            wait_time = value * 3600
        else:
            await ctx.send("Invalid time unit! Please use seconds, minutes, or hours.")
            return

        if wait_time <= 0:
            await ctx.send("Please enter a positive time value.")
            return

        await ctx.send(f"Okay, {ctx.author.mention}, I'll remind you in {time_str} to: {message}")
        await asyncio.sleep(wait_time)
        await ctx.author.send(f"⏰ Reminder! You asked me to remind you to: {message}")

    except ValueError:
        await ctx.send("Invalid time format! Please make sure the number of seconds/minutes/hours is a valid number.")
    except Exception as e:
        print(f"An error occurred: {e}")
        await ctx.send("Something went wrong with setting the reminder.")

@bot.command(name='poll', help='Creates a poll with up to 10 options.')
async def poll(ctx, question, *options):
    if len(options) < 2 or len(options) > 10:
        await ctx.send("Please provide between 2 and 10 poll options, each in quotes!")
        return

    embed = discord.Embed(title=f"📊 {question}", color=discord.Color.orange())
    reactions = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯"]
    option_str = ""
    for i, option in enumerate(options):
        option_str += f"{reactions[i]} {option}\n"
    embed.description = option_str
    poll_message = await ctx.send(embed=embed)
    for i in range(len(options)):
        await poll_message.add_reaction(reactions[i])

@bot.command(name='commands', help='Lists all available commands.')
async def list_commands(ctx):
    embed = discord.Embed(title="🤖 All My Awesome Commands!", color=discord.Color.blurple())
    command_list = []
    for command in bot.commands:
        if not command.hidden:  # Don't show hidden commands
            command_list.append(f"`!{command.name}` - {command.help if command.help else 'No description available.'}")

    # Basic pagination - we'll send multiple messages if there are too many commands
    commands_per_page = 10
    pages = [command_list[i:i + commands_per_page] for i in range(0, len(command_list), commands_per_page)]

    for i, page in enumerate(pages):
        page_embed = discord.Embed(title=f"🤖 All My Awesome Commands! (Page {i+1}/{len(pages)})", color=discord.Color.blurple())
        page_embed.description = "\n".join(page)
        await ctx.send(embed=page_embed)

@bot.command(name='dm', help='Sends a direct message to a specified user.')
async def send_dm(ctx, user: discord.Member, *, message):
    try:
        await user.send(f"Hey! {ctx.author.name} asked me to send you this message: {message}")
        await ctx.send(f"Sent a DM to {user.name}!")
    except discord.Forbidden:
        await ctx.send(f"Hmm, I couldn't DM {user.name}. They might have their DMs turned off for people who aren't friends.")
    except discord.HTTPException:
        await ctx.send("Something went wrong while trying to send the DM.")

@bot.command(name='hug', help='Sends a virtual hug to a specified user (or yourself).')
async def hug(ctx, member: discord.Member = None):
    if member:
        await ctx.send(f"{ctx.author.mention} gives a big hug to {member.mention}! 🤗")
    else:
        await ctx.send(f"{ctx.author.mention} gives a big self-hug! 🤗")

@bot.command(name='pat', help='Sends a virtual pat on the head to a specified user (or yourself).')
async def pat(ctx, member: discord.Member = None):
    if member:
        await ctx.send(f"{ctx.author.mention} pats {member.mention} gently on the head! 👋")
    else:
        await ctx.send(f"{ctx.author.mention} pats themselves on the head! 👋")

@bot.command(name='uptime', help='Shows how long the bot has been running.')
async def get_uptime(ctx):
    now = datetime.now(timezone.utc)
    uptime = now - startup_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    start_time_str = startup_time.strftime("%Y-%m-%d at %H:%M:%S UTC")
    await ctx.send(f"My awesome journey started on **{start_time_str}**. I've been running for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds!")

@bot.command(name='ping', help='Checks the bot\'s latency (how fast it responds).')
async def ping(ctx):
    latency = round(bot.latency * 1000)  # Convert to milliseconds
    await ctx.send(f'Pong! 🏓 My latency is **{latency}ms**.')

@bot.command(name='avatar', help='Displays the avatar of a specified user.')
async def avatar(ctx, member: discord.Member = None):
    user = member if member else ctx.author
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    embed = discord.Embed(title=f"Avatar of **{user.name}**", color=discord.Color.purple())
    embed.set_image(url=avatar_url)
    await ctx.send(embed=embed)

@bot.command(name='servericon', help='Displays the icon of the current server.')
async def servericon(ctx):
    if ctx.guild.icon:
        embed = discord.Embed(title=f"Server Icon of **{ctx.guild.name}**", color=discord.Color.dark_orange())
        embed.set_image(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)
    else:
        await ctx.send("This server doesn't have an icon!")

@bot.command(name='define', help='Searches for the definition of a word.')
async def define(ctx, *, word):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}") as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    meaning = data[0]['meanings'][0]['definitions'][0]['definition']
                    phonetic = data[0].get('phonetic', 'No phonetic available')
                    embed = discord.Embed(title=f"Definition of **{word}**", color=discord.Color.gold())
                    embed.add_field(name="Phonetic", value=phonetic, inline=False)
                    embed.add_field(name="Definition", value=meaning, inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"Hmm, I couldn't find a definition for **{word}**!")
            elif response.status == 404:
                await ctx.send(f"Sorry, I couldn't find the word **{word}** in my dictionary!")
            else:
                await ctx.send("Oops! Something went wrong while looking up the definition.")

# Example of a command that might need pages (let's pretend we have a lot of server emojis)
@bot.command(name='emojis', help='Lists all the emojis on the server.')
async def emojis(ctx):
    server_emojis = ctx.guild.emojis
    if not server_emojis:
        await ctx.send("This server doesn't have any custom emojis!")
        return

    emoji_list = [f"<:{emoji.name}:{emoji.id}>" for emoji in server_emojis]
    emojis_per_page = 20
    pages = [emoji_list[i:i + emojis_per_page] for i in range(0, len(emoji_list), emojis_per_page)]

    if not pages:
        return

    async def send_page(page_num):
        embed = discord.Embed(title=f"Server Emojis (Page {page_num + 1}/{len(pages)})", color=discord.Color.lighter_grey())
        embed.description = " ".join(pages[page_num])
        message = await ctx.send(embed=embed)
        return message

    current_page = 0
    message = await send_page(current_page)

    if len(pages) > 1:
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and reaction.message == message and str(reaction.emoji) in ["⬅️", "➡️"]

        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)

                if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                    current_page += 1
                    await message.edit(embed=discord.Embed(title=f"Server Emojis (Page {current_page + 1}/{len(pages)})", color=discord.Color.lighter_grey(), description=" ".join(pages[current_page])))
                    await message.remove_reaction(reaction, user)
                elif str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=discord.Embed(title=f"Server Emojis (Page {current_page + 1}/{len(pages)})", color=discord.Color.lighter_grey(), description=" ".join(pages[current_page])))
                    await message.remove_reaction(reaction, user)
                else:
                    await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                for reaction in message.reactions:
                    if reaction.me:
                        await message.remove_reaction(reaction.emoji, bot.user)
                break

bot.run(BOT_TOKEN)
