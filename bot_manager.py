import os
import json
import logging
import asyncio
import datetime
from typing import Dict, List, Optional, Union
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据存储路径
DATA_DIR = "data"
BOTS_FILE = os.path.join(DATA_DIR, "bots.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
KEYWORDS_FILE = os.path.join(DATA_DIR, "keywords.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")
SCHEDULED_TASKS_FILE = os.path.join(DATA_DIR, "scheduled_tasks.json")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 状态机
class AdminStates(StatesGroup):
    ADD_BOT = State()
    DELETE_BOT = State()
    ADD_KEYWORD = State()
    DELETE_KEYWORD = State()
    ADD_DEVICE = State()
    DELETE_DEVICE = State()
    SCHEDULE_MESSAGE = State()
    FORWARD_TO_GROUP = State()

class TelegramBotManager:
    def __init__(self):
        self.bots: Dict[str, Bot] = {}
        self.dispatchers: Dict[str, Dispatcher] = {}
        self.users: Dict[int, Dict] = self._load_data(USERS_FILE)
        self.keywords: Dict[str, List[str]] = self._load_data(KEYWORDS_FILE)
        self.messages: Dict[str, List[Dict]] = self._load_data(MESSAGES_FILE)
        self.scheduled_tasks: List[Dict] = self._load_data(SCHEDULED_TASKS_FILE)
        self.storage = MemoryStorage()
        self.scheduler = AsyncIOScheduler()
        self.admins = [123456789]  # 替换为实际管理员ID
        
        # 加载已保存的机器人
        self._load_bots()
        
        # 启动定时任务
        self._start_scheduler()
    
    def _load_data(self, file_path: str) -> Union[Dict, List]:
        """从JSON文件加载数据"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载数据文件 {file_path} 失败: {e}")
        return {} if file_path in [USERS_FILE, KEYWORDS_FILE, MESSAGES_FILE] else []
    
    def _save_data(self, file_path: str, data: Union[Dict, List]) -> None:
        """保存数据到JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据到文件 {file_path} 失败: {e}")
    
    def _load_bots(self) -> None:
        """加载已保存的机器人"""
        bots_data = self._load_data(BOTS_FILE)
        for bot_token, bot_info in bots_data.items():
            try:
                bot = Bot(token=bot_token)
                dp = Dispatcher(bot, storage=self.storage)
                self._setup_dispatcher(dp, bot_token)
                self.bots[bot_token] = bot
                self.dispatchers[bot_token] = dp
                logger.info(f"已加载机器人: {bot_info['name']}")
            except Exception as e:
                logger.error(f"加载机器人失败 (token: {bot_token}): {e}")
    
    def _setup_dispatcher(self, dp: Dispatcher, bot_token: str) -> None:
        """设置机器人的消息处理器"""
        # 处理普通消息
        @dp.message_handler()
        async def handle_message(message: types.Message):
            await self._process_message(message, bot_token)
        
        # 处理管理员命令
        @dp.message_handler(Command("admin"), user_id=self.admins)
        async def admin_command(message: types.Message):
            await self._handle_admin_command(message, bot_token)
    
    async def _process_message(self, message: types.Message, bot_token: str) -> None:
        """处理接收到的消息"""
        # 记录用户信息
        user_id = message.from_user.id
        if user_id not in self.users:
            self.users[user_id] = {
                "id": user_id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "joined_at": datetime.datetime.now().isoformat()
            }
            self._save_data(USERS_FILE, self.users)
        
        # 检查是否为关键词
        if message.text:
            for keyword, target_groups in self.keywords.items():
                if keyword in message.text:
                    # 处理结算查询关键词
                    if keyword == "结算查询":
                        await self._handle_settlement_query(message, bot_token)
                    else:
                        # 转发消息到指定群组
                        for group_id in target_groups:
                            try:
                                await self.bots[bot_token].forward_message(
                                    chat_id=group_id,
                                    from_chat_id=message.chat.id,
                                    message_id=message.message_id
                                )
                                logger.info(f"已将关键词 '{keyword}' 的消息从 {message.chat.id} 转发到 {group_id}")
                            except Exception as e:
                                logger.error(f"转发消息失败: {e}")
                    break
    
    async def _handle_settlement_query(self, message: types.Message, bot_token: str) -> None:
        """处理结算查询请求"""
        # 这里应实现实际的结算查询逻辑
        # 示例返回一个模拟的结算信息
        response = "您的待结算余额为: ¥1,234.56\n"
        response += "上次结算日期: 2023-05-15\n"
        response += "结算周期: 2023-05-01至2023-05-15"
        
        await message.answer(response)
        logger.info(f"已回复结算查询给用户 {message.from_user.id}")
    
    async def _handle_admin_command(self, message: types.Message, bot_token: str) -> None:
        """处理管理员命令"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["添加机器人", "删除机器人", "添加关键词", "删除关键词", 
                   "添加设备", "删除设备", "定时内容", "转发到群组", "查看统计"]
        keyboard.add(*buttons)
        
        await message.answer("欢迎使用管理系统，请选择操作:", reply_markup=keyboard)
        await AdminStates.ADD_BOT.set()
    
    async def run(self) -> None:
        """运行所有机器人"""
        for bot_token, dp in self.dispatchers.items():
            try:
                executor.start_polling(dp, skip_updates=True)
            except Exception as e:
                logger.error(f"启动机器人失败 (token: {bot_token}): {e}")
    
    def _start_scheduler(self) -> None:
        """启动定时任务调度器"""
        # 加载已保存的定时任务
        for task in self.scheduled_tasks:
            try:
                self.scheduler.add_job(
                    self._send_scheduled_message,
                    'cron',
                    hour=task['hour'],
                    minute=task['minute'],
                    kwargs={
                        'bot_token': task['bot_token'],
                        'chat_id': task['chat_id'],
                        'message': task['message']
                    }
                )
                logger.info(f"已添加定时任务: {task['message'][:20]}...")
            except Exception as e:
                logger.error(f"添加定时任务失败: {e}")
        
        self.scheduler.start()
    
    async def _send_scheduled_message(self, bot_token: str, chat_id: int, message: str) -> None:
        """发送定时消息"""
        if bot_token in self.bots:
            try:
                await self.bots[bot_token].send_message(chat_id, message)
                logger.info(f"已发送定时消息到 {chat_id}: {message[:20]}...")
            except Exception as e:
                logger.error(f"发送定时消息失败: {e}")
        else:
            logger.error(f"发送定时消息失败: 机器人 {bot_token} 不存在")

if __name__ == "__main__":
    manager = TelegramBotManager()
    asyncio.run(manager.run())    