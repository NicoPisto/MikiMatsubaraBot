import platform
import time

import discord
from discord.ext import commands

MIKI_PINK = discord.Colour.from_str("#ff6fa5")


class General(commands.Cog):
    """Comandos gerais e utilidades da Miki"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(name="help", aliases=["ajuda"], description="Mostra todos os comandos da Miki")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Comandos da Miki! 🎶",
            description="Funciona com `!comando` ou `/comando`",
            colour=MIKI_PINK,
        )
        embed.add_field(
            name="🎵 Música",
            value=(
                "`/play <busca ou link>` — Toca uma música do YouTube\n"
                "`/pause` / `/resume` — Pausa e despausa\n"
                "`/skip` — Pula a música atual\n"
                "`/queue` — Mostra a fila\n"
                "`/nowplaying` — Música tocando agora\n"
                "`/shuffle` — Embaralha a fila\n"
                "`/remove <posição>` — Remove uma música da fila\n"
                "`/loop` — Repete a música atual\n"
                "`/volume <0-100>` — Ajusta o volume\n"
                "`/clear` — Limpa a fila\n"
                "`/stop` — Para tudo\n"
                "`/join` / `/leave` — Entra e sai do canal de voz"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛠️ Utilidades",
            value=(
                "`/ping` — Latência do bot\n"
                "`/avatar [@membro]` — Mostra o avatar de alguém\n"
                "`/userinfo [@membro]` — Infos de um membro\n"
                "`/serverinfo` — Infos do servidor\n"
                "`/sobre` — Sobre a Miki"
            ),
            inline=False,
        )
        embed.set_footer(text="Miki Matsubara Bot • city pop forever 🌃")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ping", description="Mostra a latência da Miki")
    async def ping(self, ctx: commands.Context):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! 🏓 `{latency_ms}ms`")

    @commands.hybrid_command(name="avatar", description="Mostra o avatar de um membro")
    async def avatar(self, ctx: commands.Context, membro: discord.Member = None):
        membro = membro or ctx.author
        embed = discord.Embed(title=f"Avatar de {membro.display_name}", colour=MIKI_PINK)
        embed.set_image(url=membro.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", description="Mostra informações de um membro")
    async def userinfo(self, ctx: commands.Context, membro: discord.Member = None):
        membro = membro or ctx.author
        embed = discord.Embed(title=f"Sobre {membro.display_name}", colour=MIKI_PINK)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.add_field(name="Usuário", value=str(membro), inline=True)
        embed.add_field(name="ID", value=membro.id, inline=True)
        embed.add_field(
            name="Conta criada em",
            value=discord.utils.format_dt(membro.created_at, style="D"),
            inline=False,
        )
        if membro.joined_at:
            embed.add_field(
                name="Entrou no servidor em",
                value=discord.utils.format_dt(membro.joined_at, style="D"),
                inline=False,
            )
        roles = [role.mention for role in membro.roles[1:]]  # ignora @everyone
        if roles:
            embed.add_field(name="Cargos", value=" ".join(roles[:15]), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", description="Mostra informações do servidor")
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        embed = discord.Embed(title=guild.name, colour=MIKI_PINK)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Membros", value=guild.member_count, inline=True)
        embed.add_field(name="Dono", value=guild.owner.mention if guild.owner else "?", inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        embed.add_field(
            name="Criado em",
            value=discord.utils.format_dt(guild.created_at, style="D"),
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="sobre", aliases=["about"], description="Sobre a Miki")
    async def sobre(self, ctx: commands.Context):
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        embed = discord.Embed(
            title="Miki Matsubara Bot 🌃",
            description=(
                "Bot de música inspirado na rainha do city pop, "
                "[Miki Matsubara](https://en.wikipedia.org/wiki/Miki_Matsubara) 💖"
            ),
            colour=MIKI_PINK,
        )
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}min", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
