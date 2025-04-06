import discord
from discord.ext import commands
import asyncio
import random
import urllib.parse
import aiohttp
from datetime import datetime, timedelta
import os

# Get the bot token from environment variables
BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
# Get the mod logs channel ID from environment variables
MOD_LOGS_CHANNEL_ID = os.environ.get('MOD_LOGS_CHANNEL_ID')

# We need to tell the bot what it's allowed to do!
intents = discord.Intents.default()
intents.message_content = True  # Make sure to add this if your bot reads messages!

# Now we create the bot and give it the intents
bot = commands.Bot(command_prefix='??', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name='Made by Creative Vivo Designs'))

@bot.command()
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

@bot.command()
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

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    embed = discord.Embed(title=f"ALL ABOUT **{member.name}**!", color=discord.Color.blue())
    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Joined Server At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.add_field(name="Joined Discord At", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    embed = discord.Embed(title=f"**{ctx.guild.name}** - ALL THE DETAILS!", color=discord.Color.green())
    embed.add_field(name="Server ID", value=ctx.guild.id, inline=False)
    embed.add_field(name="Owner", value=ctx.guild.owner.mention, inline=False)
    embed.add_field(name="Member Count", value=ctx.guild.member_count, inline=False)
    embed.add_field(name="Created At", value=ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed)

@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command()
async def flip(ctx):
    outcome = random.choice(["**HEADS!**", "**TAILS!**"])
    await ctx.send(outcome)

@bot.command()
async def roll(ctx, num_dice: int = 1, num_sides: int = 6):
    if num_dice > 0 and num_sides > 0 and num_dice <= 10 and num_sides <= 100:
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        roll_text = ", ".join(map(str, rolls))
        await ctx.send(f'{ctx.author.mention} rolled {num_dice} dice with {num_sides} sides each! Results: **[{roll_text}]** (Total: **{sum(rolls)}**)')
    else:
        await ctx.send('WHOA THERE! Invalid number of dice or sides! Try again with 1-10 dice and 1-100 sides.')

@bot.command(name='8ball')
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

@bot.command()
async def bold(ctx, *, text):
    await ctx.send(f'**{text}**')

@bot.command()
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

@bot.command()
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

@bot.command()
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

@bot.command(name='commands')
async def list_commands(ctx):
    command_list = [command.name for command in bot.commands]
    await ctx.send(f"Here are all the commands you can use with this bot: `{'`, `'.join(command_list)}`")

@bot.command(name='dm')
async def send_dm(ctx, user: discord.Member, *, message):
    try:
        await user.send(f"Hey! {ctx.author.name} asked me to send you this message: {message}")
        await ctx.send(f"Sent a DM to {user.name}!")
    except discord.Forbidden:
        await ctx.send(f"Hmm, I couldn't DM {user.name}. They might have their DMs turned off for people who aren't friends.")
    except discord.HTTPException:
        await ctx.send("Something went wrong while trying to send the DM.")

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN environment variable not set!")
