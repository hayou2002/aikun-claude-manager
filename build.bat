@echo off
echo ========================================
echo   aikun-claude-manager - 本地打包
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [2/3] 安装依赖...
pip install -r requirements.txt -q
pip install pyinstaller -q

echo [3/3] 打包应用程序...
pyinstaller --onefile --noconsole --name "aikun-claude-manager" --add-data="ui;ui" --add-data="logo.png;." --icon=logo.ico main.py

echo.
echo 打包完成！
echo 生成文件: dist\aikun-claude-manager.exe
echo.
pause
