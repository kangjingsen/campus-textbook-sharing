# Textbook Sharing 项目文件用途说明

本文档用于说明项目中主要目录和关键文件的职责，便于新成员快速上手。

## 1. 根目录文件

- `docker-compose.yml`
  - 定义整套容器化服务的编排方式，通常包含后端、前端、数据库等服务。
- `README.md`
  - 项目总览文档，包含启动方式、功能简介、开发说明。
- `PROJECT_CONTEXT.md`
  - 项目背景与上下文说明，帮助理解业务目标与系统边界。
- `PRE_DEFENSE_GUIDE.md`
  - 答辩前准备指南，通常用于演示和讲解流程。
- `start.bat`
  - Windows 一键启动脚本，简化本地运行流程。

## 2. 后端目录（backend）

后端为 Django 项目，按业务模块拆分为多个 app。

### 2.1 后端核心文件

- `backend/manage.py`
  - Django 管理入口。用于运行开发服务器、迁移数据库、创建管理员、执行自定义命令。
- `backend/requirements.txt`
  - Python 依赖列表。
- `backend/Dockerfile`
  - 后端镜像构建配置。
- `backend/entrypoint.sh`
  - 容器启动脚本，通常包含等待数据库、执行迁移、启动服务等步骤。

### 2.2 全局配置（backend/config）

- `backend/config/settings.py`
  - Django 全局配置（数据库、缓存、中间件、认证、静态文件等）。
- `backend/config/urls.py`
  - 项目总路由，将请求分发到各 app。
- `backend/config/asgi.py`
  - ASGI 入口，支持异步协议（如 WebSocket）。
- `backend/config/wsgi.py`
  - WSGI 入口，适用于传统同步部署。
- `backend/config/celery.py`
  - Celery 任务队列配置。

### 2.3 业务 app 通用文件职责

以下模式适用于 `community`、`messaging`、`orders`、`recommendations`、`reviews`、`statistics`、`textbooks`、`users` 等目录：

- `models.py`
  - 定义数据库模型（表结构和字段关系）。
- `serializers.py`
  - API 数据序列化与反序列化规则。
- `views.py`
  - 业务接口逻辑（请求处理、调用服务、返回响应）。
- `urls.py`
  - app 级路由配置。
- `admin.py`
  - Django Admin 管理后台模型注册与展示配置。
- `apps.py`
  - app 启动配置。
- `migrations/`
  - 数据库迁移文件，用于版本化管理表结构变更。

### 2.4 业务 app 中的特殊文件

- `backend/apps/messaging/consumers.py`
  - WebSocket 消费者，处理实时消息收发。
- `backend/apps/messaging/middleware.py`
  - 消息模块相关中间件（如鉴权或上下文注入）。
- `backend/apps/messaging/routing.py`
  - WebSocket 路由配置。
- `backend/apps/recommendations/content_based.py`
  - 基于内容的推荐算法实现。
- `backend/apps/recommendations/collaborative_filtering.py`
  - 协同过滤推荐算法实现。
- `backend/apps/recommendations/tasks.py`
  - 推荐模块异步任务。
- `backend/apps/recommendations/signals.py`
  - 推荐相关信号处理逻辑。
- `backend/apps/reviews/sensitive_filter.py`
  - 评论敏感词过滤逻辑。
- `backend/apps/reviews/signals.py`
  - 评论模块信号处理。

### 2.5 后端辅助目录

- `backend/fixtures/initial_data.json`
  - 初始化数据，可用于开发环境快速导入样例数据。
- `backend/tests/`
  - 后端测试代码（如订单与统计逻辑测试）。
- `backend/utils/permissions.py`
  - 通用权限控制工具。
- `backend/media/`
  - 用户上传文件目录（封面、支付二维码、资源文件等）。

## 3. 前端目录（frontend）

前端使用 Vite 构建（通常为 Vue 技术栈）。

- `frontend/package.json`
  - 前端依赖和 npm 脚本定义。
- `frontend/vite.config.js`
  - Vite 构建与开发服务器配置。
- `frontend/index.html`
  - 前端应用入口 HTML。
- `frontend/src/main.js`
  - 前端启动入口，挂载应用、注册插件。
- `frontend/src/App.vue`
  - 根组件。
- `frontend/src/api/`
  - API 请求封装。
- `frontend/src/components/`
  - 可复用组件。
- `frontend/src/router/`
  - 路由定义。
- `frontend/src/stores/`
  - 状态管理逻辑。
- `frontend/src/views/`
  - 页面级视图。
- `frontend/Dockerfile`
  - 前端镜像构建配置。
- `frontend/nginx.conf`
  - 前端部署时 Nginx 配置。

## 4. 数据库与脚本

- `mysql/init.sql`
  - MySQL 初始化脚本（建库、建表、初始数据或权限配置）。
- `scripts/deepwiki/`
  - 项目脚本目录（通常用于文档、分析或自动化任务）。

## 5. 快速定位建议

- 想改数据库结构：优先看对应 app 的 `models.py` 与 `migrations/`。
- 想改接口行为：看对应 app 的 `views.py`、`serializers.py`、`urls.py`。
- 想看全局配置：看 `backend/config/settings.py` 与 `backend/config/urls.py`。
- 想改前端页面：看 `frontend/src/views/` 与 `frontend/src/components/`。
- 想改前后端启动方式：看 `docker-compose.yml`、`backend/Dockerfile`、`frontend/Dockerfile`、`start.bat`。
