from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import json
import os
import subprocess
import time
import jdatetime
import datetime
import pytz
import pycountry

dirname = os.path.dirname(__file__)
json_conf = os.path.join(dirname, 'conf.json')
url = "https://check-host.net"
color_flag = {
    4: "🟢",
    3: "🟡",
    2: "🟠",
    1: "🔴",
    0: "⚠️"
}
start_cmd_msg = "Welcome to the Ping Bot! 👋\n\nThis bot checks the status of your servers every hour and sends you the results."
ip_cmd_msg = "🪄 Command: /ip\n\n🔧 Usage:\n\n🔸 Add IP: /ip add 127.0.0.1\n🔸 Remove IP: /ip rm 127.0.0.1\n🔸 List Servers IP: /ip list"
cc_cmd_msg = "🪄 Command: /cc\n\n🔧 Usage:\n\n🔸 Change Country: /cc ir"
node_cmd_msg = "🪄 Command: /node\n\n🔧 Usage:\n\n🔸 Change Node: /node ir\n\n🛰 Available Nodes:\n\nbr,bg,hr,cz,fi,fr,de,hk,in,ir,il,it,jp,kz,lt,md,nl,pl,pt,ru,rs,es,ch,tr,ae,uk,ua,us"
res_cmd_msg = "🪄 Command: /res\n\n🔧 Usage:\n\n🔸 Restart Bot: /res"
cmd_msg = "🪄 Bot Commands:\n\n🔸 Show this Message: /cmd\n🔸 Add/Remove/List Servers IP: /ip\n🔸 Ping Servers IP: /ping\n🔸 Change Country: /cc\n🔸 Change Node: /node\n🔸 Restart Bot: /res"

def handle_json(job, key, value):
    with open(json_conf, 'r') as file:
        data = json.load(file)
    if job == "get":
        return data[key]
    else:
        if job == "add":
            data["servers"].append(value)
        elif job == "rm":
            data["servers"].remove(value)
        elif job == "rep":
            data[key] = value
        with open(json_conf, 'w') as file:
            json.dump(data, file, indent=4)

def json_data():
    user_id = int(handle_json("get", "user_id", ""))
    token = handle_json("get", "bot_token", "")
    servers = handle_json("get", "servers", "")
    ccode = handle_json("get", "ccode", "")
    cnode = handle_json("get", "node", "")
    data_dict = {"user_id": user_id,
                 "token": token,
                 "servers": servers,
                 "ccode": ccode,
                 "cnode": cnode
                 }
    return data_dict

def time_calc(ccode):
    try:
        country_timezones = pytz.country_timezones(ccode.upper())
    except:
        country_timezones = None
    if country_timezones and ccode == "ir":
        tz = pytz.timezone(country_timezones[0])
        now = jdatetime.datetime.now(tz=tz)
    elif country_timezones:
        tz = pytz.timezone(country_timezones[0])
        now = datetime.datetime.now(tz=tz)
    else:
        tz = pytz.timezone('UTC')
        now = datetime.datetime.now(tz=tz)
    time_seconds = int(now.timestamp())
    date_str = now.strftime(f'{tz}: %Y/%m/%d %H:%M:%S')
    return int(time_seconds), date_str

def authenticate_user(func):
    def for_function(update: Update, context: CallbackContext):
        user = update.effective_chat.id
        if json_data()["user_id"] == user:
            return func(update, context)
        else:
            pass
    return for_function

def get_nodes(code):
    code = code.lower()
    try:
        response = requests.get(f"{url}/nodes/hosts")
    except:
        time.sleep(20)
        get_nodes(code)
    data = json.loads(response.text)
    country_nodes = []
    location = []
    for node, info in data["nodes"].items():
        if node.startswith(code):
            location = info["location"]
            city = location[2]
            country_nodes.append({"name": city, "node": node})
    if len(location) > 1 and location[1] != "":
        country = location[1]
    else:
        country = False
        country_nodes = False
    return country, country_nodes

def check_host(context: CallbackContext):
    user_id = json_data()["user_id"]
    servers = json_data()["servers"]
    ccode = json_data()["ccode"]
    cnode = json_data()["cnode"]
    selected_node = get_nodes(cnode)
    if (selected_node[0] is not False and selected_node[1] is not False) and (selected_node[0] is not [] and selected_node[1] is not []):
        country = selected_node[0]
        nodes = selected_node[1]
        time_date = time_calc(ccode)[1]
        context.bot.send_message(chat_id=user_id, text=f"🛰 Pinging Started:\n\n🗓 {time_date}")
        for server in servers:
            ping_link = f"{url}/check-ping?host={server}"
            for node in nodes:
                ping_link += f'&node={node["node"]}'
            ping_response = requests.get(ping_link, headers={"Accept": "application/json"})
            time.sleep(20)
            ping_data = json.loads(ping_response.text)
            result_link = f"{url}/check-result/{ping_data['request_id']}"
            result_response = requests.get(result_link, headers={"Accept": "application/json"})
            if result_response.status_code == 200:
                try:
                    stat = []
                    result_data = result_response.json()
                    node_index = 0
                    for pings in result_data.values():
                        successful_pings = 0
                        if pings:
                            for ping_results in pings:
                                for result in ping_results:
                                    if result[0] == "OK":
                                        successful_pings += 1
                            if nodes[node_index]['name'] != "Coventry":
                                stat.append(f"{color_flag[successful_pings]} {nodes[node_index]['name']}: {successful_pings}/4")
                            else:
                                context.bot.send_message(chat_id=user_id, text="🌏 Country Not Found in Checkhost Nodes !!!\n\n⚠️ Change Country Code using /cc Command !!!")
                                break
                        node_index += 1
                    stat_str = ""
                    for l in stat:
                        stat_str += l+"\n"
                    time_date = time_calc(ccode)[1]
                    message = f"🌏 Country: {country}\n\n📡 Server: {server}\n\n{stat_str}\n🗓 {time_date}"
                    context.bot.send_message(chat_id=user_id, text=message)
                except json.decoder.JSONDecodeError as e:
                    context.bot.send_message(chat_id=user_id, text=f"Error decoding JSON: {e}")
                    return
            else:
                context.bot.send_message(chat_id=user_id, text=f"Error: Received status code {result_response.status_code}")
                return
        time_date = time_calc(ccode)[1]
        context.bot.send_message(chat_id=user_id, text=f"🛰 Pinging Finished:\n\n🗓 {time_date}")
    else:
        context.bot.send_message(chat_id=user_id, text="🌏 Country Not Found in Checkhost Nodes !!!\n\n⚠️ Change Country Code using /cc Command !!!")
        return

def ping(update: Update, context: CallbackContext):
    user_id = json_data()["user_id"]
    user = update.effective_chat.id
    if user_id == user:
        check_host(context)
    else:
        pass

@authenticate_user
def start(_, context: CallbackContext):
    user_id = json_data()["user_id"]
    context.bot.send_message(chat_id=user_id, text=start_cmd_msg)

@authenticate_user
def ip(_, context: CallbackContext):
    user_id = json_data()["user_id"]
    servers = json_data()["servers"]
    ccode = json_data()["ccode"]
    if len(context.args) > 0:
        command_args = context.args
        if len(command_args) == 2:
            if command_args[0] == "add":
                handle_json("add", "servers", command_args[1])
                context.bot.send_message(chat_id=user_id, text=f"📡 Server ({command_args[1]}) Added Successfully.")
            elif command_args[0] == "rm":
                handle_json("rm", "servers", command_args[1])
                context.bot.send_message(chat_id=user_id, text=f"📡 Server ({command_args[1]}) Removed Successfully.")
            else:
                context.bot.send_message(chat_id=user_id, text=ip_cmd_msg)
                return
        elif len(command_args) == 1 and command_args[0] == "list":
            sv_list = ""
            count = 1
            for server in servers:
                sv_list += f"{count}. {server}\n"
                count += 1
            time_date = time_calc(ccode)[1]
            context.bot.send_message(chat_id=user_id, text=f"📡 Servers List:\n\n{sv_list}\n🗓 {time_date}")
        else:
            context.bot.send_message(chat_id=user_id, text=ip_cmd_msg)
            return
    else:
        context.bot.send_message(chat_id=user_id, text=ip_cmd_msg)
        return

@authenticate_user
def change_country(_, context: CallbackContext):
    user_id = json_data()["user_id"]
    if len(context.args) > 0:
        command_args = context.args[0].split(' ')
        if len(command_args) == 1:
            if len(command_args[0]) == 2:
                try:
                    country = pycountry.countries.get(alpha_2=command_args[0].upper())
                    if country is not None:
                        handle_json("rep", "ccode", command_args[0])
                        context.bot.send_message(chat_id=user_id, text=f"🌏 Country Successfully Changed to ({country.name}).")
                    else:
                        context.bot.send_message(chat_id=user_id, text="🌏 Country Code Not Found in Time Zones !!!\n\n⚠️ Change Country Code using /cc Command !!!")
                except:
                    context.bot.send_message(chat_id=user_id, text="⚠️ Error Occurred while Processing the Country Code !!!\n\n⚠️ Change Country Code using /cc Command !!!")
            else:
                context.bot.send_message(chat_id=user_id, text=cc_cmd_msg)
                return
        else:
            context.bot.send_message(chat_id=user_id, text=cc_cmd_msg)
            return
    else:
        context.bot.send_message(chat_id=user_id, text=cc_cmd_msg)
        return

@authenticate_user
def change_node(_, context: CallbackContext):
    user_id = json_data()["user_id"]
    if len(context.args) > 0:
        command_args = context.args[0].split(' ')
        if len(command_args) == 1:
            if len(command_args[0]) == 2:
                try:
                    handle_json("rep", "node", command_args[0])
                    context.bot.send_message(chat_id=user_id, text=f"🌏 Node Successfully Changed to ({command_args[0]}).")
                except:
                    context.bot.send_message(chat_id=user_id, text="⚠️ Error Occurred while Processing the Node Country !!!\n\n⚠️ Change Node Country using /node Command !!!")
            else:
                context.bot.send_message(chat_id=user_id, text=node_cmd_msg)
                return
        else:
            context.bot.send_message(chat_id=user_id, text=node_cmd_msg)
            return
    else:
        context.bot.send_message(chat_id=user_id, text=node_cmd_msg)
        return

@authenticate_user
def res_cmd(_, context: CallbackContext):
    user_id = json_data()["user_id"]
    if len(context.args) > 0:
        context.bot.send_message(chat_id=user_id, text=res_cmd_msg)
        return
    else:
        context.bot.send_message(chat_id=user_id, text="🤖 Bot Successfully has Restarted.")
        subprocess.run("systemctl restart pingbot.service", shell=True, text=True)
        return
    
@authenticate_user
def cmd(_, context: CallbackContext):
    user_id = json_data()["user_id"]
    if len(context.args) > 0:
        context.bot.send_message(chat_id=user_id, text=cmd_msg)
        return
    else:
        context.bot.send_message(chat_id=user_id, text=cmd_msg)
        return

def main():
    updater = Updater(json_data()["token"], use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("ip", ip))
    dp.add_handler(CommandHandler("ping", ping))
    dp.add_handler(CommandHandler("cc", change_country))
    dp.add_handler(CommandHandler("node", change_node))
    dp.add_handler(CommandHandler("res", res_cmd))
    dp.add_handler(CommandHandler("cmd", cmd))
    check_host(CallbackContext(dp))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
