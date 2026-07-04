#!/usr/bin/env bash
# Instala a Miki como serviço 24/7 em Ubuntu/Debian (Oracle Cloud, VPS, Raspberry Pi...)
# Uso: bash deploy/setup.sh
set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOT_USER="$(whoami)"

echo "==> Instalando dependências do sistema (python3, ffmpeg)..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv ffmpeg

# Máquinas com pouca RAM (ex: VM.Standard.E2.1.Micro da Oracle, 1GB) ganham 1GB de swap
if [ "$(free -m | awk '/^Mem:/{print $2}')" -lt 1500 ] && [ ! -f /swapfile ]; then
    echo "==> Pouca RAM detectada, criando 1GB de swap..."
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
fi

echo "==> Criando ambiente virtual e instalando dependências Python..."
python3 -m venv "$BOT_DIR/.venv"
"$BOT_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$BOT_DIR/.venv/bin/pip" install --quiet -r "$BOT_DIR/requirements.txt"

if [ ! -f "$BOT_DIR/.env" ]; then
    echo
    echo "Pegue o token em https://discord.com/developers/applications (Bot -> Reset Token)"
    read -rp "Cole o token do bot (DISCORD_TOKEN): " TOKEN
    echo "DISCORD_TOKEN=$TOKEN" > "$BOT_DIR/.env"
    chmod 600 "$BOT_DIR/.env"
fi

echo "==> Instalando serviço systemd..."
sed -e "s|{{USER}}|$BOT_USER|g" -e "s|{{DIR}}|$BOT_DIR|g" \
    "$BOT_DIR/deploy/miki.service" | sudo tee /etc/systemd/system/miki.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now miki

echo
echo "✅ Miki instalada e rodando 24/7!"
echo "   Ver status:    systemctl status miki"
echo "   Ver logs:      journalctl -u miki -f"
echo "   Reiniciar:     sudo systemctl restart miki"
echo "   Atualizar bot: git pull && sudo systemctl restart miki"
