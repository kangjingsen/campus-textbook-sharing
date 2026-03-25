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
- ✉️ 忘记密码（邮箱重置链接）
- 📚 教材浏览、模糊搜索
- 📝 发布教材（买卖/租借/赠送）
- 🛒 下单交易、订单管理
- 💬 WebSocket 实时私信聊天
- 🎯 个性化推荐（协同过滤 + 内容推荐混合算法）
- 💖 心愿单（记录需求、驱动推荐优化、更新后强制刷新推荐）
- 🎯 推荐增强（支持心愿关键词多字段匹配，过滤本人教材，避免缓存滞后）
- 👤 个人中心、浏览历史
- 👍 教材点赞/点踩
- ⭐ 教材星级评分（支持修改与取消）
- 💬 教材评论（支持嵌套回复）
- 📂 在线资料共享区（上传/下载/管理电子资料）
- 🧾 在线资料售卖（资料订单、卖家确认后上传支付二维码图片、支付后下载）
- 📁 我的在线资料（独立列表、筛选、CSV/XLSX 导出）
- 📊 我的统计分析（个人数据概览、积压排行、需求排行）
- 🧭 我的教材转化漏斗（在架→被下单→确认→完成→取消）
- 📋 教材批量导入导出（CSV/XLSX 格式）
- 📝 订单取消原因必填（买卖双方均可发起，记录取消方角色）
- 🏛 论坛问答社区（讨论/问答帖、最佳回答标记、浏览统计）
- 🙋 个人中心我的帖子（查看本人发帖并一键跳转论坛详情）
- 👤 帖子作者主页跳转（从帖子直接进入用户主页）
- 📢 公告资讯（平台公告展示）

### 管理端
- 📊 数据概览仪表盘
- ✅ 教材审核（DFA敏感词过滤自动审核 + 人工审核，无敏感词自动通过）
- 🗑 管理员可删除任意用户的上架教材
- 👥 用户管理（角色分配、禁用/启用）
- 📂 分类管理（多级分类树）
- 🚫 敏感词管理
- 📈 多维统计分析（流通率、价格趋势、学院需求、热门排行等）- 支持统一筛选快速切换
- 🏆 售卖排行榜、需求排行榜、优秀商家
- 📉 取消订单专题分析（取消率趋势、高取消分类/卖家）
- 🧾 取消原因分布与买卖方取消占比分析
- ⏱ 履约漏斗与时效分析（教材订单 + 资料订单）
- 📊 价格统计增强（价格指数、环比、同比、最大最小值、中位数、平均数）
- 📋 论坛与公告管理（创建/编辑/删除公告与帖子）

## 关键修复与优化

- **商家完成率计算修复**: 完成率从包含所有订单状态改为仅根据已定论订单（completed/cancelled/returned），排除待确认(pending)和已确认(confirmed)订单，使数据分布从极端(0%-100%)改为合理(25%-91%)
- **并发下单修复**: 下单与取消流程引入事务+行级锁，避免同一本教材并发重复下单
- **取消回架修复**: 取消订单时先判断是否仍存在进行中订单，避免错误回架
- **评分机制升级**:
	- 商家评分：同一用户可重复提交，按“更新”处理
	- 教材评分：支持创建/修改/取消（传 `0` 或重复同分值可取消）

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

# 3) 通过Web爬虫扩展教材库（豆瓣+OpenLibrary+掌阅+番茄等多源）
python manage.py expand_textbooks_real --multiplier 4        # 4倍扩展（基于当前总量）
python manage.py expand_textbooks_real --target-total 2000   # 目标达到2000本
python manage.py expand_textbooks_real --target-total 2000 --owner-username admin --dry-run  # 预览模式

# 4) 查看回填覆盖率
python manage.py shell -c "from apps.textbooks.models import Textbook; total=Textbook.objects.count(); open_data=Textbook.objects.filter(description__startswith='[OPEN_DATA').count(); seeded=Textbook.objects.filter(description__startswith='[AUTO_SEED]').count(); real_web=Textbook.objects.filter(description__startswith='[REAL_WEB_').count(); print('total=', total, 'open_data=', open_data, 'auto_seed=', seeded, 'real_web=', real_web)"

# 5) 统计演示订单补数（跨月 completed/cancelled）
python manage.py seed_stats_orders
# 管理端统计页推荐参数：覆盖流通率月度趋势、各类别均价趋势、价格指数/环比
python manage.py seed_stats_orders --months 18 --orders-per-month 9 --cancel-every 5
# 说明：若工作区 .venv 缺少 Django，可直接用系统 python 执行（与 start.bat 一致）

# 6) 对 REAL_WEB 扩容数据执行分类纠偏（先预览后写入）
python manage.py reclassify_textbooks --scope real-web --dry-run
python manage.py reclassify_textbooks --scope real-web

# 7) 对 REAL_WEB 扩容数据做中文元数据+真实封面补齐（仅使用公开网站真实数据）
python manage.py localize_real_textbooks --scope real-web --limit 100 --dry-run
python manage.py localize_real_textbooks --scope real-web --limit 300 --sleep-ms 80

# 8) 从公开网站新增中文书（真实封面），并按四个用户轮转分配
python manage.py seed_real_cn_books --count 500 --owners admin,test_user,wenchang,alice --sleep-ms 20
# 若遇外部限流，可开启 broaden 词池重试
python manage.py seed_real_cn_books --count 100 --owners admin,test_user,wenchang,alice --broaden --sleep-ms 20

# 9) 创建演示账号 user1-user20（密码为用户名+123456，例如 user1/user1123456）
python manage.py create_userx_accounts

# 10) 将教材、订单、资料订单均匀重分配给前 24 个活跃用户
python manage.py rebalance_demo_data --users 24
# 仅预览，不写入数据库
python manage.py rebalance_demo_data --users 24 --dry-run

# 11) 历史订单适配（补齐取消原因/取消方，并按历史订单修正教材状态）
python manage.py adapt_legacy_orders --dry-run
python manage.py adapt_legacy_orders
```

**expand_textbooks_real 参数说明:**
- `--multiplier N`: 基于当前总量的倍数扩展（默认4倍）
- `--target-total N`: 指定目标总量（优先级高于 multiplier）
- `--owner-username USERNAME`: 指定新增教材的归属用户，默认admin
- `--dry-run`: 仅预览无需入库

说明：`start.bat` 默认走系统 `python`，不是工作区 `.venv`。

补充说明：
- `localize_real_textbooks` 与 `seed_real_cn_books` 都只使用真实网站返回的封面图片，不会生成虚假封面。
- 公开站点存在限流（例如 418），建议分批多次执行并设置 `--sleep-ms`。

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
| 用户 | `/api/users/` | 注册、登录、个人信息、忘记密码、重置密码 |
| 教材 | `/api/textbooks/` | CRUD、搜索、我的教材、点赞点踩、评论 |
| 资料 | `/api/textbooks/resources/` | 在线资料上传、下载、删除 |
| 我的资料 | `/api/textbooks/resources/my/` | 我的在线资料列表与导出（`export=1`） |
| 订单 | `/api/orders/` | 下单、确认、完成、取消 |
| 消息 | `/api/messages/` | 会话、消息、未读数 |
| 审核 | `/api/reviews/` | 待审列表、审核操作 |
| 推荐 | `/api/recommendations/` | 个性化推荐、热门 |
| 心愿单 | `/api/recommendations/wishlist/` | 心愿单增删改查 |
| 统计 | `/api/statistics/` | 多维统计数据（含热门教材排行、优秀商家评分排行） |
| 评分 | `/api/textbooks/<id>/rating/`、`/api/statistics/seller-ratings/*` | 教材评分、商家评分 |
| 资料订单 | `/api/textbooks/resources/orders/` | 资料订单创建、确认、支付完成、取消 |
| WebSocket | `ws://host/ws/chat/<id>/` | 实时聊天 |

用户主页新增公开接口：
- `/api/users/<id>/textbooks/`：查看该用户发布教材（含在售、已售、已租等状态）

统计模块新增端点示例：
- `/api/statistics/popular-detail/?rank_type=views|orders|comprehensive&limit=15`
- `/api/statistics/top-sellers-rating/?limit=12`
- `/api/statistics/user-insights/?limit=10`（用户端含热门教材与优秀商家评分榜）
- `/api/statistics/fulfillment-insights/`（履约漏斗与平均时效）
- `/api/statistics/cancellation-insights/`（含取消原因分布、取消方占比）

## 测试建议

```bash
cd backend
python manage.py test tests.test_order_and_stats_logic -v 1
```

当前回归覆盖：
- 下单后教材不可重复下单
- 取消订单时若仍有进行中订单，不回架
- 用户漏斗统计口径包含非 `approved` 的自有教材
- 商家评分同用户重复提交应更新
- 教材评分支持创建/更新/取消

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_NAME | textbook_sharing | 数据库名 |
| DB_USER | root | 数据库用户 |
| DB_PASSWORD | root123456 | 数据库密码 |
| DB_HOST | db | 数据库主机 |
| REDIS_HOST | redis | Redis主机 |
| SECRET_KEY | django-secret-key | Django密钥 |
| FRONTEND_URL | http://localhost:3000 | 密码重置邮件里的前端链接前缀 |
| EMAIL_BACKEND | django.core.mail.backends.console.EmailBackend | 邮件后端（开发默认打印到终端） |
| EMAIL_HOST | smtp.qq.com | SMTP 主机 |
| EMAIL_PORT | 587 | SMTP 端口 |
| EMAIL_USE_TLS | 1 | 是否启用 TLS |
| EMAIL_HOST_USER | (空) | SMTP 用户名（发件邮箱） |
| EMAIL_HOST_PASSWORD | (空) | SMTP 授权码 |
| DEFAULT_FROM_EMAIL | noreply@textbook-sharing.local | 默认发件人地址 |
| PASSWORD_RESET_TIMEOUT | 1800 | 重置链接有效期（秒） |

