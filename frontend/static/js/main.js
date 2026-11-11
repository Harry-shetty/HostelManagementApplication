// Nestora Housing Main JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // Keyboard shortcut CMD/CTRL + K to focus search
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('hostel-search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });

    // Close modals and sidebar on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-layer').forEach(modal => {
                modal.style.display = 'none';
            });
            if (typeof closeSidebar === 'function') {
                closeSidebar();
            }
        }
    });

    // Reset mobile sidebar when resizing window to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 800) {
            if (typeof closeSidebar === 'function') {
                closeSidebar();
            }
        }
    });
});

