#!/bin/bash
###
 # @Author: Zhiwei Tao zwtao21@163.com
 # @Date: 2024-12-13 01:52:40
 # @LastEditTime: 2024-12-13 02:38:13
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
cp -r app.py templates static requirements.txt config.ini ${PROJECT_NAME}/

# 打包文件
echo "打包项目..."
tar -czf ${PROJECT_NAME}.tar.gz ${PROJECT_NAME}

# 清理临时目录
rm -rf ${PROJECT_NAME}

# 在服务器上创建目录并设置权限
echo "在服务器上创建目录并设置权限..."
ssh ${SERVER} "sudo mkdir -p ${REMOTE_PATH} && \
    sudo chown -R tzw:tzw ${REMOTE_PATH} && \
    sudo chmod -R 755 ${REMOTE_PATH}"

# 上传文件
echo "上传文件到服务器..."
scp ${PROJECT_NAME}.tar.gz ${SERVER}:${REMOTE_PATH}/

# 在服务器上解压和设置
echo "在服务器上部署..."
ssh ${SERVER} "cd ${REMOTE_PATH} && \
    sudo systemctl stop wakeonlan || true && \
    sudo rm -rf venv && \
    sudo rm -f app.py templates/* static/* requirements.txt config.ini && \
    sudo mkdir -p ${REMOTE_PATH}/logs && \
    sudo mkdir -p /etc/wakeonlan && \
    tar -xzf ${PROJECT_NAME}.tar.gz && \
    mv ${PROJECT_NAME}/* . && \
    rm -rf ${PROJECT_NAME} ${PROJECT_NAME}.tar.gz && \
    sudo cp config.ini /etc/wakeonlan/config.ini && \
    sudo chmod 644 /etc/wakeonlan/config.ini && \
    sudo python3 -m venv venv && \
    sudo chown -R root:root venv && \
    sudo venv/bin/pip install -r requirements.txt && \
    sudo chown -R root:root ${REMOTE_PATH} && \
    sudo chmod 755 ${REMOTE_PATH} && \
    sudo chmod 644 ${REMOTE_PATH}/* && \
    sudo chmod 755 ${REMOTE_PATH}/logs && \
    echo '# Allow wakeonlan service to run without password
    %root ALL=(ALL) NOPASSWD: ${REMOTE_PATH}/venv/bin/python' | sudo tee /etc/sudoers.d/wakeonlan && \
    sudo chmod 440 /etc/sudoers.d/wakeonlan"

# 创建并上传服务文件
echo "创建系统服务..."
cat > wakeonlan.service << EOF
[Unit]
Description=Wake On LAN Web Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/home/tzw/app/wakeOnLan
Environment="PATH=/home/tzw/app/wakeOnLan/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/sudo /home/tzw/app/wakeOnLan/venv/bin/python /home/tzw/app/wakeOnLan/app.py
Restart=always
StandardOutput=append:/home/tzw/app/wakeOnLan/logs/wakeonlan.log
StandardError=append:/home/tzw/app/wakeOnLan/logs/wakeonlan.error.log

[Install]
WantedBy=multi-user.target
EOF

# 上传服务文件
scp wakeonlan.service ${SERVER}:${REMOTE_PATH}/
ssh ${SERVER} "cd ${REMOTE_PATH} && \
    sudo systemctl stop wakeonlan || true && \
    sudo mv ${REMOTE_PATH}/wakeonlan.service /etc/systemd/system/ && \
    sudo chown -R root:root ${REMOTE_PATH} && \
    sudo chmod 755 ${REMOTE_PATH} && \
    sudo chmod 644 ${REMOTE_PATH}/* && \
    sudo chmod 755 ${REMOTE_PATH}/venv/bin/python && \
    sudo chmod +x ${REMOTE_PATH}/app.py && \
    sudo systemctl daemon-reload && \
    sudo systemctl enable wakeonlan || true && \
    sudo systemctl start wakeonlan && \
    sleep 2 && \
    sudo systemctl status wakeonlan"

# 清理本地临时文件
rm -f ${PROJECT_NAME}.tar.gz wakeonlan.service

echo "部署完成！"
echo "检查服务状态..."
ssh ${SERVER} "sudo systemctl status wakeonlan"
echo "服务已启动，可以通过 http://192.168.20.40:5100 访问" 