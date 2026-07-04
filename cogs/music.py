import asyncio
import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import discord
import yt_dlp
from discord.ext import commands

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "skip_download": True,
    # Necessário para o yt-dlp resolver as assinaturas do YouTube (via Deno) e
    # tocar mesmo em IPs de datacenter, junto com o provedor de PO Token
    # (deploy/setup-potoken.sh). Ver README.
    "remote_components": ["ejs:github"],
}

# O YouTube bloqueia IPs de datacenter (Oracle, AWS...) com "Sign in to
# confirm you're not a bot". Exporte os cookies de uma conta logada para
# um cookies.txt na raiz do projeto que a Miki passa a usá-los (ver README).
COOKIES_FILE = Path(__file__).resolve().parent.parent / "cookies.txt"
if COOKIES_FILE.exists():
    YTDL_OPTIONS["cookiefile"] = str(COOKIES_FILE)

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

IDLE_TIMEOUT = 180  # segundos sem tocar nada antes da Miki vazar sozinha

MIKI_PINK = discord.Colour.from_str("#ff6fa5")


def format_duration(seconds) -> str:
    if not seconds:
        return "ao vivo"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


@dataclass
class Song:
    title: str
    webpage_url: str
    duration: int | None
    thumbnail: str | None
    uploader: str | None
    requester: discord.abc.User

    def embed_line(self) -> str:
        return f"[{self.title}]({self.webpage_url}) `[{format_duration(self.duration)}]`"


@dataclass
class GuildState:
    queue: deque[Song] = field(default_factory=deque)
    current: Song | None = None
    volume: float = 0.5
    loop: bool = False
    channel: discord.abc.Messageable | None = None
    idle_task: asyncio.Task | None = None


class Music(commands.Cog):
    """Comandos de música da Miki 🎶"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states: dict[int, GuildState] = {}

    def get_state(self, guild: discord.Guild) -> GuildState:
        if guild.id not in self.states:
            self.states[guild.id] = GuildState()
        return self.states[guild.id]

    # ------------------------------------------------------------------ #
    # Busca / extração (roda em thread para não travar o bot)
    # ------------------------------------------------------------------ #

    async def search_song(self, query: str, requester: discord.abc.User) -> Song | None:
        def _extract():
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                if info and "entries" in info:
                    entries = info["entries"]
                    if not entries:
                        return None
                    info = entries[0]
                return info

        try:
            info = await asyncio.to_thread(_extract)
        except yt_dlp.utils.DownloadError:
            return None

        if info is None:
            return None

        return Song(
            title=info.get("title", "???"),
            webpage_url=info.get("webpage_url") or info.get("url", ""),
            duration=info.get("duration"),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("uploader"),
            requester=requester,
        )

    async def get_stream_url(self, song: Song) -> str | None:
        """Extrai a URL do stream na hora de tocar (URLs do YouTube expiram)."""

        def _extract():
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(song.webpage_url, download=False)
                return info.get("url") if info else None

        try:
            return await asyncio.to_thread(_extract)
        except yt_dlp.utils.DownloadError:
            return None

    # ------------------------------------------------------------------ #
    # Player
    # ------------------------------------------------------------------ #

    async def play_next(self, guild: discord.Guild):
        state = self.get_state(guild)
        voice = guild.voice_client

        if voice is None or not voice.is_connected():
            return

        if state.loop and state.current is not None:
            song = state.current
        elif state.queue:
            song = state.queue.popleft()
        else:
            state.current = None
            self.start_idle_timer(guild)
            return

        self.cancel_idle_timer(state)
        stream_url = await self.get_stream_url(song)

        if stream_url is None:
            if state.channel:
                await state.channel.send(f"Não consegui tocar **{song.title}**, pulando... 😥")
            await self.play_next(guild)
            return

        state.current = song
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
            volume=state.volume,
        )

        def after_playing(error):
            if error:
                print(f"Erro no player: {error!r}")
            fut = asyncio.run_coroutine_threadsafe(self.play_next(guild), self.bot.loop)
            try:
                fut.result()
            except Exception as exc:
                print(f"Erro ao tocar a próxima: {exc!r}")

        voice.play(source, after=after_playing)

        if state.channel and not state.loop:
            embed = discord.Embed(
                title="Tocando agora 🎶",
                description=song.embed_line(),
                colour=MIKI_PINK,
            )
            if song.thumbnail:
                embed.set_thumbnail(url=song.thumbnail)
            if song.uploader:
                embed.add_field(name="Canal", value=song.uploader, inline=True)
            embed.add_field(name="Pedida por", value=song.requester.mention, inline=True)
            await state.channel.send(embed=embed)

    # ------------------------------------------------------------------ #
    # Auto-desconectar quando ficar ociosa
    # ------------------------------------------------------------------ #

    def start_idle_timer(self, guild: discord.Guild):
        state = self.get_state(guild)
        self.cancel_idle_timer(state)

        async def idle_disconnect():
            await asyncio.sleep(IDLE_TIMEOUT)
            voice = guild.voice_client
            if voice and voice.is_connected() and not voice.is_playing():
                await voice.disconnect()
                if state.channel:
                    await state.channel.send(
                        "Fiquei sozinha muito tempo, fui embora... じゃあね! 👋"
                    )

        state.idle_task = self.bot.loop.create_task(idle_disconnect())

    @staticmethod
    def cancel_idle_timer(state: GuildState):
        if state.idle_task and not state.idle_task.done():
            state.idle_task.cancel()
        state.idle_task = None

    # ------------------------------------------------------------------ #
    # Checks / helpers
    # ------------------------------------------------------------------ #

    async def ensure_voice(self, ctx: commands.Context) -> bool:
        """Garante que o autor está num canal de voz e conecta a Miki nele."""
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("Entre em um canal de voz primeiro, baka! 😤")
            return False

        channel = ctx.author.voice.channel
        voice = ctx.voice_client

        if voice is None or not voice.is_connected():
            await channel.connect()
        elif voice.channel != channel:
            await voice.move_to(channel)

        return True

    # ------------------------------------------------------------------ #
    # Comandos
    # ------------------------------------------------------------------ #

    @commands.hybrid_command(name="play", aliases=["p"], description="Toca uma música do YouTube (busca ou link)")
    async def play(self, ctx: commands.Context, *, busca: str):
        if not await self.ensure_voice(ctx):
            return

        state = self.get_state(ctx.guild)
        state.channel = ctx.channel

        async with ctx.typing():
            song = await self.search_song(busca, ctx.author)

        if song is None:
            await ctx.send("Não achei essa música... tenta outra busca! 🔍")
            return

        state.queue.append(song)

        voice = ctx.voice_client
        if voice.is_playing() or voice.is_paused():
            embed = discord.Embed(
                title="Adicionada à fila ✅",
                description=f"{song.embed_line()}\nPosição na fila: **{len(state.queue)}**",
                colour=MIKI_PINK,
            )
            await ctx.send(embed=embed)
        else:
            if ctx.interaction:
                await ctx.send(f"🎶 Procurando **{song.title}**...")
            await self.play_next(ctx.guild)

    @commands.hybrid_command(name="pause", description="Pausa a música atual")
    async def pause(self, ctx: commands.Context):
        voice = ctx.voice_client
        if voice and voice.is_playing():
            voice.pause()
            await ctx.send("Pausado ⏸️")
        else:
            await ctx.send("Não tem nada tocando agora.")

    @commands.hybrid_command(name="resume", aliases=["r"], description="Despausa a música")
    async def resume(self, ctx: commands.Context):
        voice = ctx.voice_client
        if voice and voice.is_paused():
            voice.resume()
            await ctx.send("Voltando a tocar ▶️")
        else:
            await ctx.send("Não tem nada pausado.")

    @commands.hybrid_command(name="skip", aliases=["s"], description="Pula a música atual")
    async def skip(self, ctx: commands.Context):
        voice = ctx.voice_client
        if voice and (voice.is_playing() or voice.is_paused()):
            state = self.get_state(ctx.guild)
            state.loop = False  # pular desliga o loop, senão a música volta
            voice.stop()  # o callback "after" já chama a próxima
            await ctx.send("Pulei! ⏭️")
        else:
            await ctx.send("Não tem nada tocando pra pular.")

    @commands.hybrid_command(name="queue", aliases=["q", "fila"], description="Mostra a fila de músicas")
    async def queue(self, ctx: commands.Context):
        state = self.get_state(ctx.guild)

        if state.current is None and not state.queue:
            await ctx.send("A fila está vazia! Usa `/play` pra adicionar algo 🎵")
            return

        embed = discord.Embed(title="Fila da Miki 🎶", colour=MIKI_PINK)

        if state.current:
            loop_icon = " 🔁" if state.loop else ""
            embed.add_field(
                name=f"Tocando agora{loop_icon}",
                value=state.current.embed_line(),
                inline=False,
            )

        if state.queue:
            lines = [
                f"`{i}.` {song.embed_line()}"
                for i, song in enumerate(list(state.queue)[:10], start=1)
            ]
            if len(state.queue) > 10:
                lines.append(f"...e mais **{len(state.queue) - 10}** música(s)")
            embed.add_field(name="Próximas", value="\n".join(lines), inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="Mostra a música que está tocando")
    async def nowplaying(self, ctx: commands.Context):
        state = self.get_state(ctx.guild)
        if state.current is None:
            await ctx.send("Não tem nada tocando agora.")
            return

        embed = discord.Embed(
            title="Tocando agora 🎶",
            description=state.current.embed_line(),
            colour=MIKI_PINK,
        )
        if state.current.thumbnail:
            embed.set_thumbnail(url=state.current.thumbnail)
        embed.add_field(name="Pedida por", value=state.current.requester.mention)
        if state.loop:
            embed.set_footer(text="Loop ativado 🔁")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shuffle", aliases=["misturar"], description="Embaralha a fila")
    async def shuffle(self, ctx: commands.Context):
        state = self.get_state(ctx.guild)
        if len(state.queue) < 2:
            await ctx.send("Precisa de pelo menos 2 músicas na fila pra embaralhar.")
            return
        random.shuffle(state.queue)
        await ctx.send("Fila embaralhada! 🔀")

    @commands.hybrid_command(name="remove", description="Remove uma música da fila pela posição")
    async def remove(self, ctx: commands.Context, posicao: int):
        state = self.get_state(ctx.guild)
        if posicao < 1 or posicao > len(state.queue):
            await ctx.send(f"Posição inválida! A fila tem {len(state.queue)} música(s).")
            return
        removed = state.queue[posicao - 1]
        del state.queue[posicao - 1]
        await ctx.send(f"Removi **{removed.title}** da fila 🗑️")

    @commands.hybrid_command(name="loop", description="Liga/desliga o loop da música atual")
    async def loop(self, ctx: commands.Context):
        state = self.get_state(ctx.guild)
        if state.current is None:
            await ctx.send("Não tem nada tocando pra deixar em loop.")
            return
        state.loop = not state.loop
        if state.loop:
            await ctx.send(f"Loop ativado pra **{state.current.title}** 🔁")
        else:
            await ctx.send("Loop desativado ➡️")

    @commands.hybrid_command(name="volume", aliases=["v"], description="Ajusta o volume (0 a 100)")
    async def volume(self, ctx: commands.Context, valor: commands.Range[int, 0, 100]):
        state = self.get_state(ctx.guild)
        state.volume = valor / 100
        voice = ctx.voice_client
        if voice and voice.source and isinstance(voice.source, discord.PCMVolumeTransformer):
            voice.source.volume = state.volume
        await ctx.send(f"Volume ajustado para **{valor}%** 🔊")

    @commands.hybrid_command(name="clear", aliases=["c"], description="Limpa a fila (a música atual continua)")
    async def clear(self, ctx: commands.Context):
        state = self.get_state(ctx.guild)
        state.queue.clear()
        await ctx.send("Fila limpa! 🧹")

    @commands.hybrid_command(name="stop", description="Para tudo e limpa a fila")
    async def stop(self, ctx: commands.Context):
        state = self.get_state(ctx.guild)
        state.queue.clear()
        state.loop = False
        state.current = None
        voice = ctx.voice_client
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()
        await ctx.send("Parei tudo e limpei a fila ⏹️")

    @commands.hybrid_command(name="leave", aliases=["l", "d", "disconnect", "vaza"], description="A Miki sai do canal de voz")
    async def leave(self, ctx: commands.Context):
        voice = ctx.voice_client
        if voice is None or not voice.is_connected():
            await ctx.send("Nem estou em um canal de voz...")
            return

        state = self.get_state(ctx.guild)
        state.queue.clear()
        state.loop = False
        state.current = None
        self.cancel_idle_timer(state)
        await voice.disconnect()
        await ctx.send("Fui! またね 👋")

    @commands.hybrid_command(name="join", aliases=["entra"], description="A Miki entra no seu canal de voz")
    async def join(self, ctx: commands.Context):
        if await self.ensure_voice(ctx):
            await ctx.send(f"Entrei em **{ctx.author.voice.channel.name}** 🎤")

    # ------------------------------------------------------------------ #
    # Tratamento básico de erros dos comandos deste cog
    # ------------------------------------------------------------------ #

    @play.error
    async def play_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Me fala o nome ou link da música! Ex: `!play stay with me`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
