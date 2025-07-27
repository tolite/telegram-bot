from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
import os
import json
import logging
from datetime import datetime

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
DEVICES_FILE = os.path.join(DATA_DIR, "devices.json")
SCHEDULED_TASKS_FILE = os.path.join(DATA_DIR, "scheduled_tasks.json")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # 请更换为安全的密钥

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# 简单用户类
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# 数据加载和保存函数
def load_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据文件 {file_path} 失败: {e}")
    return {} if file_path in [BOTS_FILE, USERS_FILE, KEYWORDS_FILE, MESSAGES_FILE, DEVICES_FILE] else []

def save_data(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存数据到文件 {file_path} 失败: {e}")

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 这里应该实现实际的身份验证逻辑
        # 示例中使用硬编码的用户名和密码
        if username == 'admin' and password == 'password':  # 请更换为安全的凭证
            user = User(1)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 首页
@app.route('/')
@login_required
def index():
    bots = load_data(BOTS_FILE)
    users = load_data(USERS_FILE)
    devices = load_data(DEVICES_FILE)
    scheduled_tasks = load_data(SCHEDULED_TASKS_FILE)
    
    return render_template('index.html', 
                           bots=bots, 
                           user_count=len(users), 
                           device_count=len(devices),
                           task_count=len(scheduled_tasks))

# 机器人管理
@app.route('/bots')
@login_required
def bots():
    bots_data = load_data(BOTS_FILE)
    return render_template('bots.html', bots=bots_data)

@app.route('/bots/add', methods=['GET', 'POST'])
@login_required
def add_bot():
    if request.method == 'POST':
        bot_token = request.form.get('token')
        bot_name = request.form.get('name')
        
        bots_data = load_data(BOTS_FILE)
        bots_data[bot_token] = {
            "name": bot_name,
            "added_at": datetime.now().isoformat()
        }
        
        save_data(BOTS_FILE, bots_data)
        return redirect(url_for('bots'))
    
    return render_template('add_bot.html')

@app.route('/bots/delete/<bot_token>', methods=['POST'])
@login_required
def delete_bot(bot_token):
    bots_data = load_data(BOTS_FILE)
    if bot_token in bots_data:
        del bots_data[bot_token]
        save_data(BOTS_FILE, bots_data)
    return redirect(url_for('bots'))

# 用户管理
@app.route('/users')
@login_required
def users():
    users_data = load_data(USERS_FILE)
    return render_template('users.html', users=users_data)

# 关键词管理
@app.route('/keywords')
@login_required
def keywords():
    keywords_data = load_data(KEYWORDS_FILE)
    return render_template('keywords.html', keywords=keywords_data)

@app.route('/keywords/add', methods=['GET', 'POST'])
@login_required
def add_keyword():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        target_groups = request.form.get('target_groups').split(',')
        
        keywords_data = load_data(KEYWORDS_FILE)
        keywords_data[keyword] = [group.strip() for group in target_groups]
        
        save_data(KEYWORDS_FILE, keywords_data)
        return redirect(url_for('keywords'))
    
    return render_template('add_keyword.html')

@app.route('/keywords/delete/<keyword>', methods=['POST'])
@login_required
def delete_keyword(keyword):
    keywords_data = load_data(KEYWORDS_FILE)
    if keyword in keywords_data:
        del keywords_data[keyword]
        save_data(KEYWORDS_FILE, keywords_data)
    return redirect(url_for('keywords'))

# 设备管理
@app.route('/devices')
@login_required
def devices():
    devices_data = load_data(DEVICES_FILE)
    return render_template('devices.html', devices=devices_data)

@app.route('/devices/add', methods=['GET', 'POST'])
@login_required
def add_device():
    if request.method == 'POST':
        device_id = request.form.get('device_id')
        device_name = request.form.get('name')
        description = request.form.get('description')
        
        devices_data = load_data(DEVICES_FILE)
        devices_data[device_id] = {
            "name": device_name,
            "description": description,
            "added_at": datetime.now().isoformat()
        }
        
        save_data(DEVICES_FILE, devices_data)
        return redirect(url_for('devices'))
    
    return render_template('add_device.html')

@app.route('/devices/delete/<device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    devices_data = load_data(DEVICES_FILE)
    if device_id in devices_data:
        del devices_data[device_id]
        save_data(DEVICES_FILE, devices_data)
    return redirect(url_for('devices'))

# 定时任务管理
@app.route('/tasks')
@login_required
def tasks():
    tasks_data = load_data(SCHEDULED_TASKS_FILE)
    return render_template('tasks.html', tasks=tasks_data)

@app.route('/tasks/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        bot_token = request.form.get('bot_token')
        chat_id = request.form.get('chat_id')
        message = request.form.get('message')
        hour = request.form.get('hour')
        minute = request.form.get('minute')
        
        tasks_data = load_data(SCHEDULED_TASKS_FILE)
        new_task = {
            "bot_token": bot_token,
            "chat_id": chat_id,
            "message": message,
            "hour": hour,
            "minute": minute,
            "created_at": datetime.now().isoformat()
        }
        
        tasks_data.append(new_task)
        save_data(SCHEDULED_TASKS_FILE, tasks_data)
        return redirect(url_for('tasks'))
    
    bots_data = load_data(BOTS_FILE)
    return render_template('add_task.html', bots=bots_data)

@app.route('/tasks/delete/<int:task_index>', methods=['POST'])
@login_required
def delete_task(task_index):
    tasks_data = load_data(SCHEDULED_TASKS_FILE)
    if 0 <= task_index < len(tasks_data):
        del tasks_data[task_index]
        save_data(SCHEDULED_TASKS_FILE, tasks_data)
    return redirect(url_for('tasks'))

# API 接口
@app.route('/api/stats')
@login_required
def api_stats():
    bots = load_data(BOTS_FILE)
    users = load_data(USERS_FILE)
    devices = load_data(DEVICES_FILE)
    tasks = load_data(SCHEDULED_TASKS_FILE)
    
    return jsonify({
        "bot_count": len(bots),
        "user_count": len(users),
        "device_count": len(devices),
        "task_count": len(tasks)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)    