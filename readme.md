# 🚀 Web SSH — 基于浏览器的远程服务器管理平台

一个具有完整鉴权机制的 Web SSH 管理系统，通过浏览器即可远程连接和管理多台 Linux 服务器。支持终端实时交互、文件管理、用户权限控制和资产分配。

---

## 📑 目录

- [核心特性](#-核心特性)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
  - [前置条件](#1-前置条件)
  - [Docker 基础设施部署](#2-docker-基础设施部署)
  - [后端服务部署](#3-后端服务部署)
  - [前端服务部署](#4-前端服务部署)
  - [启动项目](#5-启动项目)
- [使用指南](#-使用指南)
- [配置说明](#-配置说明)
- [API 接口概览](#-api-接口概览)
- [开发路线图](#-开发路线图)
- [免责声明](#-免责声明)

---

## ✨ 核心特性

- 🔐 **JWT 鉴权体系** — 基于 `simplejwt` 的 Token 认证，支持 access/refresh 双令牌自动续期
- 👥 **RBAC 权限管理** — 四级权限层级（超级管理员 / 管理员 / 普通用户 / 只读用户），精细化控制用户操作
- 🖥️ **Web SSH 终端** — 基于 `xterm.js` + WebSocket 的浏览器终端，支持实时命令交互
- 🗂️ **远程文件管理** — 内置 SFTP 文件管理器，支持目录浏览、文件上传/下载、创建文件夹和删除
- 🔑 **SSH 密钥自动管理** — 新增主机时自动生成 RSA 密钥对，自动推送公钥至目标服务器
- 📊 **资产管理** — 主机 CRUD 管理，支持按类别分组（数据库服务器、Web 服务器等）
- 🎯 **资源分配** — 灵活将主机资源分配给指定用户，实现租户隔离
- 🔧 **连接修复** — 容器/虚拟机重建后一键修复 SSH 连接（重新推送公钥）
- 📡 **在线探测** — 选择主机时自动发起 SSH 连接探测，实时显示主机在线/离线状态
- 🐳 **Docker 化部署** — 完整的 Docker Compose 编排，一键启动 SSH 靶机（默认使用 SQLite + 内存通道层，无需 MySQL/Redis）
- 🎨 **响应式布局** — 自适应窗口宽度，≤ 1000px 自动折叠侧栏，窄屏隐藏标题和面包屑
- 🌐 **中文本地化** — 全局 Ant Design 中文配置，穿梭框、表格、弹窗等组件完整汉化
- 🖼️ **用户头像** — 支持上传自定义头像，无头像时按角色显示不同渐变默认头像

---

## 📦 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.5 | 前端框架 |
| Vite | ^7.0 | 构建工具 |
| Ant Design Vue | ^4.2 | UI 组件库 |
| Vue Router | ^4.4 | 路由管理 |
| Pinia | ^3.0 | 状态管理 |
| Axios | ^1.7 | HTTP 客户端 |
| xterm.js | ^5.5 | 终端模拟器 |
| xterm-addon-fit | ^0.8 | 终端自适应插件 |
| jwt-decode | ^4.0 | JWT 解析 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Django | 6.0 | Web 框架 |
| Django Channels | 4.3 | WebSocket 通信 |
| Django REST Framework | 3.16 | REST API |
| simplejwt | 5.5 | JWT 认证 |
| Paramiko | 4.0 | SSH/SFTP 客户端 |
| Daphne | 4.0 | ASGI 服务器 |
| django-cors-headers | 4.3 | 跨域处理 |
| django-filter | 25.2 | 查询过滤 |
| Pillow | 12.2 | 图片处理（头像） |

### 基础设施

| 技术 | 用途 |
|------|------|
| Docker / Docker Compose | 容器化部署（仅 SSH 靶机） |
| SQLite | 持久化数据库（默认） |
| InMemoryChannelLayer | WebSocket 消息队列（默认，内存） |

---

## 📁 项目结构

```
web_ssh/
├── backend/                        # Django 后端
│   ├── manage.py                   # Django 管理入口
│   ├── requirements.txt            # Python 依赖
│   └── src/
│       ├── asgi.py                 # ASGI 配置 (HTTP + WebSocket)
│       ├── settings/
│       │   ├── base.py             # 基础配置 (SQLite + 内存缓存兜底)
│       │   └── dev.py              # 开发环境配置 (SQLite/内存/JWT，MySQL/Redis 已注释备用)
│       ├── apps/
│       │   ├── host/               # 主机管理应用
│       │   │   ├── models.py       # Host, HostCategory 模型
│       │   │   ├── views.py        # 主机 CRUD + 文件操作接口
│       │   │   └── serializers.py  # 序列化器 (含自动密钥生成)
│       │   └── user/               # 用户管理应用
│       │       ├── models.py       # 自定义 User 模型
│       │       ├── views.py        # 用户 CRUD + 注册接口
│       │       └── authentication.py  # 手机号/用户名双模式登录
│       └── utils/
│           ├── ssh.py              # SSH 核心逻辑 (WebSocket Consumer + SFTP)
│           ├── permissions.py      # 四级权限类
│           ├── exceptions.py       # 统一异常处理
│           └── middleware.py       # 访问日志中间件
│
├── frontend/                       # Vue 3 前端
│   └── src/
│       ├── views/
│       │   ├── Home.vue            # SSH 终端主界面（展示大厅）
│       │   ├── Host.vue            # 资产管理 + 分类管理（合并）
│       │   ├── User.vue            # 用户管理页
│       │   ├── Allocation.vue      # 资源分配页
│       │   ├── Login.vue           # 登录页
│       │   ├── Register.vue        # 注册页
│       │   └── Test.vue            # 测试/预留页
│       ├── components/
│       │   ├── FileManager.vue     # 远程文件管理器
│       │   └── FileUpload.vue      # 文件上传组件
│       ├── stores/auth.js          # Pinia 认证状态管理
│       ├── http/index.js           # Axios 封装 (拦截器 + Token 刷新)
│       └── router/index.js         # 路由守卫
│
├── docker/                         # Docker 基础设施
│   ├── build/
│   │   ├── docker-compose.yaml     # 容器编排 (4×SSH)
│   │   └── Dockerfile              # ubuntu-ssh 镜像构建
│
└── assets/                         # 文档截图
```

---

## 🚀 快速开始

### 1. 前置条件

| 依赖 | 说明 |
|------|------|
| **Docker / Docker Desktop** | 运行 SSH 靶机容器（可选，SQLite + 内存通道层无需 Docker） |
| **Node.js** (推荐 v18+) | 前端构建 |
| **Python** (推荐 3.12+) | 后端运行 |
| **uv** | Python 包管理器 |
| **WSL 2** (v2.6+) | ⚠️ 仅 Windows 用户需要 |

#### Windows 用户 — 安装 WSL 2

确保系统版本 ≥ 19041，并在"控制面板 → 启用或关闭 Windows 功能"中开启"虚拟机平台"。

```powershell
# 管理员 PowerShell
wsl --install                        # 全新安装（附带 Ubuntu）
wsl --set-default-version 2          # 设 WSL2 为默认
wsl --update --web-download          # 强制更新到最新内核 (2.6+)
```

---

### 2. Docker 基础设施部署

构建 SSH 镜像并启动所有服务容器：

```bash
cd docker/build

# 构建 ubuntu-ssh 镜像
docker build -t ubuntu-ssh:latest .

# 启动 SSH 容器（默认使用 SQLite + 内存通道层，无需 MySQL/Redis）
docker compose up -d
```

启动后可用端口：

| 服务 | 端口 | 说明 |
|------|------|------|
| Ubuntu SSH #1 | 10021 | SSH 靶机 |
| Ubuntu SSH #2 | 10022 | SSH 靶机 |
| Ubuntu SSH #3 | 10023 | SSH 靶机 |
| Ubuntu SSH #4 | 10024 | SSH 靶机 |

SSH 容器内置账户（见dockerfile）：

| 用户名 | 密码 | 权限 |
|--------|------|------|
| `root` | `123456` | 管理员 |
| `visitor` | `VisitorPass123` | 普通用户 |

---

### 3. 后端服务部署

```bash
cd backend

# 安装 Python 依赖（使用 uv）
uv sync

# 数据库迁移
uv run python manage.py makemigrations
uv run python manage.py migrate

# 创建超级管理员账户（这是登录平台的唯一账户）
uv run python manage.py createsuperuser

# 启动后端开发服务器 → http://127.0.0.1:8000
uv run python manage.py runserver
```

Django Admin 管理后台：[http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

### 4. 前端服务部署

```bash
cd frontend

# 安装依赖
npm install

# 启动前端开发服务器 → http://localhost:5173
npm run dev
```

---

### 5. 启动项目

确保两个终端服务均已启动：

- **终端 1** — 前端 Vite 开发服务器 → `http://localhost:5173`
- **终端 2** — 后端 Django 服务器 → `http://127.0.0.1:8000`

在浏览器访问 `http://localhost:5173/`，使用创建的超级管理员账号登录。

---

## 📖 使用指南

登录后的典型操作流程：

1. **👥 用户管理** — 创建新用户，设置权限角色，上传头像
2. **🖥️ 资产管理** — 新增 SSH 主机（填写 IP、端口、用户名和密码），支持接入 Docker 部署的 Ubuntu 容器或任意可连通的 SSH 服务器。内置分类管理，便于按类别组织资产
3. **🔗 资源分配** — 将主机资源分配给指定用户，控制访问权限
4. **💻 终端操作** — 在"展示大厅"中选择已分配的主机，进入 Web SSH 终端执行命令，使用文件管理器上传/下载文件

> 💡 **提示**：分类管理已合并至资产管理页面，点击"管理分类"按钮即可操作。

### 权限层级

| 角色 | 权限范围 |
|------|----------|
| **超级管理员** (is_superuser) | 全部权限，可管理所有资源和用户 |
| **管理员** (is_staff) | 可管理普通用户，不可修改其他管理员和超级用户 |
| **普通用户** (is_active) | 可访问已分配的主机，执行终端和文件操作 |
| **只读用户** (is_active_readonly) | 仅可查看已分配的资源，不可修改 |

---

## ⚙️ 配置说明

### 默认配置：SQLite + 内存通道层

开发环境默认使用 **SQLite** 数据库和 **内存通道层**，无需安装 MySQL/Redis，开箱即用。

### 切换至 MySQL + Redis

如需使用 MySQL 和 Redis，在 `dev.py` 中取消注释对应的配置块，并注释掉 SQLite/内存配置即可。MySQL 环境变量：

| 环境变量      | 默认值      | 说明                   |
| ------------- | ----------- | ---------------------- |
| `DB_NAME`     | `web_ssh`   | 数据库名（需提前创建） |
| `DB_USER`     | `root`      | 数据库用户名           |
| `DB_PASSWORD` | `123456`    | 数据库密码             |
| `DB_HOST`     | `127.0.0.1` | 数据库地址             |
| `DB_PORT`     | `3306`      | 数据库端口             |

Redis 连接地址在 `dev.py` 注释中的 `CHANNEL_LAYERS` 的 `hosts` 字段修改。

---

## 🔌 API 接口概览

### 认证接口

| 方法 | 端点              | 说明              |
| ---- | ----------------- | ----------------- |
| POST | `/token/obtain/`  | 登录获取 Token    |
| POST | `/token/refresh/` | 刷新 Access Token |
| POST | `/token/verify/`  | 校验 Token 有效性 |

### 用户管理 `/user/`

| 方法           | 端点                       | 说明                   |
| -------------- | -------------------------- | ---------------------- |
| POST           | `/user/register/`          | 用户注册（无需认证）   |
| GET/POST       | `/user/users/`             | 用户列表 / 创建        |
| GET/PUT/DELETE | `/user/users/{id}/`        | 用户详情 / 更新 / 删除 |
| POST           | `/user/users/{id}/avatar/` | 上传用户头像           |

### 主机管理 `/host/`

| 方法           | 端点                       | 说明                        |
| -------------- | -------------------------- | --------------------------- |
| GET/POST       | `/host/hosts/`             | 主机列表 / 新增             |
| GET/PUT/DELETE | `/host/hosts/{id}/`        | 主机详情 / 更新 / 删除      |
| POST           | `/host/hosts/{id}/repair/` | 修复 SSH 连接               |
| POST           | `/host/hosts/{id}/probe/`  | 探测主机在线状态            |
| GET/POST       | `/host/category/`          | 分类列表 / 新增             |
| POST           | `/host/{dev_id}/file/`     | 文件操作（pwd/ls/rm/mkdir） |
| POST           | `/host/{dev_id}/upload/`   | 文件上传                    |
| POST           | `/host/{dev_id}/download/` | 文件下载                    |

### WebSocket

| 协议      | 端点                | 说明             |
| --------- | ------------------- | ---------------- |
| WebSocket | `ws/ssh/{host_id}/` | SSH 终端实时通信 |

---

## 🗺️ 开发路线图

- [x] **用户头像** — 支持头像上传与角色默认头像
- [x] **在线探测** — 选择主机时实时检测 SSH 在线状态
- [x] **分类管理** — 合并至资产管理页，弹窗操作
- [ ] **批量执行** — 支持在多台主机上批量运行 Shell 脚本
- [ ] **定时任务** — 支持在指定时间自动运行预设脚本
- [ ] **操作审计** — 记录所有 SSH 操作日志，支持回放
- [ ] **多因子认证** — 增加 TOTP/短信验证码二次验证
- [ ] **生产环境配置** — 完善 `prod.py` 生产部署配置

---

## ⚠️ 免责声明

本项目为学习项目，仅供学习交流使用。**禁止用于商业用途或其他非法目的。**

- 请勿将本系统部署于生产环境或用于管理生产服务器
- 使用者应对自身操作行为负责，因不合理操作造成的任何财产损失，本项目概不负责
- 请遵守所在国家/地区的法律法规，未经授权不得连接他人服务器

---

## 📄 License

MIT License — 仅供学习交流。
