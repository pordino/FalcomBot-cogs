import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import escape, info, error
import codecs

class Rot13(commands.Cog):
    """Provides ROT-13 encoding/decoding functionality, and the ability to auto-decode messages with reactions."""

    guild_conf = {
            "react":                "\U0001f513",
            "on_react_decode_dm":   True,
            "auto_react_to":        "",
    }


    def __init__(self, bot):
        """Initialize ROT-13 cog."""
        self.bot = bot

        self.config = Config.get_conf(self, identifier=0xff5269620001)
        self.config.register_global(**Rot13.guild_conf)
        self.config.register_guild(**Rot13.guild_conf)

        #self.embed_cache = []

    async def on_message_without_command(self, message):
        """Handle on_message: Add auto-reaction if settings permit."""
        if not isinstance(message.channel, discord.TextChannel):
            # this is a DM or group DM, discard early
            return

        if message.type != discord.MessageType.default:
            # this is a system message, discard early
            return

        if message.author.id == self.bot.user.id:
            # this is ours, discard early
            return
        
        if message.author.bot:
            # this is a bot, discard early
            return

        if len(message.clean_content) == 0:
            # nothing to do, exit early
            return

        settings = await self.config.guild(message.guild).all()
        if settings["on_react_decode_dm"] and len(settings["auto_react_to"]) > 0:
            # do we need to add reaction?
            if settings["auto_react_to"] and \
                    settings["auto_react_to"].casefold() in message.clean_content.casefold():
                # if TEXT is not None and TEXT is present, do reaction
                try:
                    await message.add_reaction(settings["react"])
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

    async def on_raw_reaction_add(self, payload):
        """Handle on_raw_reaction_add: DM result of ROT-13 if settings permit."""
        user    = self.bot.get_user(payload.user_id)
        if user is None:
            # user could not be found and cannot be DMd
            return
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            # channel could not be found, inaccessible, or is gone
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            # message could not be found, inaccessible, or is gone
            return

        if   isinstance(channel, discord.TextChannel):
            settings = await self.config.guild(message.guild).all()
            footer = "In channel #{channel} on {guild}".format(channel = channel, guild = message.guild)
        elif isinstance(channel, discord.DMChannel):
            settings = await self.config.all()
            footer = ""
        elif isinstance(channel, discord.GroupChannel):
            settings = await self.config.all()
            if "name" in channel and len(channel.name):
                name = "group chat {}".format(channel.name)
            else:
                name = "a group chat with {n} members ({list})".format(n = len(channel.list), list = ", ".join([x.display_name for x in channel.list if x.id != user.id]))
            footer = "In group chat {name}".format(name = name)
        else:
            # unknown and unsupported channel type
            return

        if user.id == self.bot.user.id:
            # this is our reaction, discard early
            return

        if user.bot:
            # this reaction is a bot, discard early
            return

        #if message.id in self.embed_cache:
        #    # this is an embed we made from [p]rot13, let's skip the other checks
        #    content = message.embed.description
        #else:
        if message.type != discord.MessageType.default:
            # this is a system message, discard early
            return

        if message.author.id == self.bot.user.id:
            # this is our message, discard early
            return
        
        if message.author.bot:
            # this is a bot or a bot's reaction, discard early
            return

        if len(message.clean_content) == 0:
            # nothing to do, exit early
            return
        else:
            for prefix in await self.bot.get_prefix(message):
                if message.clean_content.startswith(prefix):
                    # starts with prefix, ignore command here
                    return

        content = message.clean_content

        if settings["on_react_decode_dm"]:
            # do we need to send a message?
            if settings["react"] == str(payload.emoji):
                embed = discord.Embed(description=self._rot13(content))
                if message.author.color != discord.Color.default():
                    embed.color = message.author.color
                embed.set_author(name=message.author.display_name)
                embed.set_thumbnail(url=message.author.avatar_url)
                embed.set_footer(text=footer)
                embed.timestamp = message.created_at
                #await message.author.send(content=self._rot13(message.clean_content))
                try:
                    await user.send(embed=embed)
                except (discord.Forbidden, discord.HTTPException):
                    # DMs disabled
                    pass

    @commands.command()
    async def rot13(self, ctx, *, text):
        """Encodes text using ROT-13."""
        if isinstance(ctx.channel, discord.TextChannel):
            # this not is a DM or group DM
            #message = ctx.message
            #footer = "In channel #{channel} on {guild}".format(channel = ctx.channel, guild = message.guild)
            #async with ctx.typing():
            await ctx.send(content=error("This is a server channel. The ROT-13 command is supported for direct messages only. The purpose is to make an encoded message."))
               #try:
               #    await message.delete()
               #except (discord.Forbidden, discord.HTTPException):
               #    # permissions to delete here denied
               #    await ctx.send(content=error("This is a public location and I do not have permission to delete your message!"))
               #    return

               #embed = discord.Embed(description=self._rot13(text))
               #if message.author.color != discord.Color.default():
               #    embed.color = message.author.color
               #embed.set_author(name=message.author.display_name)
               #embed.set_thumbnail(url=message.author.avatar_url)
               #embed.set_footer(text=footer)
               #embed.timestamp = message.created_at
               ##await user.send(content=self._rot13(message.clean_content))
               #try:
               #    post = await ctx.send(embed=embed)
               #except (discord.Forbidden, discord.HTTPException):
               #    await ctx.send(content=error("This is a public location and I do not have the ability to post an embed!"))
               #    return

               #self.embed_cache.append(int(message.id))

               #settings = await self.config.guild(message.guild).all()
               #try:
               #    await post.add_reaction(settings["react"])
               #except (discord.NotFound, discord.Forbidden, discord.HTTPException):
               #    pass
        else:
            # private location: only reply with text
            await ctx.send(content=self._rot13(text))

    @commands.group()
    @checks.mod_or_permissions(manage_guild=True)
    async def rot13set(self, ctx):
        """ROT-13 module settings."""
        pass

    @rot13set.command()
    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def dm_rot13(self, ctx, value : bool = None):
        """Whether to automatically DM ROT-13'd text when a user reacts.
        
        Omit the value to toggle."""
        if value is None:
            value = not await self.config.guild(ctx.guild).on_react_deocde_dm()
        await self.config.guild(ctx.guild).on_react_decode_dm.set(value)
        await ctx.send(info("Set **DM ROT-13** setting for this server to: `{}`".format(value)))

    @rot13set.command()
    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def auto_react_match_text(self, ctx, match_text : str = ""):
        """Text to check for to automatically react, to allow users to one-click decode."""
        if "@" in match_text:
            await ctx.send(error("You cannot use that match text."))
            return

        await self.config.guild(ctx.guild).auto_react_to.set(match_text)
        if match_text:
            await ctx.send(info("If new user messages on this server match `{}`, I will add a reaction automatically.".format(match_text)))
        else:
            await ctx.send(info("Disabled automatically reacting on this erver."))

    def _rot13(self, text):
        """Do ROT-13."""
        # obscured links with [TEXT](URL) broken by making them all [TEXT]\(URL)
        return codecs.encode(text.replace("](", "]\\("), "rot_13")

