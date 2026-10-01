// ── Sidebar toggle ──────────────────────────────────────────
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    if (sidebar && sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) && e.target !== toggle && !toggle?.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// ── Auto-dismiss toasts ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach((toast, i) => {
        setTimeout(() => {
            toast.style.transition = 'all 0.4s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(120%)';
            setTimeout(() => toast.remove(), 400);
        }, 4000 + i * 500);
    });
});

// ── Animate stat counters ───────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.stat-value').forEach(el => {
        const target = parseInt(el.textContent, 10);
        if (isNaN(target) || target === 0) return;
        let current = 0;
        const duration = 800;
        const step = target / (duration / 16);
        const timer = setInterval(() => {
            current = Math.min(current + step, target);
            el.textContent = Math.floor(current).toLocaleString();
            if (current >= target) {
                el.textContent = target.toLocaleString();
                clearInterval(timer);
            }
        }, 16);
    });
});

// ── Uppercase certificate ID input ──────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[style*="text-transform:uppercase"]').forEach(inp => {
        inp.addEventListener('input', () => {
            const pos = inp.selectionStart;
            inp.value = inp.value.toUpperCase();
            inp.setSelectionRange(pos, pos);
        });
    });
});

// ── Confirm before form submit (data-confirm) ───────────────
document.addEventListener('submit', (e) => {
    const msg = e.target.dataset.confirm;
    if (msg && !confirm(msg)) e.preventDefault();
});
