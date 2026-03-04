# 校园教材共享服务系统 - 项目上下文

## 项目概览
- **项目名称**: 校园教材共享服务系统
- **项目路径**: `C:\Projects\textbook-sharing\`
- **技术栈**: Django 4.2 (后端) + Vue 3 + Element Plus (前端) + MySQL 8.0

## 目录结构
```
C:\Projects\textbook-sharing\
├── backend/                # Django 后端
│   ├── config/             # Django 项目配置 (settings.py, urls.py, asgi.py)
│   ├── apps/               # 7 个 Django App
│   │   ├── users/          # 用户管理 (注册/登录/个人资料)
│   │   ├── textbooks/      # 教材管理 (发布/搜索/分类)
│   │   ├── orders/         # 订单管理 (购买/借阅/交易)
│   │   ├── messaging/      # 消息系统 (WebSocket 实时聊天)
│   │   ├── reviews/        # 审核管理 (教材审核/敏感词过滤)
│   │   ├── recommendations/# 推荐系统 (基于协同过滤)
│   │   └── statistics/     # 数据统计
│   ├── fixtures/           # 初始数据 (30 个分类 + 8 个敏感词)
│   ├── media/              # 上传文件目录
│   └── manage.py
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # Vue Router
│   │   ├── api/            # Axios API 封装
│   │   └── utils/          # 工具函数
│   └── vite.config.js      # Vite 配置 (端口 3000, 代理到 8000)
└── start.bat               # 一键启动脚本
```

## 运行环境
- **Python**: 3.8.0 (`D:\UersApps\Python\`)
- **Node.js**: v24.14.0, npm 11.9.0
- **MySQL**: 8.0.37 (`D:\UersApps\MySQLfix\`), 配置文件 `D:\UersApps\MySQLData\my.ini`
- **系统代理**: `127.0.0.1:7897` (Clash VPN, 必须保持开启)
- **数据库名**: `textbook_sharing`, 用户 `root`, 密码 `root123456`

## 特殊配置说明
- 使用 **PyMySQL** 替代 mysqlclient（在 `config/__init__.py` 中配置）
- 本地开发模式：InMemoryChannelLayer（无需 Redis）、LocMemCache、CELERY_TASK_ALWAYS_EAGER=True、`USE_TZ=False`（避免 MySQL 时区表缺失问题）
- channels 4.x 使用 `AsyncWebsocketConsumer`（小写 s）
- pip 安装命令需带代理：`pip install <包> -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --proxy http://127.0.0.1:7897`
- npm 代理已配置：registry `https://registry.npmmirror.com`

## 启动方式
双击 `C:\Projects\textbook-sharing\start.bat`，或手动：
1. 后端：`cd backend && python manage.py runserver 8000`
2. 前端：`cd frontend && npm run dev`
3. 访问：http://localhost:3000

## 账号信息
- 管理员：`admin` / `admin123456`（role=admin）
- 测试用户：`test_user`（学生，未验证）

## 关键模型字段
- **Textbook**: title, author, isbn, `price`(非 selling_price), original_price, `condition`(IntegerField 1-5), transaction_type, status, owner(FK)
- **TextbookVote**: textbook(FK), user(FK), vote(SmallInt 1/-1), unique_together('textbook','user')
- **TextbookComment**: textbook(FK), user(FK), content(TextField 500), parent(self FK, 支持嵌套回复)
- **SharedResource**: title, description, file(FileField → resources/), file_size, resource_type(pdf/doc/ppt/other), category(FK), uploader(FK), download_count
- **Order**: order_no(自动生成), textbook(FK), buyer(FK), seller(FK), price, status, transaction_type
- **TextbookCreateView** 使用 `MultiPartParser, FormParser`（非 JSON）

## 主要 API 端点
- 用户：/api/users/register/, /api/users/login/, /api/users/profile/, /api/users/change-password/, /api/users/{id}/ (AllowAny, 公开主页)
- 教材：/api/textbooks/, /api/textbooks/create/, /api/textbooks/search/, /api/textbooks/{id}/, /api/textbooks/my/, /api/textbooks/categories/tree/
- 管理员删除：/api/textbooks/admin/{id}/delete/
- 点赞点踩：/api/textbooks/{id}/vote/ (GET 统计+我的投票, POST 切换)
- 评论：/api/textbooks/{id}/comments/ (GET 列表, POST 发布), /api/textbooks/comments/{id}/delete/
- 在线资料：/api/textbooks/resources/ (GET 列表, POST 上传), /api/textbooks/resources/{id}/ (GET 详情, DELETE 删除), /api/textbooks/resources/{id}/download/ (POST 记录下载)
- 订单：/api/orders/create/, /api/orders/, /api/orders/{id}/confirm|complete|cancel|return/
- 审核：/api/reviews/pending/, /api/reviews/action/{id}/, /api/reviews/sensitive-words/

## 特殊修复记录
- **统计模块 500 错误修复**: MySQL 时区表为空导致 `TruncMonth`/`TruncDate` 报 `ValueError`，通过设置 `USE_TZ = False` 解决
- **统计模块前后端数据契约修复**: 8 处字段名/数据格式不匹配（`views.py` 返回字段已对齐前端期望）
- **自动审核**: 无敏感词的教材自动审核通过（`reviews/signals.py`）
- **评论 textbook 必填修复**: `TextbookCommentSerializer` 中 `textbook` 字段加入 `read_only_fields`，通过 URL pk 自动设置
- **统计排行图修复**: `Statistics.vue` 中 `loadRank` 的 JS `||` 短路导致“按订单数”显示成浏览量，已改为根据 `rankType` 明确取对应字段
- **用户公开主页权限**: `UserDetailView` 改为 `AllowAny` + `UserPublicSerializer`（不暴露 email/phone/student_id）

## 新增功能记录
- **管理员删除教材**: `AdminTextbookDeleteView`，管理员可删除任意用户的教材
- **点赞/点踩**: `TextbookVote` 模型 + `TextbookVoteView`，教材列表卡片和详情页均显示计数
- **评论系统**: `TextbookComment` 模型（支持嵌套回复），本人或管理员可删除
- **在线资料共享区**: `SharedResource` 模型，新页面 `Resources.vue`，支持上传/下载/筛选/删除，导航栏已添加入口
- **用户公开主页**: 新页面 `UserProfile.vue`（路由 `/user/:id`），展示用户公开信息 + TA 发布的教材；教材详情页/列表页/评论区的用户名均可点击跳转

## 待完成事项
- [ ] 论文测试部分（黑盒测试、白盒测试、性能测试、可用性测试）
  - 工具：Postman、Selenium、JMeter 5.6、pytest+coverage
- [ ] 清理 Docker 相关文件（docker-compose.yml, Dockerfile 等）
