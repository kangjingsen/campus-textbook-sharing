# 校园教材共享服务系统

一个功能完善的校园二手教材交易平台，支持买卖、租借、赠送等多种交易模式。

## 技术栈

- **后端**: Django 4.2 + Django REST Framework + Django Channels + Celery
- **前端**: Vue 3 + Element Plus + Pinia + ECharts
- **数据库**: MySQL 8.0
- **缓存/消息队列**: Redis 7（本地开发可不启动，使用 InMemoryChannelLayer）
- **部署**: Docker Compose / 本地 start.bat 一键启动

## 功能模块

### 用户端
- 🔐 用户注册/登录（JWT认证）
- 📚 教材浏览、模糊搜索
- 📝 发布教材（买卖/租借/赠送）
- 🛒 下单交易、订单管理
- 💬 WebSocket 实时私信聊天
- 🎯 个性化推荐（协同过滤 + 内容推荐混合算法）
- 💖 心愿单（记录需求、驱动推荐优化）
- 👤 个人中心、浏览历史
- 👍 教材点赞/点踩
- 💬 教材评论（支持嵌套回复）
- 📂 在线资料共享区（上传/下载/管理电子资料）
- 🧾 在线资料售卖（资料订单、卖家确认后提供支付二维码、支付后下载）

### 管理端
- 📊 数据概览仪表盘
- ✅ 教材审核（DFA敏感词过滤自动审核 + 人工审核，无敏感词自动通过）
- 🗑 管理员可删除任意用户的上架教材
- 👥 用户管理（角色分配、禁用/启用）
- 📂 分类管理（多级分类树）
- 🚫 敏感词管理
- 📈 多维统计分析（流通率、价格趋势、学院需求、热门排行等）
- 🏆 售卖排行榜、需求排行榜、优秀商家
- 📉 取消订单专题分析（取消率趋势、高取消分类/卖家）
- 📊 价格统计增强（价格指数、环比、同比、最大最小值、中位数、平均数）

## 核心算法

1. **DFA敏感词过滤**: 基于确定有限自动机的 O(n) 时间复杂度敏感词检测
2. **混合推荐算法**: 协同过滤(60%) + 基于内容推荐(40%)，冷启动回退热门推荐

## 快速启动

### Docker Compose 一键部署

```bash
# 克隆项目
cd textbook-sharing

# 启动所有服务
docker-compose up -d --build

# 访问
# 前台: http://localhost
# 后台API: http://localhost:8000/api/
# 默认管理员: admin / admin123456
```

### 本地开发

**后端:**
```bash
cd backend
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata fixtures/initial_data.json
python manage.py createsuperuser
python manage.py runserver
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

### 数据初始化与教材回填（可选）

```bash
cd backend

# 1) 给末级分类补教材（默认每类补到10本）
python manage.py seed_textbooks --per-category 10

# 2) 仅对自动生成教材进行公开数据回填（书名/作者/简介/封面）
python manage.py enrich_textbooks_open_data --only-seeded

# 3) 查看回填覆盖率
python manage.py shell -c "from apps.textbooks.models import Textbook; total=Textbook.objects.count(); open_data=Textbook.objects.filter(description__startswith='[OPEN_DATA').count(); seeded=Textbook.objects.filter(description__startswith='[AUTO_SEED]').count(); print('total=', total, 'open_data=', open_data, 'auto_seed=', seeded)"
```

说明：`start.bat` 默认走系统 `python`，不是工作区 `.venv`。

## 项目结构

```
textbook-sharing/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── entrypoint.sh
│   ├── manage.py
│   ├── config/              # Django配置
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── apps/
│   │   ├── users/           # 用户管理
│   │   ├── textbooks/       # 教材管理
│   │   ├── reviews/         # 审核系统（含DFA敏感词）
│   │   ├── orders/          # 订单处理
│   │   ├── messaging/       # 即时通讯（WebSocket）
│   │   ├── recommendations/ # 推荐引擎
│   │   └── statistics/      # 统计分析
│   ├── utils/               # 工具函数
│   └── fixtures/            # 初始数据
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│       ├── api/             # API接口
│       ├── router/          # 路由
│       ├── stores/          # Pinia状态
│       └── views/           # 页面组件
│           └── admin/       # 管理后台
└── README.md
```

## API 接口概览

| 模块 | 端点 | 说明 |
|------|------|------|
| 用户 | `/api/users/` | 注册、登录、个人信息 |
| 教材 | `/api/textbooks/` | CRUD、搜索、我的教材、点赞点踩、评论 |
| 资料 | `/api/textbooks/resources/` | 在线资料上传、下载、删除 |
| 订单 | `/api/orders/` | 下单、确认、完成、取消 |
| 消息 | `/api/messages/` | 会话、消息、未读数 |
| 审核 | `/api/reviews/` | 待审列表、审核操作 |
| 推荐 | `/api/recommendations/` | 个性化推荐、热门 |
| 心愿单 | `/api/recommendations/wishlist/` | 心愿单增删改查 |
| 统计 | `/api/statistics/` | 多维统计数据 |
| 资料订单 | `/api/textbooks/resources/orders/` | 资料订单创建、确认、支付完成、取消 |
| WebSocket | `ws://host/ws/chat/<id>/` | 实时聊天 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_NAME | textbook_sharing | 数据库名 |
| DB_USER | root | 数据库用户 |
| DB_PASSWORD | root123456 | 数据库密码 |
| DB_HOST | db | 数据库主机 |
| REDIS_HOST | redis | Redis主机 |
| SECRET_KEY | django-secret-key | Django密钥 |
