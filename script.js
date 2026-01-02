function toggleDarkMode() {
    const root = document.documentElement;
    const isDark = root.classList.toggle('dark-mode');
    // Зберігаємо поточну тему в localStorage
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}
