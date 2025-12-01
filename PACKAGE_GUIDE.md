# Loong AI Translator - Windows打包指南

本指南提供了将Loong AI Translator应用打包为Windows可执行文件(.exe)的详细步骤。

## 准备工作

1. 确保您的系统已安装Python 3.8或更高版本
2. 安装所有必需的依赖：

```bash
pip install -r requirements.txt
```

## 方法一：使用PyInstaller（推荐）

PyInstaller是一个流行的Python打包工具，可以将Python应用程序打包为独立的可执行文件。

### 步骤：

1. 确保已安装PyInstaller：

```bash
pip install pyinstaller
```

2. 使用提供的spec文件打包应用：

```bash
pyinstaller loong_translator.spec
```

3. 打包完成后，可执行文件将位于`dist/LoongAITranslator/`目录中

### 自定义打包：

如果需要自定义打包选项，可以直接使用PyInstaller命令：

```bash
pyinstaller --name="LoongAITranslator" --windowed --onefile --hidden-import="PyQt6.QtCore" --hidden-import="PyQt6.QtGui" --hidden-import="PyQt6.QtWidgets" --hidden-import="win32com.client" --hidden-import="comtypes" main.py
```

## 方法二：使用cx_Freeze

cx_Freeze是另一个Python打包工具，也可以用于创建Windows可执行文件。

### 步骤：

1. 确保已安装cx_Freeze：

```bash
pip install cx_Freeze
```

2. 使用提供的setup.py文件打包应用：

```bash
python setup.py build
```

3. 打包完成后，可执行文件将位于`build/exe.win-amd64-3.x/`目录中

## 注意事项

1. **Windows特定依赖**：
   - pywin32：用于与Windows系统交互
   - comtypes：用于处理COM接口，pyttsx3依赖此库

2. **中文显示**：
   - 应用已配置为支持中文显示，无需额外设置

3. **运行时文件**：
   - 应用首次运行时会在用户目录下创建配置文件
   - 配置文件路径：`%USERPROFILE%\.loong_translator\config.json`

4. **杀毒软件误报**：
   - 打包后的可执行文件可能被某些杀毒软件误报为恶意软件
   - 这是因为PyInstaller等打包工具使用的打包方式可能被误认为是可疑行为
   - 如果遇到此问题，请将应用添加到杀毒软件的白名单中

## 故障排除

### 常见问题：

1. **缺少DLL文件**：
   - 如果运行时提示缺少某些DLL文件，请确保已安装所有依赖
   - 可能需要手动复制一些系统DLL文件到可执行文件目录

2. **应用无法启动**：
   - 检查是否所有依赖都已正确安装
   - 尝试以管理员身份运行应用

3. **中文显示问题**：
   - 如果中文显示为乱码，请确保系统字体支持中文
   - 可能需要安装中文字体包

## 发布建议

1. 创建安装程序：
   - 可以使用Inno Setup或NSIS等工具创建安装向导
   - 这将使最终用户更容易安装和使用应用

2. 数字签名：
   - 考虑为可执行文件添加数字签名
   - 这可以提高用户信任度并减少杀毒软件误报

3. 版本信息：
   - 在发布前更新应用版本号
   - 维护清晰的更新日志