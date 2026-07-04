#!/usr/bin/env bash
# Corrige o erro "Sign in to confirm you're not a bot" do YouTube em IPs de
# datacenter, SEM precisar de conta/cookies: instala o provedor de PO Token
# (bgutil-ytdlp-pot-provider) como container Docker + plugin do yt-dlp.
# Uso: bash deploy/setup-potoken.sh
set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

echo "==> Reiniciando a Miki..."
sudo systemctl restart miki

echo
echo "✅ Pronto! O yt-dlp detecta o provedor automaticamente."
echo "   Ver o provedor:  sudo docker logs bgutil-provider"
echo "   Ver a Miki:      journalctl -u miki -f"
