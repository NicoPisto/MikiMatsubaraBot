from discord.ext import commands

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
Comandos da Miki!:
!help - Mostra essa lista de comandos
!p <keywords> - Procura a música no YOUTUBE e toca. Também da resume
!q - Mostra a fila de músicas atual
!skip - Pula a música atual
!clear - Limpa a lista (inclusive a música atual)
!leave - Vaza do canal
!pause - Pausa a música
!resume - Despausa a música
```
"""
        self.text_channel_list = []


    @commands.command(name="help", help="Mostra todos os comandos do bot")
    async def help(self, ctx):
        await ctx.send(self.help_message)

    async def send_to_all(self, msg):
        for text_channel in self.text_channel_list:
            await text_channel.send(msg)