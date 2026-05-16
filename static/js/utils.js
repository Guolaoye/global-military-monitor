// 工具函数
function formatTime(timestamp) {
    const d = new Date(timestamp);
    return d.toLocaleString('zh-CN');
}

function updateServerTime() {
    document.getElementById('server-time').textContent = formatTime(new Date());
}
setInterval(updateServerTime, 1000);

// API 错误处理
async function apiCall(url, options = {}) {
    try {
        const resp = await fetch(url, options);
        return await resp.json();
    } catch (e) {
        console.error('API调用失败:', e);
        return { success: false, error: e.message };
    }
}
