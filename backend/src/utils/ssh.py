"""
SSH 核心工具模块
=================
提供 WebSocket SSH 实时通信、密钥生成/分发、命令执行、文件传输等核心功能。

模块组成:
    SSHConsumer  — WebSocket 消费者，建立浏览器 ↔ 后端 ↔ SSH 服务器的双向实时通道
    工具函数      — SSH 连接探测、远程命令执行、文件上传/下载、密钥对管理
"""

import json, io, base64, queue, threading, paramiko, time, socket
from channels.generic.websocket import WebsocketConsumer
from apps.host.models import Host


class SSHConsumer(WebsocketConsumer):
    """
    WebSocket SSH 终端消费者
    -------------------------
    生命周期: connect → _start (读写循环) → disconnect

    数据流:
        浏览器 ──WebSocket── 后端 ──paramiko SSH── 远程主机
        - 浏览器按键 → receive() → _to_ssh_q 队列 → _writer() → SSH shell
        - SSH shell 输出 → _reader() → base64 编码 → send() → 浏览器

    编码说明:
        终端输出包含不可见控制字符，使用 base64 编码保证 WebSocket 文本帧可靠传输。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = None           # 目标主机 ORM 对象
        self.ssh = None            # paramiko SSHClient 实例
        self.chan = None           # SSH channel（交互式 shell 会话）
        self._alive = False        # 连接存活标志，用于控制读写循环
        self._to_ssh_q = queue.Queue()  # 线程安全队列：浏览器输入 → SSH

    # ==================== 主线程：WebSocket 握手 ====================

    def connect(self):
        """
        WebSocket 连接建立时的握手流程:
        1. 防止重复连接
        2. 根据 URL 中的 host_id 加载主机信息
        3. 可选 JWT 子协议校验（前端传两个子协议时，第二个为 access token）
        4. 建立 SSH 连接
        5. 启动后台线程进入读写循环
        """
        if self._alive:
            self.disconnect()
        self._alive = True

        # 从 WebSocket 路由中提取主机 ID
        host_id = self.scope['url_route']['kwargs']['host_id']
        try:
            self.host = Host.objects.get(pk=host_id)
        except Host.DoesNotExist:
            self.close(code=3000)
            return

        # 可选的 JWT 子协议校验（subprotocols[1] = access token）
        protocols = self.scope.get('subprotocols', [])
        if len(protocols) >= 2:
            from rest_framework_simplejwt.tokens import AccessToken
            try:
                AccessToken(protocols[1])
            except Exception:
                self.close(code=3003)
                return
        self.accept(subprotocol='jwt' if protocols else None)

        # 建立 SSH 连接，失败则关闭 WebSocket
        ok, msg = self._open_ssh()
        if not ok:
            print("SSH初始化失败")
            print(json.dumps({'error': msg}))
            self.disconnect(code=3002)
            return

        # 启动后台线程，进入"读取SSH输出 → 转发前端"和"接收前端输入 → 转发SSH"的双向循环
        # daemon=True: 主线程退出时自动回收，防止进程挂住
        threading.Thread(target=self._start, daemon=True).start()

    # ==================== SSH 连接建立 ====================

    def _open_ssh(self):
        """
        使用主机预存的 RSA 私钥建立 SSH 连接并打开交互式 shell。

        流程:
        1. 从数据库加载私钥（PEM 格式字符串），构造 paramiko RSAKey
        2. 连接远程主机（密钥认证）
        3. 打开 session channel，申请 pty（xterm 伪终端）
        4. 启动 bash login shell，关闭 SSH 本地回显（由远程终端自己回显）

        Returns:
            (True, None)  成功
            (False, str)  失败原因
        """
        try:
            # 用数据库中的私钥构造 RSA 密钥对象
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(self.host.private_key))
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动信任未知主机密钥
            ssh.connect(
                hostname=self.host.ip_addr,
                port=int(self.host.port),
                username=self.host.username,
                pkey=pkey,
                timeout=10
            )

            # 打开交互式 shell 会话
            self.chan = ssh.get_transport().open_session()
            self.chan.get_pty(term='xterm', width=80, height=48)  # 申请伪终端
            self.chan.invoke_shell()           # 启动 shell
            self.chan.send('exec bash -l\n')   # 切换为 login shell（加载 .bashrc 等）
            self.chan.send('stty -echo\n')     # 关闭 SSH 本地回显，避免双倍字符
            print(f"SSH初始化成功")
            return True, None
        except Exception as e:
            return False, str(e)

    # ==================== 后台线程：双向转发循环 ====================

    def _start(self):
        """
        后台线程主循环，交替执行读/写操作。

        设计要点:
        - _reader 和 _writer 各自设置 0.01s 超时，交替执行而非阻塞等待
        - 任一方向失败都将 _alive 置 False，触发断开
        - finally 块保证无论正常/异常退出都执行 disconnect 清理资源
        """
        try:
            while self._alive:
                self._reader()   # SSH → 浏览器
                self._writer()   # 浏览器 → SSH
        except Exception as e:
            raise RuntimeError(f"error:{e}")
        finally:
            self.disconnect(code=3001)

    # ==================== 数据转发：SSH → 浏览器 ====================

    def _reader(self):
        """
        从 SSH channel 读取终端输出，base64 编码后通过 WebSocket 发送给浏览器。

        设计要点:
        - settimeout(0.01): 非阻塞读取，每次最多等 10ms，保证 _writer 也能及时执行
        - recv(4096): 每次最多读取 4KB
        - base64 编码: 终端 ANSI 控制码是二进制，base64 保证 WebSocket 文本帧安全传输
        """
        try:
            self.chan.settimeout(0.01)
            data = self.chan.recv(4096)
            if data:
                # bytes → base64 编码 → UTF-8 字符串 → WebSocket 文本帧
                text_data = base64.b64encode(data).decode()
                self.send(text_data=text_data)
        except socket.timeout:
            pass  # 超时正常，继续循环
        except Exception as e:
            self._alive = False
            raise RuntimeError("error:_reader数据转发失败", e)

    # ==================== 数据转发：浏览器 → SSH ====================

    def _writer(self):
        """
        从队列取出浏览器发来的按键数据，解码后写入 SSH channel。

        设计要点:
        - Queue.get(timeout=0.01): 非阻塞出队，保证 _reader 也能及时执行
        - 自动追加换行符（\\n），模拟终端回车行为
        - 收到 "exit\\n" 时优雅关闭连接
        """
        try:
            msg = self._to_ssh_q.get(timeout=0.01)
            if msg:
                raw = base64.b64decode(msg)        # base64 文本 → bytes
                if not raw.endswith((b'\r', b'\n')):  # 确保末尾有换行
                    raw += b'\n'
                if raw == b'exit\n':
                    self._alive = False             # 收到 exit 命令，结束循环
                else:
                    self.chan.sendall(raw)
        except queue.Empty:
            pass  # 队列空正常，继续循环
        except Exception as e:
            self._alive = False
            raise RuntimeError("error:_writer数据转发失败", e)

    # ==================== 主线程回调：接收浏览器消息 ====================

    def receive(self, text_data=None, bytes_data=None):
        """
        Django Channels 框架回调（主线程），浏览器每发来一个 WebSocket 帧就触发。
        仅负责把数据放入队列，不做耗时操作以避免阻塞主线程。
        """
        try:
            payload = text_data or bytes_data.decode()
            self._to_ssh_q.put(payload)
        except Exception:
            self.disconnect(code=3001)

    # ==================== 断开与清理 ====================

    def disconnect(self, code):
        """
        关闭 WebSocket 连接并释放所有 SSH 资源。

        关闭顺序:
        1. 置 _alive=False，终止后台线程的读写循环
        2. 关闭 SSH channel
        3. 关闭 SSH 连接
        4. 关闭 WebSocket
        """
        self._alive = False
        if getattr(self, 'chan', None):
            self.chan.close()
        if getattr(self, 'ssh', None):
            self.ssh.close()
        self.close(code=code)


# ==================== 密钥管理工具函数 ====================

def generate_key_pair() -> tuple[str, str]:
    """
    生成 RSA 2048 位密钥对，用于 SSH 免密登录。

    Returns:
        tuple[str, str]: (私钥 PEM 字符串, 公钥 OpenSSH 格式字符串)

    Raises:
        RuntimeError: 密钥生成失败时抛出

    使用场景:
        新增主机时自动生成密钥对，私钥存入数据库，公钥推送到远程主机。
    """
    try:
        key = paramiko.RSAKey.generate(2048)

        # --- 私钥：PEM 格式 ---
        private_io = io.StringIO()
        key.write_private_key(private_io)   # paramiko 原生方法，写入 PEM
        private_io.seek(0)
        private = private_io.read()

        # --- 公钥：OpenSSH authorized_keys 格式 ---
        # 格式: "ssh-rsa <base64编码的密钥体> <注释>"
        public = f"{key.get_name()} {key.get_base64()} generated@web-ssh\n"
        return private, public
    except Exception as e:
        raise RuntimeError(f'密钥对生成失败：{e}')


def push_public_key(host_info):
    """
    将生成的公钥推送到远程主机的 ~/.ssh/authorized_keys。

    使用密码认证临时连接远程主机，执行以下操作:
    1. mkdir -p -m 700 ~/.ssh        # 确保 .ssh 目录存在且仅 owner 可读写
    2. echo public_key >> authorized_keys  # 追加公钥
    3. chmod 600 authorized_keys     # 设置正确权限（否则 SSH 会拒绝）

    Args:
        host_info: dict，包含 ip_addr, port, username, connect_pwd, public_key

    Raises:
        RuntimeError: 公钥推送失败时抛出
    """
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=host_info.get('ip_addr'),
            port=int(host_info.get('port')),
            username=host_info.get('username'),
            password=host_info.get('connect_pwd')  # 用密码临时认证
        )
        ssh.exec_command('mkdir -p -m 700 ~/.ssh')
        cmd = f'echo {host_info.get("public_key").strip()} >> ~/.ssh/authorized_keys'
        ssh.exec_command(cmd)
        ssh.exec_command('chmod 600 ~/.ssh/authorized_keys')
        print("公钥已上传至远端SSH服务器")
    except Exception as e:
        raise RuntimeError(f'公钥推送失败：{e}')
    finally:
        if ssh:
            ssh.close()


# ==================== SSH 连接与命令执行工具函数 ====================

def probe_ssh_connect(ip_addr, port, username, password=None, pkey_pem=None, timeout=5):
    """
    探测 SSH 连接是否可用（仅连接并立即断开，不执行任何操作）。

    认证优先级: 密钥 > 密码（二者可同时提供，密钥优先尝试）

    Args:
        ip_addr:   远程主机 IP
        port:      SSH 端口
        username:  登录用户名
        password:  密码（可选）
        pkey_pem:  PEM 格式私钥字符串（可选）
        timeout:   连接超时秒数

    Returns:
        None  连接成功
        str   错误描述字符串（连接失败时）
    """
    ssh = None
    try:
        key = None
        if pkey_pem:
            key = paramiko.RSAKey.from_private_key(io.StringIO(pkey_pem))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=ip_addr,
            port=int(port),
            username=username,
            password=password,
            pkey=key,
            timeout=timeout,
            allow_agent=False,     # 禁用 SSH agent 转发
            look_for_keys=False    # 禁用本地密钥搜索
        )
        print('远程服务器连接测试成功')
        return None
    except Exception as e:
        return str(e)
    finally:
        if ssh:
            ssh.close()


def exec_cmd(host_info=None, cmd=None, timeout=5):
    """
    在远程主机上执行单条命令并返回输出。

    通过 paramiko 建立 SSH 连接，使用 exec_command 执行命令。

    Args:
        host_info: dict，包含 ip_addr, port, username, private_key
        cmd:       要执行的 shell 命令字符串
        timeout:   SSH 连接超时秒数

    Returns:
        str: 命令的 stdout 输出

    Raises:
        RuntimeError: SSH 连接失败、命令执行超时或执行出错时抛出

    超时策略:
        命令执行最多等待 1 秒（recv_exit_status），超过则抛 RuntimeError。
    """
    ssh = None
    try:
        key_raw = host_info.get('private_key')
        pkey = None
        if key_raw:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_raw))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=host_info.get('ip_addr'),
            port=int(host_info.get('port')),
            username=host_info.get('username'),
            pkey=pkey,
            timeout=timeout
        )
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.settimeout(1)       # 最大等待 1 秒
        try:
            stdout.channel.recv_exit_status()  # 阻塞等待命令结束
        except socket.timeout:
            raise RuntimeError('命令执行超时(>1s)')

        # 检查 stderr 是否有错误输出
        err_output = stderr.read().decode()
        if err_output:
            raise RuntimeError(f'命令执行出错: {err_output.strip()}')

        return stdout.read().decode()
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f'SSH 命令执行失败: {e}')
    finally:
        if ssh:
            ssh.close()


# ==================== 文件传输工具函数 ====================

def upload_file(host_info=None, file_obj=None, remote_path=None, filename=None, timeout=5):
    """
    通过 SFTP 上传文件到远程主机。

    使用 paramiko SSH 连接 → open_sftp() → 分块写入远程文件。
    分块大小 64KB，避免大文件一次性加载到内存。

    Args:
        host_info:   dict，包含 ip_addr, port, username, private_key
        file_obj:    Django UploadedFile 对象（支持 .chunks() 迭代）
        remote_path: 远程目标目录路径
        filename:    远程文件名
        timeout:     SSH 连接超时秒数

    Raises:
        RuntimeError: 上传失败时抛出
    """
    ssh = None
    sftp = None
    try:
        key_raw = host_info.get('private_key')
        pkey = None
        if key_raw:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_raw))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=host_info.get('ip_addr'),
            port=int(host_info.get('port')),
            username=host_info.get('username'),
            pkey=pkey,
            timeout=timeout
        )
        sftp = ssh.open_sftp()
        # 分块写入，每次最多 64KB 在内存中
        with sftp.open(f'{remote_path}/{filename}', 'wb') as f:
            for chunk in file_obj.chunks(chunk_size=64 * 1024):
                f.write(chunk)
    except Exception as e:
        raise RuntimeError(f'文件上传失败: {e}')
    finally:
        if sftp:
            sftp.close()
        if ssh:
            ssh.close()


def download_file(host_info=None, remote_path=None, filename=None, timeout=5):
    """
    通过 SFTP 从远程主机下载文件。

    将远程文件一次性读入内存 BytesIO，返回文件对象和大小。

    Args:
        host_info:   dict，包含 ip_addr, port, username, private_key
        remote_path: 远程文件所在目录
        filename:    远程文件名
        timeout:     SSH 连接超时秒数

    Returns:
        tuple: (BytesIO 文件对象, int 文件大小字节数)

    Raises:
        RuntimeError: 文件不存在或下载失败时抛出
    """
    ssh = None
    try:
        key_raw = host_info.get('private_key')
        pkey = None
        if key_raw:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_raw))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=host_info.get('ip_addr'),
            port=int(host_info.get('port')),
            username=host_info.get('username'),
            pkey=pkey,
            timeout=timeout
        )
        with ssh.open_sftp() as sftp:
            with sftp.file(f'{remote_path}/{filename}', 'rb') as f:
                file = io.BytesIO(f.read())  # 一次性读入内存
                file_size = sftp.stat(f'{remote_path}/{filename}').st_size
        return file, file_size
    except FileNotFoundError:
        raise RuntimeError(f'文件不存在: {remote_path}/{filename}')
    except Exception as e:
        raise RuntimeError(f'文件下载失败: {e}')
    finally:
        if ssh:
            ssh.close()
