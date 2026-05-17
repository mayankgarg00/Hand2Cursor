document.addEventListener('DOMContentLoaded', () => {

    const glow = document.getElementById('cursor-glow');
    document.addEventListener('mousemove', e => {
        glow.style.left = e.clientX + 'px';
        glow.style.top = e.clientY + 'px';
    });

    const canvas = document.getElementById('particle-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    let w, h;

    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() { this.reset(); }
        reset() {
            this.x = Math.random() * w;
            this.y = Math.random() * h;
            this.size = Math.random() * 1.5 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            this.opacity = Math.random() * 0.4 + 0.1;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > w || this.y < 0 || this.y > h) this.reset();
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(99, 102, 241, ${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < 80; i++) particles.push(new Particle());

    function animateParticles() {
        ctx.clearRect(0, 0, w, h);
        particles.forEach(p => { p.update(); p.draw(); });

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animateParticles);
    }
    animateParticles();

    const reveals = document.querySelectorAll(
        '.feature-card, .pipeline-step, .pipeline-img-card, .arch-node, .gesture-card, .setup-step, .tech-card, .config-table-wrap, .demo-feed-wrap, .demo-sidebar'
    );
    reveals.forEach(el => el.classList.add('reveal'));

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                setTimeout(() => entry.target.classList.add('visible'), i * 60);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    reveals.forEach(el => observer.observe(el));

    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        const st = window.scrollY;
        navbar.style.background = st > 100 ? 'rgba(7, 7, 14, 0.92)' : 'rgba(7, 7, 14, 0.75)';
    });

    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', e => {
            const href = a.getAttribute('href');
            if (href === '#') return;
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) target.scrollIntoView({ behavior: 'smooth' });
        });
    });

    const heroImg = document.getElementById('hero-img');
    if (heroImg) {
        document.addEventListener('mousemove', e => {
            const x = (e.clientX / window.innerWidth - 0.5) * 8;
            const y = (e.clientY / window.innerHeight - 0.5) * 8;
            heroImg.style.transform = `perspective(800px) rotateY(${x}deg) rotateX(${-y}deg)`;
        });
    }
});

let statusInterval = null;
let lastLoggedAction = '';

function startTracking() {
    fetch('/start', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'started' || data.status === 'already_running') {
                document.getElementById('btn-start').disabled = true;
                document.getElementById('btn-stop').disabled = false;
                document.getElementById('demo-placeholder').style.display = 'none';
                const vid = document.getElementById('video-stream');
                vid.src = '/video_feed?' + Date.now();
                vid.style.display = 'block';
                document.getElementById('status-pipeline').innerHTML =
                    '<span class="status-dot online"></span> Running';
                document.getElementById('gesture-log').innerHTML =
                    '<div class="log-empty">Listening for gestures...</div>';
                startStatusPolling();
            }
        })
        .catch(() => {
            alert('Could not connect to the backend. Make sure app.py is running.');
        });
}

function stopTracking() {
    fetch('/stop', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
            document.getElementById('btn-start').disabled = false;
            document.getElementById('btn-stop').disabled = true;
            document.getElementById('video-stream').style.display = 'none';
            document.getElementById('demo-placeholder').style.display = '';
            document.getElementById('status-pipeline').innerHTML =
                '<span class="status-dot offline"></span> Offline';
            document.getElementById('status-fps').textContent = '— FPS';
            document.getElementById('status-action').textContent = '—';
            stopStatusPolling();
        });
}

function startStatusPolling() {
    stopStatusPolling();
    statusInterval = setInterval(() => {
        fetch('/status')
            .then(r => r.json())
            .then(data => {
                if (!data.active) {
                    stopTracking();
                    if (data.error) {
                        alert('Tracking Error: ' + data.error);
                    }
                    return;
                }
                document.getElementById('status-fps').textContent = data.fps + ' FPS';
                const actionLabel = data.action.replace('_', ' ').toUpperCase();
                document.getElementById('status-action').textContent = actionLabel;

                if (data.action !== 'idle' && data.action !== 'move' && data.action !== lastLoggedAction) {
                    addGestureLog(data.action);
                }
                lastLoggedAction = data.action;
            })
            .catch(() => {});
    }, 500);
}

function stopStatusPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
}

function addGestureLog(action) {
    const log = document.getElementById('gesture-log');
    const empty = log.querySelector('.log-empty');
    if (empty) empty.remove();

    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour12: false });
    const label = action.replace('_', ' ');

    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-time">${time}</span><span class="log-action ${action}">${label}</span>`;
    log.prepend(entry);

    while (log.children.length > 20) {
        log.removeChild(log.lastChild);
    }
}
