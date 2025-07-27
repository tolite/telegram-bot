import argparse
from modules import bot_core, web_admin

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Telegram Bot System')
    parser.add_argument('--config', default='config.ini', help='配置文件路径')
    parser.add_argument('--run-bot', action='store_true', help='运行机器人')
    parser.add_argument('--run-web', action='store_true', help='运行 Web 后台')
    parser.add_argument('--all', action='store_true', help='同时运行机器人和 Web 后台')
    args = parser.parse_args()

    if args.run_bot or args.all:
        bot_core.run_bot(args.config)
    if args.run_web or args.all:
        web_admin.run_web(args.config)
