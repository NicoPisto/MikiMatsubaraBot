#!/usr/bin/env bash
# Corrige o erro "Sign in to confirm you're not a bot" do YouTube em IPs de
# datacenter, SEM precisar de conta/cookies. Três peças são necessárias:
#   1. Um runtime JavaScript (Deno) — resolve as assinaturas/desafios que o
#      YouTube exige antes de liberar a URL de qualquer formato.
#   2. O componente remoto "ejs:github" — o script que o Deno executa para
#      resolver esses desafios (cogs/music.py já pede ele via yt-dlp).
#   3. O provedor de PO Token (bgutil-ytdlp-pot-provider) — gera o token de
#      verificação que alguns clientes do YouTube exigem.
# Uso: bash deploy/setup-potoken.sh
set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v deno > /dev/null; then
    echo "==> Instalando o runtime Deno..."
    if ! command -v unzip > /dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y unzip
    fi
    curl -fsSL https://deno.land/install.sh | sh
    sudo ln -sf "$HOME/.deno/bin/deno" /usr/local/bin/deno
fi
deno --version

if ! command -v docker > /dev/null; then
    echo "==> Instalando Docker..."
    sudo apt-get update -y
    sudo apt-get install -y docker.io
fi

echo "==> Subindo o provedor de PO Token (porta local 4416)..."
sudo docker rm -f bgutil-provider 2> /dev/null || true
sudo docker run -d --name bgutil-provider --restart unless-stopped --init \
    -p 127.0.0.1:4416:4416 brainicism/bgutil-ytdlp-pot-provider

echo "==> Instalando o plugin do yt-dlp e atualizando..."
"$BOT_DIR/.venv/bin/pip" install --quiet -U yt-dlp bgutil-ytdlp-pot-provider

echo "==> Testando a extração de áudio (baixa e cacheia o resolvedor de desafios)..."
"$BOT_DIR/.venv/bin/yt-dlp" --remote-components ejs:github -f bestaudio --skip-download \
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

echo "==> Reiniciando a Miki..."
sudo systemctl restart miki

echo
echo "✅ Pronto! O yt-dlp usa o Deno + o provedor de PO Token automaticamente."
echo "   Ver o provedor:  sudo docker logs bgutil-provider"
echo "   Ver a Miki:      journalctl -u miki -f"
