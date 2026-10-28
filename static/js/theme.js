// static/js/theme.js
// ProChat Theme Manager

(function() {
    // Load saved theme
    const savedTheme = localStorage.getItem('prochat_theme') || 'dark';
    applyTheme(savedTheme);

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        if (theme === 'light') {
            document.documentElement.style.setProperty('--bg',    '#f5f4ff');
            document.documentElement.style.setProperty('--bg2',   '#ffffff');
            document.documentElement.style.setProperty('--bg3',   '#f0eeff');
            document.documentElement.style.setProperty('--bg4',   '#e8e4ff');
            document.documentElement.style.setProperty('--text',  '#1a1825');
            document.documentElement.style.setProperty('--text2', '#3d3555');
            document.documentElement.style.setProperty('--text3', '#8b80a8');
            document.documentElement.style.setProperty('--border','#0000000d');
            document.documentElement.style.setProperty('--border2','#00000018');
        } else {
            document.documentElement.style.removeProperty('--bg');
            document.documentElement.style.removeProperty('--bg2');
            document.documentElement.style.removeProperty('--bg3');
            document.documentElement.style.removeProperty('--bg4');
            document.documentElement.style.removeProperty('--text');
            document.documentElement.style.removeProperty('--text2');
            document.documentElement.style.removeProperty('--text3');
            document.documentElement.style.removeProperty('--border');
            document.documentElement.style.removeProperty('--border2');
        }
    }

    // Global toggle function
    window.toggleTheme = function() {
        const current = localStorage.getItem('prochat_theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem('prochat_theme', next);
        applyTheme(next);
    };

    // Mobile sidebar overlay
    document.addEventListener('click', function(e) {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.querySelector('.menu-toggle');
        if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
            sidebar.classList.remove('open');
        }
    });
})();