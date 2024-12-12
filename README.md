<!--
 * @Author: Zhiwei Tao zwtao21@163.com
 * @Date: 2024-12-13 02:54:25
 * @LastEditTime: 2024-12-13 03:05:03
 * @LastEditors: Zhiwei Tao zwtao21@163.com
 * @FilePath: /wakeOnLan/README.md
 * @Description: 
-->
# Wake On LAN Web Service

一个基于 Web 的网络设备扫描和远程唤醒工具。

## 功能特点

- 网络设备扫描
  - 支持 CIDR 格式的网段扫描
  - 自动识别设备主机名、IP 地址和 MAC 地址
  - 多平台网络接口自适应
- 远程唤醒 (WOL)
  - 支持通过 MAC 地址远程唤醒设备
  - 广播魔术包唤醒
- 历史记录管理
  - 保存扫描历史
  - 设备信息自动更新
- 跨平台支持
  - Linux
  - macOS
  - Windows

## 技术栈

- 后端
  - Python 3.9+
  - Flask
  - SQLite
  - Scapy
- 前端
  - HTML5
  - CSS3
  - JavaScript

## 安装部署

### 环境要求

- Python 3.9 或更高版本
- pip 包管理器
- 系统管理员权限（用于网络扫描）

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/TheWindBlowing/wakeonlan-web.git
cd wakeonlan-web
```

2. 创建并编辑配置文件
```bash
cp config.example.ini config.ini
# 根据实际环境修改配置文件
```

3. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖包
pip install -r requirements.txt
```

4. 运行服务
```bash
# 需要管理员权限
sudo python app.py
```

### 系统服务部署（Linux）

1. 修改 deploy.sh 中的配置
```bash
# 编辑 deploy.sh，设置以下变量
SERVER="user@your-server"  # 服务器用户名和地址
REMOTE_PATH="/path/to/app" # 应用部署路径
```

2. 执行部署脚本
```bash
chmod +x deploy.sh
./deploy.sh
```

## 配置说明

配置文件 `config.ini` 包含以下主要设置：

```ini
[Server]
host = 0.0.0.0  # 监听地址
port = 5100     # 监听端口
debug = false   # 调试模式

[Platform]
# 可选值: linux, windows, mac
system = linux  # 运行平台
# 网络接口优先级列表
linux_interfaces = eth0,ens33,enp0s3,wlan0,wlp2s0
mac_interfaces = en0,en1,bridge0,lo0
windows_interfaces = Ethernet,"Wi-Fi"

[Database]
path = /path/to/database.db  # 数据库文件路径

[Logging]
log_path = /path/to/app.log  # 日志文件路径
log_level = INFO             # 日志级别
max_bytes = 1048576         # 日志文件大小限制
backup_count = 5            # 日志文件备份数量
```

## 使用说明

1. 访问 Web 界面
   - 打开浏览器访问 `http://your-server:5100`

2. 扫描网络设备
   - 在输入框中输入要扫描的网段（CIDR 格式，如：192.168.1.0/24）
   - 点击"扫描"按钮开始扫描
   - 等待扫描完成，结果会显示在设备列表中

3. 远程唤醒
   - 在设备列表中找到要唤醒的设备
   - 点击对应的"唤醒"按钮
   - 系统会发送魔术包唤醒目标设备

## 项目结构
```
wakeonlan-web/
├── app.py              # 主程序
├── config.ini          # 配置文件
├── requirements.txt    # 依赖列表
├── deploy.sh          # 部署脚本
├── static/            # 静态文件
│   ├── css/          # 样式文件
│   └── js/           # JavaScript 文件
├── templates/         # HTML 模板
└── logs/             # 日志目录
```

## 开发指南

1. Fork 项目
2. 创建功能分支
```bash
git checkout -b feature/your-feature
```

3. 提交代码
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature
```

4. 创建 Pull Request
   - 在 GitHub 上创建 PR
   - 等待代码审查
   - 合并到主分支

## 安全说明

- 本工具需要管理员权限才能运行
- 建议在受信任的内部网络中使用
- 请勿在生产环境中启用调试模式
- 确保正确设置文件和目录权限

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 作者

- Zhiwei Tao

## 更新日志

### v1.0.0 (2024-12-13)
- 初始版本发布
- 支持网络设备扫描
- 支持远程唤醒功能
- 添加历史记录管理
- 多平台支持

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

感谢所有为本项目做出贡献的开发者。