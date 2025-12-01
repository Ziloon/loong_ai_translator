import sys
import os
from cx_Freeze import setup, Executable

# 确保中文显示正常
os.environ['TCL_LIBRARY'] = os.path.join(sys.base_prefix, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(sys.base_prefix, 'tcl', 'tk8.6')

# 读取requirements.txt中的依赖
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# 构建选项
build_exe_options = {
    'packages': ['PyQt6', 'requests', 'keyboard', 'cryptography', 'pyttsx3', 'darkdetect', 'win32com.client', 'comtypes'],
    'includes': ['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
    'excludes': ['pandas'],  # 排除不需要的大型库
    'include_files': [],
    'optimize': 2,
}

# 基础设置
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'  # 使用GUI模式，不显示控制台窗口

# 执行文件配置
executables = [
    Executable(
        script='main.py',
        base=base,
        target_name='LoongAITranslator.exe',
        icon=None,  # 如果有图标文件，可以在这里指定
        shortcut_name='Loong AI Translator',
        shortcut_dir='ProgramMenuFolder',
    )
]

# 应用元数据
setup(
    name='Loong AI Translator',
    version='1.0.0',
    description='AI翻译助手，支持专业词汇分析、TTS朗读和Flomo笔记同步',
    author='Loong',
    author_email='',
    options={'build_exe': build_exe_options},
    executables=executables,
    python_requires='>=3.8',
)