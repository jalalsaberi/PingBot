#!/bin/bash
# Compatible with Ubuntu ≥ 18 || Debian ≥ 10

magenta="\e[35m"
b_yellow="\e[93m"
cyan="\e[36m"
red="\e[31m"
green="\e[32m"
endl="\e[0m"

uninstall() {
    if [ -f "/etc/systemd/system/pingbot.service" ]; then
        systemctl stop pingbot.service
        systemctl disable pingbot.service
        rm -f /etc/systemd/system/pingbot.service
        rm -rf $HOME/.pingbot
        systemctl daemon-reload
    fi
}

install() {
    apt update -y
    apt install python3 python3-pip -y
    python_path=$(which python3)
    pip3 install python-telegram-bot==13.1 jdatetime pytz schedule pycountry
    if [ -f "/etc/systemd/system/pingbot.service" ]; then
        uninstall
    fi
    mkdir $HOME/.pingbot
    # curl -4 https://raw.githubusercontent.com/jalalsaberi/TLG-ID-BOT/main/tlgidbot.py > $HOME/.pingbot/pingbot.py
    cp $HOME/pingbot.py $HOME/.pingbot/pingbot.py
    cat > "$HOME/.pingbot/conf.json" <<EOF
{
    "user_id": 0,
    "bot_token": "",
    "servers": [],
    "ccode": "",
    "node": ""
} 
EOF
    chmod +x -R $HOME/.pingbot
    clear
    echo -en "${magenta}Enter your Telegram Account User ID: ${endl}" && read user_id
    sed -i 's/"user_id": 0/"user_id": "'"$user_id"'"/' $HOME/.pingbot/conf.json
    echo -en "${magenta}Enter your Telegram Bot Token: ${endl}" && read token
    sed -i 's/"bot_token": ""/"bot_token": "'"$token"'"/' $HOME/.pingbot/conf.json
    echo -e "${green}Format: ISO 3166-1 alpha-2 codes${endl}"
    echo -en "${magenta}Enter your Two Letter Country Code: ${endl}" && read ccode
    sed -i 's/"ccode": ""/"ccode": "'"$ccode"'"/' $HOME/.pingbot/conf.json
    echo -e "${green}Available Nodes: br,bg,hr,cz,fi,fr,de,hk,in,ir,il,it,jp,kz,lt,md,nl,pl,pt,ru,rs,es,ch,tr,ae,uk,ua,us${endl}"
    echo -en "${magenta}Enter your Node Country Code: ${endl}" && read node
    sed -i 's/"node": ""/"node": "'"$node"'"/' $HOME/.pingbot/conf.json
    echo -en "${magenta}Enter your First Server IP: ${endl}" && read serverip
    sed -i 's/"servers": \[\]/"servers": \["'"$serverip"'"\]/' $HOME/.pingbot/conf.json
    echo -en "${red}!!! Start your Bot in Telegram then press Enter here !!!${endl}" && read delay
    cat > "/etc/systemd/system/pingbot.service" <<EOF
[Unit]
Description=Ping Bot

[Service]
ExecStart=$python_path $HOME/.pingbot/pingbot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable pingbot.service > /dev/null
    systemctl start pingbot.service > /dev/null
    systemctl status pingbot.service
    (crontab -l; echo "0 * * * * systemctl restart pingbot.service") | crontab -
}

main() {
    clear
    echo -e "${b_yellow}Ping Bot${endl}\n"
    echo -e "${cyan}1. Install${endl}\n${cyan}2. Uninstall${endl}\n${cyan}0. Exit${endl}\n"
    echo -en "${magenta}Choose: ${endl}" && read option
    if [[ $option == 1 ]]; then
        install
        echo -e "\n${green}Ping Bot Installed Successfully${endl}\n"
    elif [[ $option == 2 ]]; then
        uninstall
        echo -e "\n${green}Ping Bot Uninstalled Successfully${endl}\n"
    elif [[ $option == 0 ]]; then
        exit 0
    else
        echo -en "\n${red}Wrong Option!!! Choose again.${endl}\n"
        sleep 1.5
        main
    fi
}

main