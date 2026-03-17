@echo off
chcp 65001 >nul
setlocal

set ROOT_DIR=%~dp0

echo ========================================
echo   校园教材共享服务系统 - 一键启动
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
	echo [错误] 未找到 Python，请先安装并配置到 PATH。
	pause
	exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
	echo [错误] 未找到 npm，请先安装 Node.js 并配置到 PATH。
	pause
	exit /b 1
)

echo [1/3] 启动后端服务器 (端口 8000)...
cd /d "%ROOT_DIR%backend"
start "后端-Django" cmd /k "python manage.py migrate && python manage.py runserver 8000"

echo [2/3] 启动前端服务器 (端口 3000)...
cd /d "%ROOT_DIR%frontend"
start "前端-Vite" cmd /k "npx vite"

echo [3/3] 已发起启动命令，服务正在初始化...

echo.
echo ========================================
echo   启动完成！
echo   前端地址: http://localhost:3000
echo   后端地址: http://localhost:8000
echo   管理后台: http://localhost:8000/admin/
echo   管理员账号: admin / admin123456
echo ========================================
echo.
echo 关闭此窗口不会影响服务运行。
echo 要停止服务，请关闭"后端-Django"和"前端-Vite"窗口。
pause
