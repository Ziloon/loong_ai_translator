@echo off
echo 正在为 Loong AI Translator 创建 Windows 可执行文件...

echo.
echo 第一步：安装依赖...
pip install -r requirements.txt

echo.
echo 第二步：使用 PyInstaller 打包...
pyinstaller loong_translator.spec

echo.
echo 打包完成！
echo 可执行文件位于：dist\LoongAITranslator\LoongAITranslator.exe
echo.
echo 提示：
echo 1. 如果需要单个可执行文件，请运行：pyinstaller --onefile loong_translator.spec
echo 2. 如果遇到问题，请参考 PACKAGE_GUIDE.md 文件
echo.
pause