#!/bin/bash
set -e

echo "=== 粥粥的 Evoxt VPS 一键配 ==="

# 1. 系统更新 + 基础工具
apt update -y
apt install -y curl unzip ufw

# 2. 防火墙——只放行需要的
ufw default deny incoming
ufw default allow outgoing
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# 3. SSH 加固
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#ChallengeResponseAuthentication.*/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat > ~/.ssh/authorized_keys << 'KEYEOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPGN2MDmjBPO9aWHlK2viqPf2/0vZwakJLze4JDvZhIo 123@DESKTOP-C2GDEMG
KEYEOF
chmod 600 ~/.ssh/authorized_keys
systemctl restart ssh

# 4. Caddy
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" > /etc/apt/sources.list.d/caddy-stable.list
apt update -y
apt install -y caddy

# 5. Caddy 配置——静默反代，不暴露 VPS 信息
cat > /etc/caddy/Caddyfile << 'CADDYEOF'
zhou-and-claude.online {
    encode gzip
    header {
        Server ""
        -Server
    }
    respond "Hello" 200
}
CADDYEOF

systemctl enable caddy
systemctl restart caddy

# 6. 完成
echo "=== 全部完成 ==="
echo "访问 https://zhou-and-claude.online 应该看到 Hello"
echo "SSH 只能用密钥了。bot 永远进不来。"
