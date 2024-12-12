function validateCIDR(cidr) {
    // 验证 CIDR 格式
    const parts = cidr.split('/');
    if (parts.length !== 2) return false;

    const ip = parts[0];
    const mask = parseInt(parts[1]);

    // 验证 IP 地址格式
    const ipParts = ip.split('.');
    if (ipParts.length !== 4) return false;

    for (let part of ipParts) {
        const num = parseInt(part);
        if (isNaN(num) || num < 0 || num > 255) return false;
    }

    // 验证掩码长度
    if (isNaN(mask) || mask < 0 || mask > 32) return false;

    return true;
}

// 添加回车键处理函数
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        startScan();
    }
}

function startScan() {
    const networkSegment = document.getElementById('networkSegment').value.trim();
    if (!networkSegment) {
        alert('请输入网段！');
        return;
    }

    if (!validateCIDR(networkSegment)) {
        alert('请输入正确的 CIDR 格式，例如：192.168.1.0/24');
        return;
    }

    // 添加扫描动画
    const scanBtn = document.querySelector('.scan-btn');
    scanBtn.classList.add('scanning');

    fetch('/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ network_segment: networkSegment })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('扫描错误: ' + data.error);
            return;
        }
        loadHistory();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('扫描请求失败，请检查控制台获取详细信息');
    })
    .finally(() => {
        // 移除扫描动画
        scanBtn.classList.remove('scanning');
    });
}

// 添加排序状态对象
let sortState = {
    column: null,  // 当前排序的列
    ascending: true  // 排序方向
};

function loadHistory() {
    fetch('/history')
    .then(response => response.json())
    .then(devices => {
        renderTable(devices);
    })
    .catch(error => console.error('Error:', error));
}

function renderTable(devices) {
    const tbody = document.querySelector('#deviceTable tbody');
    const thead = document.querySelector('#deviceTable thead tr');
    tbody.innerHTML = '';
    
    // 添加排序图标和点击事件到表头
    thead.querySelectorAll('th').forEach((th, index) => {
        if (index === 1 || index === 3) { // IP地址或扫描时间列
            th.classList.add('sortable');
            th.innerHTML = `
                ${th.textContent}
                <span class="sort-icon">
                    <i class="arrow up"></i>
                    <i class="arrow down"></i>
                </span>
            `;
            th.onclick = () => sortTable(index, devices);
        }
    });

    // 渲染数据
    devices.forEach(device => {
        const row = tbody.insertRow();
        row.insertCell(0).textContent = device.hostname;
        row.insertCell(1).textContent = device.ip_address;
        row.insertCell(2).textContent = device.mac_address;
        row.insertCell(3).textContent = device.scan_time;
        row.insertCell(4).textContent = device.network_segment;
        
        const actionCell = row.insertCell(5);
        const wakeButton = document.createElement('button');
        wakeButton.textContent = '网络唤醒';
        wakeButton.onclick = () => wakeDevice(device.mac_address);
        actionCell.appendChild(wakeButton);
    });
}

function sortTable(columnIndex, devices) {
    const thead = document.querySelector('#deviceTable thead tr');
    const th = thead.querySelectorAll('th')[columnIndex];
    
    // 如果点击的是当前排序列，则反转排序方向
    if (sortState.column === columnIndex) {
        sortState.ascending = !sortState.ascending;
    } else {
        sortState.column = columnIndex;
        sortState.ascending = true;
    }
    
    // 更新所有表头的样式
    thead.querySelectorAll('th').forEach(header => {
        header.classList.remove('sort-asc', 'sort-desc');
    });
    
    // 添加当前排序方向的样式
    th.classList.add(sortState.ascending ? 'sort-asc' : 'sort-desc');

    // 根据列类型选择排序方法
    const sortedDevices = [...devices].sort((a, b) => {
        let valueA, valueB;
        
        if (columnIndex === 1) {  // IP地址列
            valueA = ipToNumber(a.ip_address);
            valueB = ipToNumber(b.ip_address);
        } else if (columnIndex === 3) {  // 扫描时间列
            valueA = new Date(a.scan_time);
            valueB = new Date(b.scan_time);
        }
        
        if (valueA < valueB) return sortState.ascending ? -1 : 1;
        if (valueA > valueB) return sortState.ascending ? 1 : -1;
        return 0;
    });

    renderTable(sortedDevices);
}

// 将IP地址转换为数字以便排序
function ipToNumber(ip) {
    return ip.split('.')
        .map((part, index) => parseInt(part) * Math.pow(256, 3 - index))
        .reduce((sum, num) => sum + num, 0);
}

function wakeDevice(macAddress) {
    fetch('/wake', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mac_address: macAddress })
    })
    .then(response => response.json())
    .then(data => {
        alert('网络唤醒命令已发送！');
    })
    .catch(error => console.error('Error:', error));
}

// 页面加载时获取历史记录
window.onload = loadHistory; 