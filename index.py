import discord
from discord.ext import commands
import os
import random
import datetime
import aiohttp
from discord.ui import View, Button

# Get the bot token and log channel ID from environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
LOG_CHANNEL_ID = os.environ.get('LOG_CHANNEL_ID')

# Setting up the bot's intents (what it's allowed to do)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # So we can get info about server members

# Now we create the bot! '!' will be the prefix you use for commands (like !hello)
bot = commands.Bot(command_prefix='??', intents=intents)

# --- Helper Function for Paged Embeds ---
class HelpPaginator(View):
    def __init__(self, help_commands, per_page=8): # Show 8 commands per page
        super().__init__(timeout=60)
        self.help_commands = list(help_commands)
        self.per_page = per_page
        self.current_page = 0
        self.update_buttons()

    async def send_help(self, ctx):
        self.message = await ctx.send(embed=self.get_page(), view=self)

    def get_page(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        commands_on_page = self.help_commands[start:end]

        embed = discord.Embed(title="🤖 Bot Commands", color=discord.Color.blurple())
        for name, command in commands_on_page:
            embed.add_field(name=f"!{name}", value=command.help if command.help else "No description available.", inline=False)
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.help_commands) // self.per_page + (1 if len(self.help_commands) % self.per_page > 0 else 0)}")
        return embed

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.help_commands) // self.per_page + (1 if len(self.help_commands) % self.per_page > 0 else 0) - 1

    @discord.ui.button(label='<', style=discord.ButtonStyle.grey)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user == interaction.message.author:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_page(), view=self)
        else:
            await interaction.response.send_message("Hey, these buttons aren't for you!", ephemeral=True)

    @discord.ui.button(label='>', style=discord.ButtonStyle.grey)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user == interaction.message.author:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_page(), view=self)
        else:
            await interaction.response.send_message("Hey, these buttons aren't for you!", ephemeral=True)

# --- Bot Events ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    await bot.change_presence(activity=discord.Game(name='with lots of commands!'))
    if LOG_CHANNEL_ID:
        log_channel = bot.get_channel(int(LOG_CHANNEL_ID))
        if log_channel:
            embed = discord.Embed(title="Bot Online!", description=f"{bot.user.name} is now online!", color=discord.Color.green())
            await log_channel.send(embed=embed)
        else:
            print(f"Warning: Log channel with ID {LOG_CHANNEL_ID} not found in environment variables.")
    else:
        print("Warning: LOG_CHANNEL_ID environment variable not set.")

# --- Bot Commands ---

@bot.command(name='coinflip', help='Flips a coin and shows the result.')
async def coinflip(ctx):
    result = random.choice(['Heads!', 'Tails!'])
    await ctx.send(result)

@bot.command(name='roll', help='Rolls a dice (default is 6 sides). You can specify the number of sides (e.g., !roll 20).')
async def roll(ctx, sides: int = 6):
    if 1 <= sides <= 100:
        result = random.randint(1, sides)
        await ctx.send(f'You rolled a {result} on a {sides}-sided dice!')
    else:
        await ctx.send('Please choose a number of sides between 1 and 100.')

@bot.command(name='userinfo', help='Shows detailed information about a user.')
async def userinfo(ctx, member: discord.Member = None):
    user = member or ctx.author
    embed = discord.Embed(title=f"User Info for {user.name}", color=discord.Color.dark_blue())
    embed.add_field(name="User ID", value=user.id, inline=False)
    embed.add_field(name="Nickname", value=user.nick if user.nick else "No Nickname", inline=False)
    embed.add_field(name="Joined Discord At", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.add_field(name="Joined Server At", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    roles = [role.mention for role in user.roles if role != ctx.guild.default_role]
    if roles:
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles), inline=False)
    else:
        embed.add_field(name="Roles", value="No special roles", inline=False)
    embed.add_field(name="Bot?", value="Yes" if user.bot else "No", inline=True)
    embed.add_field(name="Status", value=user.status, inline=True)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    await ctx.send(embed=embed)
@bot.command(name='serverinfo', help='Shows detailed information about the server.')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=guild.name, color=discord.Color.dark_green())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="👑 Owner", value=f"{guild.owner.mention} (ID: {guild.owner.id})", inline=False)

    members_online = sum(1 for member in guild.members if member.status != discord.Status.offline)
    members_offline = len(guild.members) - members_online
    embed.add_field(name="<:online:313956277822080002> Members", value=f"🟢 Online: {members_online}\n⚪ Offline: {members_offline}\n<:members:887589885941534720> Total: {guild.member_count}", inline=True) # Using standard Discord online emoji and a generic 'members' emoji (you might need a better one!)

    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    embed.add_field(name="<:channels:1358382823504875620> Channels", value=f"#️⃣ Text: {text_channels}\n🔊 Voice: {voice_channels}\n<:channels:1358382823504875620> Total: {len(guild.channels)}", inline=True) # Using generic text/voice/channels emojis (you might need better ones!)

    embed.add_field(name="<:roles:1358383230167945287> Roles", value=len(guild.roles), inline=True) # Generic role emoji
    embed.add_field(name="Emojis", value=len(guild.emojis), inline=True) # Generic emoji
    embed.add_field(name="🌎 Voice Region", value=str(guild.voice_channels[0].rtc_region if guild.voice_channels else "N/A"), inline=True)

    try:
        bans = await guild.bans()
        embed.add_field(name="🔨 Ban Count", value=len(bans), inline=True)
    except discord.Forbidden:
        embed.add_field(name="🔨 Ban Count", value="N/A (Bot doesn't have permission)", inline=True)

    embed.add_field(name="<:boosts:1358383678946021497> Boosts", value=f"{guild.premium_subscription_count} (Level {guild.premium_tier})", inline=True) # Generic boost emoji

    features = []
    if "AUTOMODERATION" in guild.features:
        features.append("🛡️ Auto moderation")
    if "COMMUNITY" in guild.features:
        features.append("🏘️ Community")
    if "GUILD_ONBOARDING" in guild.features:
        features.append("👋 Guild onboarding")
    if "GUILD_ONBOARDING_EVER_ENABLED" in guild.features:
        features.append("✅ Guild onboarding ever enabled")
    if "GUILD_ONBOARDING_HAS_PROMPTS" in guild.features:
        features.append("❓ Guild onboarding has prompts")
    if "NEWS" in guild.features:
        features.append("📰 News")
    if features:
        embed.add_field(name="⚙️ Server Features", value="\n".join(features), inline=False)
    else:
        embed.add_field(name="⚙️ Server Features", value="None", inline=False)

    created_at = guild.created_at
    now = datetime.datetime.utcnow()
    difference = now - created_at
    years = difference.days // 365
    remaining_days = difference.days % 365
    months = remaining_days // 30
    weeks = remaining_days // 7
    days = remaining_days % 7

    created_ago = f"{created_at.strftime('%dth %b %y')} ({years} year{'s' if years != 1 else ''} and {months} month{'s' if months != 1 else ''} and {weeks} week{'s' if weeks != 1 else ''} ago)"
    embed.add_field(name="🗓️ Created", value=created_ago, inline=False)

    await ctx.send(embed=embed)
    
@bot.command(name='ping', help='Checks the bot\'s latency (how fast it responds).')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! 🏓 My latency is {latency}ms.')

@bot.command(name='say', help='Makes the bot say what you tell it to (use responsibly!).')
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command(name='avatar', help='Displays the avatar of the mentioned user.')
async def avatar(ctx, member: discord.Member = None):
    user = member or ctx.author
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    embed = discord.Embed(title=f"Avatar of {user.name}", color=discord.Color.purple())
    embed.set_image(url=avatar_url)
    await ctx.send(embed=embed)

@bot.command(name='time', help='Shows the current time.')
async def current_time(ctx):
    now_utc = datetime.datetime.utcnow()
    await ctx.send(f'The current time is: {now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")}')

@bot.command(name='calculate', help='Performs a simple calculation (e.g., !calculate 2 + 2).')
async def calculate(ctx, *, expression):
    try:
        result = eval(expression)  # Be careful with using eval in real bots!
        await ctx.send(f'The result of `{expression}` is: **{result}**')
    except Exception as e:
        await ctx.send(f'Hmm, I couldn\'t calculate that. Please use a valid expression.')

@bot.command(name='choose', help='Chooses one option from the given choices (separate with spaces, e.g., !choose Pizza Burger Sushi).')
async def choose(ctx, *choices):
    if not choices:
        await ctx.send('Please give me some options to choose from!')
        return
    chosen = random.choice(choices)
    embed = discord.Embed(title="🤔 I Choose...", description=f"I've decided on: **{chosen}**!", color=discord.Color.blurple())
    await ctx.send(embed=embed)

@bot.command(name='google', help='Performs a simple Google search (use with caution!).')
async def google_search(ctx, *, query):
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    embed = discord.Embed(title=f'🔍 Google Search for "{query}"', url=search_url, description=f'Here is a Google search for "{query}". Be careful about what you click!', color=discord.Color.greyple())
    await ctx.send(embed=embed)

@bot.command(name='fact', help='Tells you a random fun fact!')
async def random_fact(ctx):
    facts = [
        "Honey never spoils.",
        "Bananas are berries.",
        "The Eiffel Tower can be 15 cm taller during the summer.",
        "A group of flamingos is called a 'flamboyance'.",
        "Octopuses have three hearts."
    ]
    embed = discord.Embed(title="💡 Fun Fact!", description=random.choice(facts), color=discord.Color.lighter_grey())
    await ctx.send(embed=embed)

@bot.command(name='joke', help='Tells you a random joke!')
async def random_joke(ctx):
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "What do you call a lazy kangaroo? Pouch potato!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "What do you call a fish with no eyes? Fsh!",
        "Why did the bicycle fall over? Because it was two tired!"
    ]
    embed = discord.Embed(title="😂 Joke Time!", description=random.choice(jokes), color=discord.Color.yellow())
    await ctx.send(embed=embed)

@bot.command(name='wouldyourather', help='Asks a random Would You Rather question.')
async def would_you_rather(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://wyr.askme.today/api/v1/random") as response:
            if response.status == 200:
                data = await response.json()
                if 'question' in data:
                    embed = discord.Embed(title="🤔 Would You Rather...", description=data["question"], color=discord.Color.purple())
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Hmm, I couldn't think of a 'Would You Rather' question right now.")
            else:
                await ctx.send("Oops! Something went wrong while getting a 'Would You Rather' question.")

@bot.command(name='cat', help='Sends a random picture of a cat!')
async def cat(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    await ctx.send(data[0]['url'])
                else:
                    await ctx.send("Sorry, no cat pictures found right now!")
            else:
                await ctx.send("Oops! Something went wrong while getting a cat picture.")

@bot.command(name='dog', help='Sends a random picture of a dog!')
async def dog(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://dog.ceo/api/breeds/image/random") as response:
            if response.status == 200:
                data = await response.json()
                if data['status'] == 'success':
                    await ctx.send(data['message'])
                else:
                    await ctx.send("Sorry, no dog pictures found right now!")
            else:
                await ctx.send("Oops! Something went wrong while getting a dog picture.")

@bot.command(name='meme', help='Sends a random funny meme!')
async def meme(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://meme-api.com/gimme") as response:
            if response.status == 200:
                data = await response.json()
                if data['url']:
                    await ctx.send(data['url'])
                else:
                    await ctx.send("Sorry, no memes found right now!")
            else:
                await ctx.send("Oops! Something went wrong while getting a meme.")

@bot.command(name='rps', help='Play Rock, Paper, Scissors with the bot! Use !rps rock, !rps paper, or !rps scissors.')
async def rps(ctx, choice: str):
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    user_choice = choice.lower()

    if user_choice not in choices:
        await ctx.send("Please choose rock, paper, or scissors!")
        return

    if user_choice == bot_choice:
        embed = discord.Embed(title="🤝 Rock, Paper, Scissors!", description=f"It's a tie! We both chose {user_choice}.", color=discord.Color.grey())
        await ctx.send(embed=embed)
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        embed = discord.Embed(title="🎉 Rock, Paper, Scissors!", description=f"You win! You chose {user_choice} and I chose {bot_choice}.", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="🤖 Rock, Paper, Scissors!", description=f"I win! I chose {bot_choice} and you chose {user_choice}.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='magicball', help='Ask the magic 8-ball a question!')
async def magicball(ctx, *, question):
    responses = [
        "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes - definitely.",
        "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
        "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
        "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
        "Don't count on it.","My reply is no.", "My sources say no.", "Outlook not so good.",
        "Very doubtful."
    ]
    answer = random.choice(responses)
    embed = discord.Embed(title="🎱 The Magic 8-Ball Says...", description=answer, color=discord.Color.dark_grey())
    embed.add_field(name="Your Question:", value=question, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='color', help='Shows a color based on the hex code you provide (e.g., !color #FF0000).')
async def color(ctx, hex_code):
    try:
        hex_code = hex_code.replace("#", "")
        if len(hex_code) != 6:
            await ctx.send("That doesn't look like a valid color code! Make sure it's like #RRGGBB.")
            return
        rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        embed = discord.Embed(title=f"Color: #{hex_code.upper()}", color=discord.Color.from_rgb(*rgb))
        embed.add_field(name="RGB Value", value=f"({rgb[0]}, {rgb[1]}, {rgb[2]})")
        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Oops! That doesn't seem like a valid hex color code. Please try again!")

@bot.command(name='gif', help='Searches for a GIF based on your search term (use responsibly!).')
async def gif(ctx, *, search_term):
    api_key = os.environ.get('GIPHY_API_KEY') # You'll need a Giphy API key!
    if not api_key:
        await ctx.send("Sorry, the GIF command is not set up properly right now.")
        return
    params = {"api_key": api_key, "q": search_term, "limit": 1, "rating": "g"} # Keep it G-rated!
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.giphy.com/v1/gifs/search", params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data['data']:
                    await ctx.send(data['data'][0]['embed_url'])
                else:
                    await ctx.send(f"Hmm, I couldn't find a GIF for '{search_term}'. Maybe try a different search?")
            else:
                await ctx.send("Oops! Something went wrong while searching for a GIF.")

@bot.command(name='serverlogo', help='Shows the server\'s logo (if it has one).')
async def serverlogo(ctx):
    if ctx.guild.icon:
        embed = discord.Embed(title=f"Server Logo for {ctx.guild.name}", color=discord.Color.light_grey())
        embed.set_image(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)
    else:
        await ctx.send("This server doesn't have a logo!")

# --- Help Command (now called 'commands') ---
@bot.command(name='commands', help='Shows a list of available commands with descriptions, and you can flip through pages!')
async def help_command(ctx):
    help_commands = {}
    for command in bot.commands:
        if not command.hidden:
            help_commands[command.name] = command

    paginator = HelpPaginator(help_commands.items())
    await paginator.send_help(ctx)

# --- Running the Bot ---
import asyncio
bot.run(BOT_TOKEN)
