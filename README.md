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

## Rodando 24/7 (Oracle Cloud, VPS, Raspberry Pi)

Em qualquer máquina Ubuntu/Debian, o script de deploy instala tudo e deixa a Miki rodando como serviço do systemd (reinicia sozinha se crashar ou se a máquina reiniciar):

```bash
git clone https://github.com/NicoPisto/MikiMatsubaraBot.git
cd MikiMatsubaraBot
bash deploy/setup.sh   # pede o token e configura tudo
```

Comandos úteis depois de instalado:

```bash
systemctl status miki                      # ver se está rodando
journalctl -u miki -f                      # logs ao vivo
sudo systemctl restart miki                # reiniciar
git pull && sudo systemctl restart miki    # atualizar o bot
```

## YouTube pedindo login? ("Sign in to confirm you're not a bot")

O YouTube bloqueia requisições vindas de IPs de datacenter (Oracle Cloud, AWS, etc.). Tem duas formas de resolver — a primeira não precisa de conta nenhuma:

### Opção A (recomendada): provedor de PO Token, sem conta

Roda um pequeno serviço local ([bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider)) que gera os tokens de verificação que o YouTube exige. Não usa cookies nem login de ninguém:

```bash
cd ~/MikiMatsubaraBot
bash deploy/setup-potoken.sh
```

O script instala Docker (se precisar), sobe o provedor num container e atualiza o yt-dlp. O yt-dlp detecta o provedor sozinho a partir daí — nada a configurar no código.

### Opção B: cookies de uma conta logada

Se a opção A não resolver, o fallback é dar à Miki os cookies de uma conta do YouTube:

1. **Crie uma conta Google descartável** só para isso (não use sua conta pessoal — contas usadas a partir de servidores podem ser sinalizadas pelo Google)
2. No navegador, logado nessa conta, abra o [youtube.com](https://youtube.com) e toque qualquer vídeo
3. Instale a extensão [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) (Chrome) e, ainda na aba do YouTube, clique na extensão → **Export** → salva o `cookies.txt`
4. Envie o arquivo para a pasta do bot no servidor:
   ```bash
   scp -i sua-chave.key cookies.txt ubuntu@IP_DO_SERVIDOR:~/MikiMatsubaraBot/cookies.txt
   ```
5. Reinicie a Miki: `sudo systemctl restart miki`

A Miki detecta o `cookies.txt` automaticamente. O `.gitignore` já impede que ele vá parar no GitHub — **nunca compartilhe esse arquivo**, ele dá acesso à conta.

### Dica geral

Se as músicas pararem de tocar no futuro, o primeiro passo é sempre atualizar o yt-dlp (o YouTube muda o site o tempo todo):

```bash
cd ~/MikiMatsubaraBot && .venv/bin/pip install -U yt-dlp && sudo systemctl restart miki
```

## Estrutura do projeto

```
main.py           # Inicialização do bot
cogs/
  music.py        # Comandos de música (yt-dlp + FFmpeg)
  general.py      # Help, ping, infos e utilidades
```
