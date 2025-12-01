#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Loong 的 AI Translator - 四层架构实现
1. 数据接口层 (API Layer) - 处理外部服务的接口调用
2. 功能服务层 (Service Layer) - 实现核心功能的抽象和实例
3. 业务控制层 (Controller Layer) - 处理业务逻辑和消息分发
4. 前端界面层 (UI Layer) - 负责用户界面展示和交互

遵循 Python 之禅:
- 优美胜于丑陋
- 明了胜于晦涩
- 简洁胜于复杂
- 复杂胜于凌乱
- 扁平胜于嵌套
- 间隔胜于紧凑
- 可读性很重要
"""

import sys
import os
import json
import requests
import keyboard
import pyttsx3
import darkdetect
import base64
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QTextEdit, QPushButton, 
                            QComboBox, QDialog, QFormLayout, QLineEdit, 
                            QLabel, QMessageBox, QGroupBox)
from PyQt6.QtCore import (Qt, QSettings, QUrl, QThread, pyqtSignal, QTimer,
                         QSize)
from PyQt6.QtGui import (QTextDocument, QTextCursor, QFontDatabase, QFont, 
                        QPalette, QColor, QIcon)
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

# 常量定义
APP_NAME = "Loong 的 AI Translator"
CONFIG_FILE = "config.enc"
SECRET_SALT = b'win11_translator_salt_2024'
FLOMO_BASE_URL = "https://flomoapp.com/iwh/OTQ5NQ/"

# ========================================
# 1. 数据接口层 (API Layer)
# ========================================

class TranslationAPI:
    """翻译API接口类，负责与外部翻译服务通信"""
    
    def __init__(self, config):
        """初始化翻译API"""
        self.config = config
    
    def translate(self, input_text, target_language):
        """执行翻译请求"""
        api_key = self.config.get("api_key", "")
        api_endpoint = self.config.get("api_endpoint", "https://api.example.com/v1/chat/completions")
        model = self.config.get("model", "gpt-3.5-turbo")
        skip_ssl_check = self.config.get("skip_ssl_check", False)
        
        if not api_key:
            raise ValueError("请先在设置中配置AI API Key")
        
        # 构建请求数据
        headers = {
            "Content-Type": "application/json"
        }
        
        # 处理API密钥，如果已经包含Bearer则直接使用，否则添加Bearer前缀
        if api_key.strip().startswith("Bearer "):
            headers["Authorization"] = api_key.strip()
        else:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 构建提示词，明确要求返回JSON格式
        prompt = f"""
        请将以下文本从源语言翻译成{target_language}。请严格按照以下JSON格式返回结果，不要添加任何额外的文本或解释：
        
        {{
          "translation": "翻译后的文本", 
          "vocabulary": [
            {{"word": "单词或词组", "phonetic": "音标", "meanings": [
              {{"definition": "含义1", "example": "例句1"}},
              {{"definition": "含义2", "example": "例句2"}}
            ]}}
          ]
        }}
        
        原文: {input_text}
        """
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        # 发送请求
        if skip_ssl_check:
            response = requests.post(api_endpoint, headers=headers, json=data, verify=False)
        else:
            response = requests.post(api_endpoint, headers=headers, json=data)
        
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 清理返回内容，移除可能的markdown代码块标记
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        # 解析JSON
        try:
            translation_data = json.loads(content)
        except json.JSONDecodeError as e:
            # 如果JSON解析失败，抛出异常
            raise ValueError(f"JSON解析失败: {str(e)}\n返回内容: {content}")
        
        # 确保返回的数据结构完整
        if "translation" not in translation_data:
            translation_data["translation"] = ""
        if "vocabulary" not in translation_data:
            translation_data["vocabulary"] = []
        
        return translation_data


class FlomoAPI:
    """Flomo API接口类，负责与Flomo服务通信"""
    
    def __init__(self, config):
        """初始化Flomo API"""
        self.config = config
    
    def save_note(self, input_text, translation_text, analysis_text):
        """保存笔记到Flomo"""
        flomo_key = self.config.get("flomo_key", "")
        if not flomo_key:
            raise ValueError("请先在设置中配置Flomo Key Part")
        
        # 构建Flomo URL
        flomo_url = f"{FLOMO_BASE_URL}{flomo_key}/"
        
        # 构建内容
        content = f"**[{input_text}]**\n\n"
        content += f"*[{translation_text}]*\n\n"
        
        # 添加重点词组
        content += "* 重点词组\n\n"
        content += analysis_text + "\n"
        
        # 发送到Flomo
        skip_ssl_check = self.config.get("skip_ssl_check", False)
        response = requests.post(flomo_url, data={"content": content}, verify=not skip_ssl_check)
        response.raise_for_status()
        
        return True


class ConfigManager:
    """配置管理器，负责配置的加密存储和读取"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_file = CONFIG_FILE
        self.secret_salt = SECRET_SALT
    
    def generate_key(self, password):
        """生成加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.secret_salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        return Fernet(base64.urlsafe_b64encode(key))
    
    def load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_file):
                return {}
            
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            # 使用固定密码生成密钥
            key = self.generate_key("loong_translator_2024")
            decrypted_data = key.decrypt(encrypted_data)
            config = json.loads(decrypted_data.decode())
            
            return config
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            return {}
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            # 使用固定密码生成密钥
            key = self.generate_key("loong_translator_2024")
            encrypted_data = key.encrypt(json.dumps(config).encode())
            
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            raise


# ========================================
# 2. 功能服务层 (Service Layer)
# ========================================

class TranslationService:
    """翻译服务类，负责翻译功能的实现"""
    
    def __init__(self, config_manager):
        """初始化翻译服务"""
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        self.translation_api = TranslationAPI(self.config)
    
    def update_config(self):
        """更新配置"""
        self.config = self.config_manager.load_config()
        self.translation_api = TranslationAPI(self.config)
    
    def format_vocabulary(self, vocabulary):
        """格式化词汇信息为Markdown格式"""
        analysis_text = ""
        
        if vocabulary:
            for item in vocabulary:
                word = item.get("word", "")
                phonetic = item.get("phonetic", "")
                
                # 显示单词/词组和音标
                if phonetic:
                    analysis_text += f"**{word}**/{phonetic}/\n"
                else:
                    analysis_text += f"**{word}**\n"
                
                # 显示含义和例句
                meanings = item.get("meanings", [])
                for i, meaning in enumerate(meanings, 1):
                    definition = meaning.get("definition", "")
                    example = meaning.get("example", "")
                    
                    analysis_text += f"{i}. {definition}"
                    if example:
                        analysis_text += f" 例如：*_{example}_*\n"
                    else:
                        analysis_text += "\n"
                
                analysis_text += "\n"  # 在每个词汇后添加空行
        
        return analysis_text
    
    def translate(self, input_text, target_language):
        """执行翻译并返回结果"""
        # 更新配置
        self.update_config()
        
        # 调用API执行翻译
        translation_data = self.translation_api.translate(input_text, target_language)
        
        # 格式化词汇信息
        analysis_text = self.format_vocabulary(translation_data.get("vocabulary", []))
        
        return {
            "translation": translation_data.get("translation", ""),
            "analysis": analysis_text
        }


class FlomoService:
    """Flomo服务类，负责Flomo同步功能的实现"""
    
    def __init__(self, config_manager):
        """初始化Flomo服务"""
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        self.flomo_api = FlomoAPI(self.config)
    
    def update_config(self):
        """更新配置"""
        self.config = self.config_manager.load_config()
        self.flomo_api = FlomoAPI(self.config)
    
    def save_to_flomo(self, input_text, translation_text, analysis_text):
        """保存到Flomo"""
        # 更新配置
        self.update_config()
        
        # 调用API保存到Flomo
        return self.flomo_api.save_note(input_text, translation_text, analysis_text)


class TTSService:
    """TTS服务类，负责文本朗读功能的实现"""
    
    def __init__(self):
        """初始化TTS服务"""
        self.tts_engine = pyttsx3.init()
    
    def read_text(self, text):
        """朗读文本"""
        if not text.strip():
            raise ValueError("没有可朗读的文本")
        
        # 设置TTS属性
        self.tts_engine.setProperty('rate', 150)  # 语速
        self.tts_engine.setProperty('volume', 1.0)  # 音量
        
        # 朗读文本
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()


# ========================================
# 3. 业务控制层 (Controller Layer)
# ========================================

class TranslationController(QThread):
    """翻译控制器，负责异步执行翻译任务"""
    
    # 定义信号
    translation_complete = pyqtSignal(dict)
    translation_error = pyqtSignal(str)
    
    def __init__(self, translation_service, input_text, target_language):
        """初始化翻译控制器"""
        super().__init__()
        self.translation_service = translation_service
        self.input_text = input_text
        self.target_language = target_language
        self.is_running = True
    
    def run(self):
        """执行翻译任务"""
        try:
            if not self.is_running:
                return
            
            # 执行翻译
            result = self.translation_service.translate(self.input_text, self.target_language)
            
            if not self.is_running:
                return
            
            # 发送完成信号
            self.translation_complete.emit(result)
            
        except Exception as e:
            if self.is_running:
                self.translation_error.emit(str(e))
    
    def stop(self):
        """停止翻译任务"""
        self.is_running = False
        self.wait()


class HotkeyController:
    """热键控制器，负责全局热键的设置和管理"""
    
    def __init__(self, callback):
        """初始化热键控制器"""
        self.callback = callback
        self.current_hotkey = None
    
    def setup_hotkey(self, hotkey):
        """设置全局热键"""
        try:
            # 清除旧的热键
            try:
                keyboard.clear_all_hotkeys()
            except AttributeError:
                pass
            
            # 设置新的热键
            keyboard.add_hotkey(hotkey, self.callback)
            self.current_hotkey = hotkey
        except Exception as e:
            print(f"设置快捷键失败: {str(e)}")


# ========================================
# 4. 前端界面层 (UI Layer)
# ========================================

class SettingsDialog(QDialog):
    """设置对话框类"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.setWindowTitle("设置")
        self.setFixedSize(400, 350)
        self.config_manager = config_manager
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        
        # 创建表单布局
        self.form_layout = QFormLayout()
        
        # AI API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow("AI API Key:", self.api_key_edit)
        
        # Flomo Key Part
        self.flomo_key_edit = QLineEdit()
        self.form_layout.addRow("Flomo Key Part:", self.flomo_key_edit)
        
        # Global Hotkey
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setText("ctrl+alt+t")
        self.form_layout.addRow("全局快捷键:", self.hotkey_edit)
        
        # API Endpoint
        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setText("https://api.example.com/v1/chat/completions")
        self.form_layout.addRow("API Endpoint:", self.api_endpoint_edit)
        
        # Model
        self.model_edit = QLineEdit()
        self.model_edit.setText("gpt-3.5-turbo")
        self.form_layout.addRow("Model:", self.model_edit)
        
        # Skip SSL Verification
        self.skip_ssl_check = QPushButton("跳过SSL校验")
        self.skip_ssl_check.setCheckable(True)
        self.skip_ssl_check.setChecked(False)
        self.form_layout.addRow("SSL校验:", self.skip_ssl_check)
        
        # 添加表单到布局
        self.layout.addLayout(self.form_layout)
        
        # 创建按钮
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(self.button_layout)
        
        # 加载现有设置
        self.load_settings()
    
    def load_settings(self):
        """加载现有设置"""
        try:
            config = self.config_manager.load_config()
            if config:
                self.api_key_edit.setText(config.get("api_key", ""))
                self.flomo_key_edit.setText(config.get("flomo_key", ""))
                self.hotkey_edit.setText(config.get("hotkey", "ctrl+alt+t"))
                self.api_endpoint_edit.setText(config.get("api_endpoint", "https://api.example.com/v1/chat/completions"))
                self.model_edit.setText(config.get("model", "gpt-3.5-turbo"))
                self.skip_ssl_check.setChecked(config.get("skip_ssl_check", False))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载设置失败: {str(e)}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 验证Flomo Key Part
            flomo_key = self.flomo_key_edit.text().strip()
            if flomo_key and not flomo_key.isalnum():
                QMessageBox.warning(self, "输入错误", "Flomo Key Part 只能包含字母和数字")
                return
            
            config = {
                "api_key": self.api_key_edit.text(),
                "flomo_key": flomo_key,
                "hotkey": self.hotkey_edit.text(),
                "api_endpoint": self.api_endpoint_edit.text(),
                "model": self.model_edit.text(),
                "skip_ssl_check": self.skip_ssl_check.isChecked()
            }
            
            self.config_manager.save_config(config)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")


class LoongAITranslator(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 600)
        
        # 初始化服务层
        self.config_manager = ConfigManager()
        self.translation_service = TranslationService(self.config_manager)
        self.flomo_service = FlomoService(self.config_manager)
        self.tts_service = TTSService()
        
        # 初始化控制层
        self.hotkey_controller = HotkeyController(self.toggle_window)
        
        # 加载配置
        self.config = self.config_manager.load_config()
        
        # 设置主题
        self.setup_theme()
        
        # 设置UI
        self.setup_ui()
        
        # 设置全局快捷键
        self.setup_hotkey(self.config.get("hotkey", "ctrl+alt+t"))
        
        # 初始化语言列表
        self.init_languages()
        
        # 初始化翻译线程
        self.translation_thread = None
        
        # 初始化等待时间计时器
        self.wait_timer = QTimer()
        self.wait_timer.timeout.connect(self.update_wait_time)
        self.wait_seconds = 0
        self.is_translating = False
    
    def setup_theme(self):
        """设置应用主题"""
        is_dark = darkdetect.isDark()
        
        # 创建调色板
        palette = QPalette()
        
        if is_dark:
            # 深色主题
            palette.setColor(QPalette.ColorRole.Window, QColor(32, 32, 32))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.Base, QColor(48, 48, 48))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(64, 64, 64))
            palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.Button, QColor(64, 64, 64))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(240, 240, 240))
        else:
            # 浅色主题
            palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(palette)
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建垂直分割器
        self.vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(self.vertical_splitter)
        
        # 创建顶部水平分割器
        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.vertical_splitter.addWidget(self.top_splitter)
        
        # 左侧输入区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("请输入要翻译的文本...")
        left_layout.addWidget(self.input_text)
        
        # 翻译按钮布局
        translate_layout = QVBoxLayout()
        self.translate_button = QPushButton("翻译")
        self.translate_button.clicked.connect(self.toggle_translation)
        translate_layout.addWidget(self.translate_button)
        
        left_layout.addLayout(translate_layout)
        
        # 右侧输出区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 语言选择
        self.language_combo = QComboBox()
        right_layout.addWidget(self.language_combo)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("翻译结果将显示在这里...")
        # 启用Markdown格式
        self.output_text.setAcceptRichText(True)
        right_layout.addWidget(self.output_text)
        
        self.read_button = QPushButton("🔊 朗读翻译")
        self.read_button.clicked.connect(self.read_translation)
        right_layout.addWidget(self.read_button)
        
        # 将左右两个区域添加到顶部分割器
        self.top_splitter.addWidget(left_widget)
        self.top_splitter.addWidget(right_widget)
        
        # 底部分析区域
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        # 分析结果标题和按钮
        analysis_header_layout = QHBoxLayout()
        analysis_label = QLabel("重点词组")
        analysis_header_layout.addWidget(analysis_label)
        
        self.save_to_flomo_button = QPushButton("保存到 Flomo")
        self.save_to_flomo_button.clicked.connect(self.save_to_flomo)
        analysis_header_layout.addWidget(self.save_to_flomo_button)
        
        self.settings_button = QPushButton("⚙️ 设置")
        self.settings_button.clicked.connect(self.open_settings)
        analysis_header_layout.addWidget(self.settings_button)
        
        bottom_layout.addLayout(analysis_header_layout)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlaceholderText("重点词组将显示在这里...")
        # 启用Markdown格式
        self.analysis_text.setAcceptRichText(True)
        bottom_layout.addWidget(self.analysis_text)
        
        self.vertical_splitter.addWidget(bottom_widget)
        
        # 设置分割器比例
        self.vertical_splitter.setSizes([400, 200])
        self.top_splitter.setSizes([450, 450])
    
    def init_languages(self):
        """初始化语言列表"""
        languages = [
            "中文", "英语", "日语", "韩语", "法语", 
            "德语", "西班牙语", "俄语", "葡萄牙语", "意大利语"
        ]
        self.language_combo.addItems(languages)
        # 默认选择英语
        self.language_combo.setCurrentText("英语")
    
    def setup_hotkey(self, hotkey):
        """设置全局快捷键"""
        self.hotkey_controller.setup_hotkey(hotkey)
    
    def toggle_window(self):
        """切换窗口显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.input_text.setFocus()
    
    def toggle_translation(self):
        """切换翻译/停止状态"""
        if self.is_translating:
            # 如果正在翻译，则停止
            self.stop_translation()
        else:
            # 如果未在翻译，则开始
            self.start_translation()
    
    def start_translation(self):
        """开始翻译"""
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "警告", "请输入要翻译的文本")
            return
        
        target_language = self.language_combo.currentText()
        
        # 如果已有翻译线程在运行，先停止
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.stop()
        
        # 保存原始占位符文本
        original_placeholder = self.output_text.placeholderText()
        
        # 重置等待时间并在输出框中显示
        self.wait_seconds = 0
        self.output_text.setMarkdown(f"等待中... 0秒")
        
        # 更改按钮状态为停止
        self.translate_button.setText("停止")
        self.is_translating = True
        
        # 启动等待时间计时器
        self.wait_timer.start(1000)  # 每秒更新一次
        
        # 创建并启动翻译线程
        self.translation_thread = TranslationController(
            self.translation_service, 
            input_text, 
            target_language
        )
        self.translation_thread.translation_complete.connect(self.on_translation_complete)
        self.translation_thread.translation_error.connect(self.on_translation_error)
        self.translation_thread.finished.connect(self.on_translation_finished)
        self.translation_thread.start()
    
    def stop_translation(self):
        """停止翻译"""
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.stop()
        
        # 停止等待时间计时器
        self.wait_timer.stop()
        
        # 恢复输出框占位符
        self.output_text.setPlaceholderText("翻译结果将显示在这里...")
        
        # 恢复按钮状态为翻译
        self.translate_button.setText("翻译")
        self.is_translating = False
    
    def on_translation_complete(self, result):
        """翻译完成处理"""
        # 显示翻译结果（使用Markdown格式）
        self.output_text.setMarkdown(result.get("translation", ""))
        
        # 显示分析结果（使用Markdown格式）
        self.analysis_text.setMarkdown(result.get("analysis", ""))
    
    def on_translation_error(self, error_message):
        """翻译错误处理"""
        QMessageBox.warning(self, "错误", error_message)
    
    def on_translation_finished(self):
        """翻译线程结束处理"""
        # 停止等待时间计时器
        self.wait_timer.stop()
        
        # 恢复按钮状态为翻译
        self.translate_button.setText("翻译")
        self.is_translating = False
    
    def update_wait_time(self):
        """更新等待时间显示"""
        self.wait_seconds += 1
        self.output_text.setMarkdown(f"等待中... {self.wait_seconds}秒")
    
    def read_translation(self):
        """朗读翻译结果"""
        text = self.output_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "没有可朗读的翻译结果")
            return
        
        try:
            self.tts_service.read_text(text)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"朗读失败: {str(e)}")
    
    def save_to_flomo(self):
        """保存到Flomo"""
        input_text = self.input_text.toPlainText().strip()
        translation_text = self.output_text.toPlainText().strip()
        analysis_text = self.analysis_text.toPlainText().strip()
        
        if not input_text or not translation_text:
            QMessageBox.warning(self, "警告", "请先进行翻译")
            return
        
        try:
            self.flomo_service.save_to_flomo(input_text, translation_text, analysis_text)
            QMessageBox.information(self, "成功", "已保存到Flomo")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存到Flomo失败: {str(e)}")
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.config_manager)
        if dialog.exec():
            # 更新配置
            self.config = self.config_manager.load_config()
            
            # 更新全局快捷键
            self.setup_hotkey(self.config.get("hotkey", "ctrl+alt+t"))


if __name__ == "__main__":
    # 修复中文显示问题
    import matplotlib
    matplotlib.use('Agg')
    
    # 忽略libpng警告
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="PIL")
    
    # 忽略requests的SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont()
    font.setFamily("Microsoft YaHei")
    app.setFont(font)
    
    window = LoongAITranslator()
    window.show()
    
    sys.exit(app.exec())