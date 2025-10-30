document.addEventListener('DOMContentLoaded', () => {
        bindHandlers();
    });

function toggleDarkMode() {
    var element = document.body;
    element.classList.toggle("dark-mode");
}
