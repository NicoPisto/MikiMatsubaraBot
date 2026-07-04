# Miki Matsubara Bot 🌃🎶

Bot de música para Discord inspirado na rainha do city pop, [Miki Matsubara](https://en.wikipedia.org/wiki/Miki_Matsubara).

Toca músicas do YouTube nos canais de voz, com fila por servidor, loop, volume, embaralhamento e mais — funciona tanto com slash commands (`/play`) quanto com o prefixo clássico (`!play`).

## Comandos

### 🎵 Música

| Comando | O que faz |
|---|---|
| `/play <busca ou link>` (`!p`) | Toca uma música do YouTube |
| `/pause` / `/resume` | Pausa e despausa |
| `/skip` (`!s`) | Pula a música atual |
| `/queue` (`!q`) | Mostra a fila |
| `/nowplaying` (`!np`) | Música tocando agora |
| `/shuffle` | Embaralha a fila |
| `/remove <posição>` | Remove uma música da fila |
| `/loop` | Repete a música atual |
| `/volume <0-100>` | Ajusta o volume |
| `/clear` | Limpa a fila |
| `/stop` | Para tudo e limpa a fila |
| `/join` / `/leave` | Entra e sai do canal de voz |

A Miki sai sozinha do canal de voz depois de 3 minutos sem tocar nada.

### 🛠️ Utilidades

| Comando | O que faz |
|---|---|
| `/ping` | Latência do bot |
| `/avatar [@membro]` | Avatar de alguém |
| `/userinfo [@membro]` | Infos de um membro |
| `/serverinfo` | Infos do servidor |
| `/sobre` | Sobre a Miki |
| `/help` | Lista de comandos |

## Como rodar

### Pré-requisitos

- Python 3.10 ou superior
- [FFmpeg](https://ffmpeg.org/download.html) instalado e disponível no PATH
  - Windows: baixe e adicione a pasta `bin` ao PATH, ou `winget install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`

### Configuração do bot no Discord

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications)
2. Na sua aplicação → **Bot**, clique em **Reset Token** e copie o novo token
3. Ainda em **Bot**, ative o **Message Content Intent** (necessário para os comandos com `!`)
4. Em **OAuth2 → URL Generator**, marque os escopos `bot` e `applications.commands`, e as permissões de enviar mensagens e conectar/falar em canais de voz. Use a URL gerada para convidar o bot.

### Instalação

```bash
git clone https://github.com/NicoPisto/MikiMatsubaraBot.git
cd MikiMatsubaraBot

# (opcional, mas recomendado) ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Crie o arquivo `.env` a partir do exemplo e cole o seu token:

```bash
cp .env.example .env
# edite o .env e coloque o token no lugar indicado
```

⚠️ **Nunca commite o arquivo `.env` nem coloque o token no código!** O `.gitignore` já protege o `.env`.

### Rodando

```bash
python main.py
```

Os slash commands podem levar alguns minutos para aparecer no Discord na primeira vez.

## Estrutura do projeto

```
main.py           # Inicialização do bot
cogs/
  music.py        # Comandos de música (yt-dlp + FFmpeg)
  general.py      # Help, ping, infos e utilidades
```
