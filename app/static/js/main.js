/* ==========================================
   JOB TRACKER v3 - JavaScript
   ========================================== */

document.addEventListener('DOMContentLoaded', () => {

    // === Animated Stat Counters ===
    const counters = document.querySelectorAll('.stat-value[data-target]');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.dataset.target);
                const suffix = el.dataset.suffix || '';
                if (isNaN(target) || target === 0) {
                    el.textContent = '0' + suffix;
                    return;
                }
                let current = 0;
                const duration = 1200;
                const steps = 50;
                const increment = target / steps;
                const stepTime = duration / steps;

                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        current = target;
                        clearInterval(timer);
                    }
                    el.textContent = Math.round(current) + suffix;
                }, stepTime);

                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(el => observer.observe(el));

    // === Animate activity bars ===
    const activityBars = document.querySelectorAll('.activity-bar');
    setTimeout(() => {
        activityBars.forEach(bar => {
            const h = bar.style.height;
            bar.style.height = '0%';
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    bar.style.height = h;
                });
            });
        });
    }, 400);

    // === Keyboard shortcuts ===
    document.addEventListener('keydown', (e) => {
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
        if (e.key === '/') {
            e.preventDefault();
            const input = document.querySelector('.search-input');
            if (input) input.focus();
        }
        if (e.key === 'n') {
            window.location.href = '/add';
        }
    });

    // === Close mobile sidebar on link click ===
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', () => {
            document.querySelector('.sidebar')?.classList.remove('open');
        });
    });

    // === Close sidebar on outside click (mobile) ===
    document.addEventListener('click', (e) => {
        const sidebar = document.querySelector('.sidebar');
        const menuBtn = document.querySelector('.mobile-menu-btn');
        if (sidebar?.classList.contains('open') && !sidebar.contains(e.target) && !menuBtn?.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
});
