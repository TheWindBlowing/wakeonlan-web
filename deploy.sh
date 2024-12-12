#!/bin/bash
###
 # @Author: Zhiwei Tao zwtao21@163.com
 # @Date: 2024-12-13 01:52:40
 # @LastEditTime: 2024-12-13 02:06:42
 # @LastEditors: Zhiwei Tao zwtao21@163.com
 # @FilePath: /wakeOnLan/deploy.sh
 # @Description: 
### 

# 配置信息
SERVER="tzw@192.168.20.40"
REMOTE_PATH="/home/tzw/app/wakeOnLan"
PROJECT_NAME="wakeOnLan"

# 打包前清理
echo "清理旧的构建文件..."
rm -f ${PROJECT_NAME}.tar.gz

# 创建临时目录并复制文件
echo "准备文件..."
mkdir -p ${PROJECT_NAME}
cp -r app.py templates static requirements.txt ${PROJECT_NAME}/

# 打包文件
echo "打包项目..."
tar -czf ${PROJECT_NAME}.tar.gz ${PROJECT_NAME}

# 清理临时目录
rm -rf ${PROJECT_NAME}

# 在服务器上创建目录
echo "在服务器上创建目录..."
ssh ${SERVER} "mkdir -p ${REMOTE_PATH}"

# 上传文件
echo "上传文件到服务器..."
scp ${PROJECT_NAME}.tar.gz ${SERVER}:${REMOTE_PATH}/

# 在服务器上解压和设置
echo "在服务器上部署..."
ssh ${SERVER} "cd ${REMOTE_PATH} && \
    tar -xzf ${PROJECT_NAME}.tar.gz && \
    mv ${PROJECT_NAME}/* . && \
    rm -rf ${PROJECT_NAME} ${PROJECT_NAME}.tar.gz && \
    sudo python3 -m venv venv && \
    sudo chown -R root:root venv && \
    sudo venv/bin/pip install -r requirements.txt && \
    echo '# Allow wakeonlan service to run without password
    %root ALL=(ALL) NOPASSWD: ${REMOTE_PATH}/venv/bin/python' | sudo tee /etc/sudoers.d/wakeonlan && \
    sudo chmod 440 /etc/sudoers.d/wakeonlan && \
    sudo chown -R root:root ${REMOTE_PATH}"

# 创建并上传服务文件
echo "创建系统服务..."
cat > wakeonlan.service << EOF
[Unit]
Description=Wake On LAN Web Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${REMOTE_PATH}
Environment="PATH=${REMOTE_PATH}/venv/bin"
ExecStart=/usr/bin/sudo ${REMOTE_PATH}/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 上传服务文件
scp wakeonlan.service ${SERVER}:${REMOTE_PATH}/
ssh ${SERVER} "sudo mv ${REMOTE_PATH}/wakeonlan.service /etc/systemd/system/ && \
    sudo chown -R root:root ${REMOTE_PATH} && \
    sudo chmod 755 ${REMOTE_PATH} && \
    sudo chmod 644 ${REMOTE_PATH}/* && \
    sudo chmod 755 ${REMOTE_PATH}/venv/bin/python && \
    sudo systemctl daemon-reload && \
    sudo systemctl enable wakeonlan && \
    sudo systemctl start wakeonlan"

# 清理本地临时文件
rm -f ${PROJECT_NAME}.tar.gz wakeonlan.service

echo "部署完成！"
echo "服务已启动，可以通过 http://192.168.20.25:5100 访问" 