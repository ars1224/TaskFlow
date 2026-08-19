const menuButton = document.querySelector("#menuButton");
const sidebar = document.querySelector("#sidebar");
const sidebarOverlay = document.querySelector("#sidebarOverlay");

function closeMenu() {
    if (!menuButton || !sidebar || !sidebarOverlay) {
        return;
    }

    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("open");
    menuButton.setAttribute("aria-expanded", "false");
}

function toggleMenu() {
    const isOpen = sidebar.classList.toggle("open");

    sidebarOverlay.classList.toggle("open", isOpen);
    menuButton.setAttribute("aria-expanded", String(isOpen));
}

if (menuButton && sidebar && sidebarOverlay) {
    menuButton.addEventListener("click", toggleMenu);
    sidebarOverlay.addEventListener("click", closeMenu);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMenu();
        }
    });
}

document.querySelectorAll("[data-disable-on-submit]").forEach((form) => {
    form.addEventListener("submit", () => {
        const submitButton = form.querySelector("button[type='submit']");

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Saving...";
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const progressBar = document.querySelector(".dashboard-progress-fill");

    if (progressBar) {
        const progress = progressBar.dataset.progress || 0;
        progressBar.style.width = `${progress}%`;
    }
});