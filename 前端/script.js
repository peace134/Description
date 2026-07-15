// ================================================================
// 1. 页面加载时检查登录状态
// ================================================================
(function checkAuth() {
    if (localStorage.getItem('isLogin') !== 'true') {
        // 如果在主页但未登录，跳转到登录页
        if (window.location.pathname.includes('index.html') || window.location.pathname === '/' || window.location.pathname === '') {
            window.location.href = 'login.html';
        }
        return;
    }

    // 如果在登录/注册页但已登录，跳转到主页
    if (window.location.pathname.includes('login.html') || window.location.pathname.includes('register.html')) {
        window.location.href = 'index.html';
    }

    // 显示当前用户名
    const currentUser = localStorage.getItem('currentUser') || '用户';
    const userDisplay = document.getElementById('userDisplay');
    if (userDisplay) {
        userDisplay.textContent = '👤 ' + currentUser;
    }
})();


// ================================================================
// 2. 粒子背景（全页面通用）
// ================================================================
(function initParticles() {
    const canvas = document.getElementById('particlesCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w, h;
    const particles = [];
    const COUNT = 90;

    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * w;
            this.y = Math.random() * h;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            this.opacity = Math.random() * 0.4 + 0.1;
            this.color = Math.random() > 0.6 ? '246, 184, 61' : '167, 139, 250';
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > w) { this.speedX *= -1; }
            if (this.y < 0 || this.y > h) { this.speedY *= -1; }
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${this.color}, ${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < COUNT; i++) {
        particles.push(new Particle());
    }

    function drawLines() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 160) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    const alpha = 0.06 * (1 - dist / 160);
                    ctx.strokeStyle = `rgba(246, 184, 61, ${alpha})`;
                    ctx.lineWidth = 0.6;
                    ctx.stroke();
                }
            }
        }
    }

    let mouseX = null,
        mouseY = null;
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animate() {
        ctx.clearRect(0, 0, w, h);

        // 鼠标交互：粒子靠近鼠标会散开
        if (mouseX !== null && mouseY !== null) {
            particles.forEach(p => {
                const dx = p.x - mouseX;
                const dy = p.y - mouseY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    const force = (120 - dist) / 120 * 0.5;
                    p.x += (dx / dist) * force;
                    p.y += (dy / dist) * force;
                }
            });
        }

        particles.forEach(p => { p.update();
            p.draw(); });
        drawLines();
        requestAnimationFrame(animate);
    }
    animate();
})();


// ================================================================
// 3. 密码可见性切换（登录/注册通用）
// ================================================================
document.querySelectorAll('.toggle-pwd').forEach(btn => {
    btn.addEventListener('click', function() {
        const input = this.closest('.input-wrap').querySelector('input');
        if (input.type === 'password') {
            input.type = 'text';
            this.textContent = '🙈';
        } else {
            input.type = 'password';
            this.textContent = '👁️';
        }
    });
});


// ================================================================
// 4. 退出登录
// ================================================================
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
        localStorage.removeItem('isLogin');
        localStorage.removeItem('currentUser');
        window.location.href = 'login.html';
    });
}


// ================================================================
// 5. 主页功能（仅当在主页时执行）
// ================================================================
if (document.getElementById('uploadZone')) {

    // ---- DOM 引用 ----
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const uploadContent = document.getElementById('uploadContent');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const resetBtn = document.getElementById('resetBtn');
    const originalPreview = document.getElementById('originalPreview');
    const annotatedPreview = document.getElementById('annotatedPreview');
    const resultCategory = document.getElementById('resultCategory');
    const confidenceBar = document.getElementById('confidenceBar');
    const confidenceText = document.getElementById('confidenceText');
    const recognizeBtn = document.getElementById('recognizeBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    let currentFile = null;
    let currentAnnotatedDataUrl = null;

    // ---- 点击上传 ----
    uploadZone.addEventListener('click', () => fileInput.click());

    // ---- 文件选择 ----
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) handleFile(this.files[0]);
    });

    // ---- 拖拽上传 ----
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // ---- 核心：处理文件 ----
    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('⚠️ 请上传图片文件（JPG / PNG / WebP）');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            alert('⚠️ 文件大小不能超过 10MB');
            return;
        }

        currentFile = file;

        // 显示文件信息
        const sizeKB = (file.size / 1024).toFixed(1);
        const sizeMB = (file.size / 1024 / 1024).toFixed(2);
        fileName.textContent = file.name;
        fileSize.textContent = sizeMB > 1 ? sizeMB + ' MB' : sizeKB + ' KB';
        fileInfo.style.display = 'flex';
        uploadContent.style.display = 'none';

        // 本地预览原图
        const reader = new FileReader();
        reader.onload = function(e) {
            originalPreview.innerHTML = `<img src="${e.target.result}" alt="原图" />`;
        };
        reader.readAsDataURL(file);

        clearResult();
        recognizeBtn.disabled = false;
        downloadBtn.disabled = true;
    }

    // ---- 重置 ----
    resetBtn.addEventListener('click', resetAll);

    function resetAll() {
        currentFile = null;
        currentAnnotatedDataUrl = null;
        fileInput.value = '';
        fileInfo.style.display = 'none';
        uploadContent.style.display = 'block';
        originalPreview.innerHTML = `
                    <div class="placeholder-text">
                        <span class="ph-icon">🖼️</span>
                        <span>暂无图片</span>
                    </div>
                `;
        clearResult();
        recognizeBtn.disabled = true;
        downloadBtn.disabled = true;
    }

    function clearResult() {
        resultCategory.textContent = '等待识别…';
        confidenceBar.style.width = '0%';
        confidenceText.textContent = '0%';
        annotatedPreview.innerHTML = `
                    <div class="placeholder-text">
                        <span class="ph-icon">🏷️</span>
                        <span>等待识别…</span>
                    </div>
                `;
        currentAnnotatedDataUrl = null;
        downloadBtn.disabled = true;
    }

    // ---- 识别功能（带 Loading 动画） ----
    recognizeBtn.addEventListener('click', async function() {
        if (!currentFile) {
            alert('请先上传一张卡牌图片');
            return;
        }

        // 按钮加载状态
        this.classList.add('loading');
        this.disabled = true;
        this.querySelector('.btn-text').textContent = '识别中';

        // 显示加载动画
        annotatedPreview.innerHTML = `
                    <div style="display:flex;flex-direction:column;align-items:center;gap:16px;color:var(--gold);">
                        <div class="loading-dots">
                            <span></span><span></span><span></span>
                        </div>
                        <span style="font-size:14px;color:var(--text-secondary);">AI 正在分析卡牌图案…</span>
                    </div>
                `;

        try {
            const formData = new FormData();
            formData.append('file', currentFile);

            // 【重要】后端地址，联调时改成 C 提供的地址
            const API_URL = 'http://127.0.0.1:5000/api/upload';

            const response = await fetch(API_URL, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.code === 0) {
                const d = data.data;
                resultCategory.textContent = d.category || '未知';

                const conf = d.confidence || 0;
                const confPercent = (conf * 100).toFixed(0);
                confidenceBar.style.width = confPercent + '%';
                confidenceText.textContent = confPercent + '%';

                if (d.annotated_image) {
                    const imgSrc = d.annotated_image;
                    annotatedPreview.innerHTML = `<img src="${imgSrc}" alt="标注效果图" />`;
                    currentAnnotatedDataUrl = imgSrc;
                    downloadBtn.disabled = false;
                }
            } else {
                throw new Error(data.message || '识别失败');
            }

        } catch (error) {
            console.error('识别请求失败:', error);
            annotatedPreview.innerHTML = `
                        <div class="placeholder-text" style="color:#fca5a5;">
                            <span class="ph-icon">❌</span>
                            <span>识别失败，请检查后端服务</span>
                            <span style="font-size:12px;color:var(--text-muted);">${error.message}</span>
                        </div>
                    `;
            // 自动切换 Mock 模式（后端未启动时）
            if (error.message.includes('Failed to fetch') || error.message.includes('HTTP')) {
                const useMock = confirm(
                    '⚠️ 后端服务未启动，是否使用演示模式（Mock）？\n\n' +
                    '点击「确定」使用模拟数据演示\n' +
                    '点击「取消」稍后重试'
                );
                if (useMock) {
                    mockRecognize();
                }
            }
        } finally {
            this.classList.remove('loading');
            this.disabled = false;
            this.querySelector('.btn-text').textContent = '🔍 开始识别';
        }
    });

    // ---- Mock 模式（演示用） ----
    function mockRecognize() {
        recognizeBtn.disabled = true;
        recognizeBtn.querySelector('.btn-text').textContent = '演示中';

        annotatedPreview.innerHTML = `
                    <div style="display:flex;flex-direction:column;align-items:center;gap:16px;color:var(--gold);">
                        <div class="loading-dots">
                            <span></span><span></span><span></span>
                        </div>
                        <span style="font-size:14px;color:var(--text-secondary);">演示模式：模拟识别中…</span>
                    </div>
                `;

        setTimeout(() => {
            const categories = ['⚔️ SSR-暗影龙王', '🔥 SR-烈焰凤凰', '❄️ R-冰霜巨人', '⚡ SR-雷霆领主', '💎 UR-黄金圣龙'];
            const randomCat = categories[Math.floor(Math.random() * categories.length)];
            const confidence = (0.78 + Math.random() * 0.21);

            resultCategory.textContent = randomCat;
            const confPercent = (confidence * 100).toFixed(0);
            confidenceBar.style.width = confPercent + '%';
            confidenceText.textContent = confPercent + '%';

            // 在 Canvas 上生成标注图
            const img = originalPreview.querySelector('img');
            if (img) {
                const canvas = document.createElement('canvas');
                const maxSize = 500;
                let w = img.naturalWidth || 400;
                let h = img.naturalHeight || 400;
                if (w > maxSize) { h = h * maxSize / w;
                    w = maxSize; }
                if (h > maxSize) { w = w * maxSize / h;
                    h = maxSize; }
                canvas.width = w;
                canvas.height = h;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, w, h);

                // 绘制发光边框
                ctx.shadowColor = 'rgba(246, 184, 61, 0.5)';
                ctx.shadowBlur = 20;
                ctx.strokeStyle = '#f6b83d';
                ctx.lineWidth = 4;
                const margin = 30;
                ctx.strokeRect(margin, margin, w - margin * 2, h - margin * 2);
                ctx.shadowBlur = 0;

                // 绘制类别标签
                ctx.fillStyle = 'rgba(11, 17, 32, 0.7)';
                const textW = ctx.measureText(randomCat).width + 40;
                const textH = 44;
                const tx = margin;
                const ty = margin - textH + 8;
                ctx.shadowColor = 'rgba(0,0,0,0.5)';
                ctx.shadowBlur = 12;
                ctx.beginPath();
                ctx.roundRect(tx, ty, textW, textH, 8);
                ctx.fill();
                ctx.shadowBlur = 0;

                ctx.fillStyle = '#f6b83d';
                ctx.font = 'bold 20px "Segoe UI", Arial, sans-serif';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(randomCat, tx + 20, ty + textH / 2);

                const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
                annotatedPreview.innerHTML = `<img src="${dataUrl}" alt="标注效果图" />`;
                currentAnnotatedDataUrl = dataUrl;
                downloadBtn.disabled = false;
            } else {
                annotatedPreview.innerHTML = `
                            <div class="placeholder-text" style="color:#fca5a5;">
                                <span class="ph-icon">⚠️</span>
                                <span>无法生成标注图，请先上传图片</span>
                            </div>
                        `;
            }

            recognizeBtn.disabled = false;
            recognizeBtn.querySelector('.btn-text').textContent = '🔍 开始识别';
        }, 1800);
    }

    // ---- Canvas roundRect polyfill（兼容旧浏览器） ----
    if (!CanvasRenderingContext2D.prototype.roundRect) {
        CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, r) {
            if (r > w / 2) r = w / 2;
            if (r > h / 2) r = h / 2;
            this.moveTo(x + r, y);
            this.arcTo(x + w, y, x + w, y + h, r);
            this.arcTo(x + w, y + h, x, y + h, r);
            this.arcTo(x, y + h, x, y, r);
            this.arcTo(x, y, x + w, y, r);
            return this;
        };
    }

    // ---- 下载标注图 ----
    downloadBtn.addEventListener('click', function() {
        if (!currentAnnotatedDataUrl) {
            alert('没有可下载的标注图，请先识别');
            return;
        }
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        link.download = `recognition_${timestamp}.jpg`;
        link.href = currentAnnotatedDataUrl;
        link.click();
    });
}