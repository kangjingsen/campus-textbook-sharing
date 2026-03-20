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
│   │   ├── recommendations/# 推荐系统 (协同过滤 + 内容推荐)
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
- **Python**: 3.8.0（本机安装路径）
- **Node.js**: v24.14.0, npm 11.9.0
- **MySQL**: 8.0.37（本机安装路径），配置文件（本机实际 my.ini 路径）
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
- **SharedResource**: title, description, file(FileField → resources/), file_size, resource_type(pdf/doc/ppt/other), `sale_type`(free/sell), `price`, category(FK), uploader(FK), download_count
- **ResourceOrder**: resource(FK), buyer(FK), seller(FK), price, status(pending/confirmed/paid_pending/completed/cancelled), payment_qr, payment_qr_image, payment_proof, confirmed_at, paid_at, completed_at
- **Order**: order_no(自动生成), textbook(FK), buyer(FK), seller(FK), price, status, transaction_type, `started_at`, completed_at
- **TextbookCreateView** 使用 `MultiPartParser, FormParser`（非 JSON）

## 主要 API 端点
- 用户：/api/users/register/, /api/users/login/, /api/users/token/refresh/, /api/users/forgot-password/, /api/users/reset-password/, /api/users/profile/, /api/users/change-password/, /api/users/{id}/ (AllowAny, 公开主页)
- 教材：/api/textbooks/, /api/textbooks/create/, /api/textbooks/search/, /api/textbooks/{id}/, /api/textbooks/my/, /api/textbooks/categories/tree/
- 管理员删除：/api/textbooks/admin/{id}/delete/
- 点赞点踩：/api/textbooks/{id}/vote/ (GET 统计+我的投票, POST 切换)
- 评论：/api/textbooks/{id}/comments/ (GET 列表, POST 发布), /api/textbooks/comments/{id}/delete/
- 在线资料：/api/textbooks/resources/ (GET 列表, POST 上传), /api/textbooks/resources/{id}/ (GET 详情, DELETE 删除), /api/textbooks/resources/{id}/download/ (POST 授权下载)
- 资料订单：/api/textbooks/resources/orders/create/, /api/textbooks/resources/orders/, /api/textbooks/resources/orders/{id}/confirm|complete|seller-complete|cancel/
- 教材订单：/api/orders/create/, /api/orders/, /api/orders/{id}/confirm|complete|cancel|return/
- 审核：/api/reviews/pending/, /api/reviews/action/{id}/, /api/reviews/sensitive-words/
- 心愿单：/api/recommendations/wishlist/, /api/recommendations/wishlist/{id}/
- 统计增强：/api/statistics/sales-ranking/, /api/statistics/demand-ranking/, /api/statistics/top-sellers/, /api/statistics/price-metrics/, /api/statistics/wishlist-demand/, /api/statistics/cancellation-insights/

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
- **心愿单系统**: 新增 `WishlistItem` 模型与 `/api/recommendations/wishlist/` 接口，支持新增/编辑/删除/状态管理，并接入推荐算法权重
- **推荐实时刷新**: 心愿单增删改会触发推荐缓存刷新（signals）；首页全局事件监听自动更新推荐列表
- **推荐刷新防缓存滞后**: `/api/recommendations/` 新增 `refresh=1` 强制实时重算；首页在心愿单变更后使用强制刷新参数拉取推荐
- **推荐候选过滤增强**: 推荐结果统一排除用户本人发布教材，仅保留 `approved` 状态教材，避免推荐名额被无效候选占用
- **心愿匹配增强**: 心愿词支持标题/作者/ISBN/出版社/描述多字段匹配，并增加规范化与分段模糊匹配，提升“大学生体质与健康”这类书名的命中率
- **在线资料售卖**: `SharedResource` 新增 `sale_type/price`，新增 `ResourceOrder` 资料订单，支持卖家确认并填写支付二维码，买家确认支付后开放下载
- **资料支付二维码图片**: `ResourceOrder` 新增 `payment_qr_image`，卖家确认资料订单时可直接上传二维码图片，买家可直接查看图片支付
- **订单提醒角标**: 导航栏"我的订单"与订单页新增待处理订单提醒（轮询统计卖家待确认订单）
- **忘记密码流程**: 新增 `/api/users/forgot-password/` 与 `/api/users/reset-password/`，通过邮箱重置链接设置新密码
- **线下交易自动完成**: `Order` 新增 `started_at`，确认后超过 3 天自动完成（在订单查询时触发）
- **统计增强（仪表盘）**: 新增售卖排行榜、需求排行榜、优秀商家、取消订单专题分析、价格指标（指数/环比/同比/中位数/最大最小/均值）
- **用户统计接口**: 新增 `/api/statistics/user-insights/` 返回用户个人概览(总教材数/在架数/积压数/成交额)、积压排行(在架天数/浏览量/积压分)、需求排行(心愿数/订单数/需求分)
- **用户统计页面**: 新页面 `UserStatistics.vue`（路由 `/statistics`），支持勾选显示[概览/积压/需求]、设置查看数量(5-30)
- **管理员统计页面统一筛选**: 后台 `Statistics.vue` 新增统一筛选下拉框，快速跳转到各个统计图表，改善用户体验
- **教材批量导入导出**: 新增 `TextbookBulkImportView`/`TextbookBulkExportView`，支持 CSV/XLSX 格式；前端集成client-side CSV生成(后端route返回404时自动回退)；我的教材页面集成导入/导出按钮
- **论坛与公告模块**: 新增 `apps.community`，包含 `Announcement`(标题/摘要/内容/置顶)、`ForumTopic`(讨论/问答/浏览计数)、`ForumReply`(最佳回答标记) 三个模型；新页面 `Forum.vue`(路由 `/forum`)提供完整社区 UI，支持帖子创建/回复/最佳回答标记
- **首页集成**: 首页新增公告资讯和论坛热帖展示区块，导航栏新增论坛和统计分析入口，心愿单更新时自动刷新推荐列表
- **后台公告管理**: 新增公告管理端点 `/api/community/announcements/manage/`，管理员可新增/编辑/删除公告和帖子

## 运行补充说明
- `start.bat` 使用系统默认 `python` 启动后端（不是工作区 `.venv`）。
- 若在 `.venv` 里执行 `manage.py`，需先安装 `backend/requirements.txt`，否则会出现 `No module named 'django'`。
- 本地默认邮件后端为 console（重置邮件打印到后端终端）；配置 SMTP 环境变量后可真实发信。
- 教材数据补齐命令：`python manage.py seed_textbooks --per-category 10`
- 教材公开数据回填命令：`python manage.py enrich_textbooks_open_data --only-seeded`

## 待完成事项
- [ ] 论文测试部分（黑盒测试、白盒测试、性能测试、可用性测试）
  - 工具：Postman、Selenium、JMeter 5.6、pytest+coverage
- [ ] 清理 Docker 相关文件（docker-compose.yml, Dockerfile 等）
