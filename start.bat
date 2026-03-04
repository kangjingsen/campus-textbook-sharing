@echo off
chcp 65001 >nul
echo ========================================
echo   校园教材共享服务系统 - 一键启动
echo ========================================
echo.

echo [1/2] 启动后端服务器 (端口 8000)...
cd /d C:\Projects\textbook-sharing\backend
start "后端-Django" cmd /k "python manage.py runserver 8000"

echo [2/2] 启动前端服务器 (端口 3000)...
cd /d C:\Projects\textbook-sharing\frontend
start "前端-Vite" cmd /k "npx vite"

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
