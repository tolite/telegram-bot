#!/bin/bash

# Telegram机器人管理系统一键部署脚本
# 适用于Linux系统

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # 无颜色

# 检查是否为root用户
if [ "$(id -u)" -ne 0 ]; then
   echo -e "${RED}错误: 请使用root用户运行此脚本${NC}"
   exit 1
fi

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}       Telegram机器人管理系统部署脚本       ${NC}"
echo -e "${GREEN}=============================================${NC}"

# 更新系统
echo -e "${YELLOW}正在更新系统包...${NC}"
apt update && apt upgrade -y

# 安装必要的软件
echo -e "${YELLOW}正在安装必要的软件...${NC}"
apt install -y python3 python3-pip python3-venv git screen nginx

# 创建工作目录
WORK_DIR="/opt/telegram-bot-manager"
echo -e "${YELLOW}正在创建工作目录: ${WORK_DIR}${NC}"
mkdir -p $WORK_DIR
cd $WORK_DIR

# 克隆代码仓库
echo -e "${YELLOW}正在克隆代码仓库...${NC}"
git clone https://github.com/yourusername/telegram-bot-manager.git .

# 创建虚拟环境
echo -e "${YELLOW}正在创建Python虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
echo -e "${YELLOW}正在安装Python依赖...${NC}"
pip3 install -r requirements.txt

# 创建systemd服务
echo -e "${YELLOW}正在创建systemd服务...${NC}"

# Bot服务
cat > /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Bot Manager
After=network.target

[Service]
User=root
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/python3 bot_manager.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Web管理后台服务
cat > /etc/systemd/system/telegram-web.service << EOF
[Unit]
Description=Telegram Bot Web Admin
After=network.target

[Service]
User=root
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/python3 web_admin.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload

# 配置Nginx反向代理
echo -e "${YELLOW}正在配置Nginx反向代理...${NC}"
cat > /etc/nginx/sites-available/telegram-bot << EOF
server {
    listen 80;
    server_name your_domain_or_ip; # 请替换为您的域名或IP地址
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 启用网站配置
ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# 重启Nginx
systemctl restart nginx

# 启动服务
echo -e "${YELLOW}正在启动服务...${NC}"
systemctl start telegram-bot
systemctl start telegram-web

# 启用服务自启动
systemctl enable telegram-bot
systemctl enable telegram-web

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}         部署完成！请访问以下地址         ${NC}"
echo -e "${GREEN}         http://your_domain_or_ip          ${NC}"
echo -e "${GREEN}         默认用户名: admin                 ${NC}"
echo -e "${GREEN}         默认密码: password                ${NC}"
echo -e "${GREEN}=============================================${NC}"
echo -e "${YELLOW}注意: 请立即修改默认密码以保证系统安全！${NC}"
echo -e "${YELLOW}使用以下命令查看服务状态:${NC}"
echo -e "${YELLOW}systemctl status telegram-bot${NC}"
echo -e "${YELLOW}systemctl status telegram-web${NC}"    