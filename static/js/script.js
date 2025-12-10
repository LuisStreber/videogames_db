document.addEventListener('DOMContentLoaded', () => {
    // Autofocus search
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        searchInput.focus();
    }

    // Simple data-animate support
    document.querySelectorAll('[data-animate]').forEach(el => {
        el.style.opacity = 0;
        el.style.transform = 'translateY(6px)';
        setTimeout(() => {
            el.style.transition = 'opacity .45s ease, transform .35s ease';
            el.style.opacity = 1;
            el.style.transform = 'translateY(0)';
        }, 60);
    });

    // Close modals with ESC (Flowbite will still manage normal hide/show)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            ['modal-game', 'modal-console'].forEach(id => {
                const m = document.getElementById(id);
                if (m && !m.classList.contains('hidden')) {
                    // Use Flowbite hide trigger if present
                    const hideBtn = m.querySelector('[data-modal-hide]');
                    if (hideBtn) hideBtn.click();
                    else m.classList.add('hidden');
                }
            });
        }
    });

    // Improve opening modal focus: when a modal is shown, focus first input
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target && target.id && !target.classList.contains('hidden')) {
                    const first = target.querySelector('input, textarea, select, button');
                    if (first) first.focus();
                }
            }
        }
    });

    ['modal-game','modal-console'].forEach(id => {
        const el = document.getElementById(id);
        if (el) observer.observe(el, { attributes: true });
    });
});
