const menuButton = document.querySelector("#menuButton");
const sidebar = document.querySelector("#sidebar");
const sidebarOverlay = document.querySelector("#sidebarOverlay");


/* =========================================================
   MOBILE SIDEBAR
   ========================================================= */

function closeMenu() {
    if (!menuButton || !sidebar || !sidebarOverlay) {
        return;
    }

    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("open");

    menuButton.setAttribute(
        "aria-expanded",
        "false"
    );
}


function toggleMenu() {
    const isOpen =
        sidebar.classList.toggle("open");

    sidebarOverlay.classList.toggle(
        "open",
        isOpen
    );

    menuButton.setAttribute(
        "aria-expanded",
        String(isOpen)
    );
}


if (menuButton && sidebar && sidebarOverlay) {

    menuButton.addEventListener(
        "click",
        toggleMenu
    );

    sidebarOverlay.addEventListener(
        "click",
        closeMenu
    );

    document.addEventListener(
        "keydown",
        (event) => {

            if (event.key === "Escape") {
                closeMenu();
            }

        }
    );
}



/* =========================================================
   CREATE / EDIT TASK VALIDATION
   ========================================================= */

document
    .querySelectorAll("form[data-disable-on-submit]")
    .forEach((form) => {

        const scheduledDateInput =
            form.querySelector(
                "[data-scheduled-date]"
            );

        const dueDateInput =
            form.querySelector(
                "[data-due-date]"
            );

        const dateError =
            form.querySelector(
                "[data-date-error]"
            );


        /* -----------------------------------------
           Clear date error
           ----------------------------------------- */

        function clearDateError() {

            if (scheduledDateInput) {

                scheduledDateInput.classList.remove(
                    "date-input-error"
                );

                scheduledDateInput.removeAttribute(
                    "aria-invalid"
                );

            }

            if (dateError) {

                dateError.textContent = "";

                dateError.classList.remove(
                    "show"
                );

            }

        }


        /* -----------------------------------------
           Show date error
           ----------------------------------------- */

        function showDateError(message) {

            if (scheduledDateInput) {

                scheduledDateInput.classList.add(
                    "date-input-error"
                );

                scheduledDateInput.setAttribute(
                    "aria-invalid",
                    "true"
                );

            }

            if (dateError) {

                dateError.textContent = message;

                dateError.classList.add(
                    "show"
                );

            }

        }


        /* -----------------------------------------
           Validate scheduled date
           ----------------------------------------- */

        function validateDates() {

            /*
             * Forms such as login/change password
             * do not have task dates.
             */

            if (
                !scheduledDateInput ||
                !dueDateInput
            ) {
                return true;
            }


            const scheduledDate =
                scheduledDateInput.value;

            const dueDate =
                dueDateInput.value;

            const today =
                scheduledDateInput.dataset.today;


            clearDateError();


            /*
             * Rule 1:
             * Scheduled date cannot be in the past.
             */

            if (
                scheduledDate &&
                today &&
                scheduledDate < today
            ) {

                showDateError(
                    "Scheduled date cannot be in the past."
                );

                scheduledDateInput.focus();

                return false;
            }


            /*
             * Rule 2:
             * Scheduled date cannot be later
             * than the due date.
             */

            if (
                scheduledDate &&
                dueDate &&
                scheduledDate > dueDate
            ) {

                showDateError(
                    "Scheduled date cannot be after the due date."
                );

                scheduledDateInput.focus();

                return false;
            }


            return true;
        }


        /* -----------------------------------------
           Form submit
           ----------------------------------------- */

        form.addEventListener(
            "submit",
            (event) => {

                /*
                 * Prevent submission if invalid.
                 *
                 * Because the form is not submitted,
                 * Bootstrap keeps the modal open.
                 */

                if (!validateDates()) {

                    event.preventDefault();

                    return;
                }


                /*
                 * Only disable the button after
                 * validation succeeds.
                 */

                const submitButton =
                    form.querySelector(
                        'button[type="submit"]'
                    );

                if (submitButton) {

                    submitButton.disabled = true;

                    submitButton.textContent =
                        "Saving...";

                }

            }
        );


        /* -----------------------------------------
           Re-check when either date changes
           ----------------------------------------- */

        if (scheduledDateInput) {

            scheduledDateInput.addEventListener(
                "change",
                validateDates
            );

        }


        if (dueDateInput) {

            dueDateInput.addEventListener(
                "change",
                validateDates
            );

        }

    });



/* =========================================================
   DASHBOARD PROGRESS BAR
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const progressBar =
            document.querySelector(
                ".dashboard-progress-fill"
            );

        if (progressBar) {

            const progress =
                progressBar.dataset.progress || 0;

            progressBar.style.width =
                `${progress}%`;

        }

    }
);