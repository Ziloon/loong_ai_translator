# Loong 的 AI Translator

一个基于 Python 和 PyQt6 的桌面翻译应用，具有 AI 翻译、专业词汇分析、TTS 朗读以及加密存储配置和 Flomo 笔记同步功能。

## 功能特点

- **AI 翻译**：支持多语言互译，提供高质量翻译结果
- **专业词汇分析**：自动识别并解释文本中的关键词组和专业词汇
- **TTS 朗读**：支持朗读翻译结果，提升语言学习体验
- **加密配置存储**：安全保存用户 API 密钥和设置
- **Flomo 笔记同步**：一键将翻译和分析结果保存到 Flomo 笔记
- **全局快捷键**：支持在任何应用中快速调用翻译功能
- **动态主题切换**：根据系统设置自动切换深色/浅色模式
- **异步翻译**：翻译过程中界面不会卡死，支持取消翻译

## 系统要求

- Python 3.8+
- PyQt6
- 其他依赖见 requirements.txt

## 安装说明

1. 克隆或下载本项目

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行应用：
```bash
python main.py
```

## 使用说明

1. 首次运行应用后，点击右下角的 "⚙️ 设置" 按钮配置以下选项：
   - **AI API Key**：您的 OpenAI 兼容 API 密钥
   - **Flomo Key Part**：您的 Flomo Webhook URL 中的哈希密钥部分
   - **全局快捷键**：默认为 `ctrl+alt+t`，可自定义
   - **API Endpoint**：OpenAI 兼容 API 的端点 URL
   - **Model**：使用的模型名称，默认为 `gpt-3.5-turbo`
   - **SSL校验**：是否跳过 SSL 校验，默认不跳过

2. 在左侧输入框中输入要翻译的文本

3. 在右侧选择目标语言

4. 点击 "翻译" 按钮开始翻译：
   - 翻译过程中，按钮会变成 "停止"，可以随时取消翻译
   - 翻译结果区域会显示等待时间
   - 翻译完成后，会显示翻译结果和词汇分析

5. 翻译完成后，可以：
   - 点击 "🔊 朗读翻译" 按钮朗读翻译结果
   - 查看底部的词汇分析结果
   - 点击 "保存到 Flomo" 按钮将翻译和分析结果保存到 Flomo 笔记

## 架构说明

本应用采用四层架构设计，遵循 Python 之禅的原则：

1. **数据接口层 (API Layer)**：
   - `TranslationAPI`：处理与翻译服务的通信
   - `FlomoAPI`：处理与 Flomo 服务的通信
   - `ConfigManager`：处理配置的加密存储和读取

2. **功能服务层 (Service Layer)**：
   - `TranslationService`：实现翻译功能的核心逻辑
   - `FlomoService`：实现 Flomo 同步功能的核心逻辑
   - `TTSService`：实现文本朗读功能的核心逻辑

3. **业务控制层 (Controller Layer)**：
   - `TranslationController`：控制异步翻译任务的执行
   - `HotkeyController`：管理全局热键的设置和响应

4. **前端界面层 (UI Layer)**：
   - `SettingsDialog`：设置对话框界面
   - `LoongAITranslator`：主窗口界面

这种架构设计使得应用具有良好的可扩展性和可维护性，可以方便地替换底层实现而不影响上层功能。

## 注意事项

- 使用前请确保已配置有效的 AI API Key
- Flomo Key Part 仅需要 Webhook URL 中的哈希密钥部分，例如 `44795ea6eb39053ea968cdf2274f29`
- 应用会自动根据系统主题切换深色/浅色模式
- 全局快捷键可能需要管理员权限才能正常工作

## 许可证

MIT License