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