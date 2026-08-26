const registrationForm = document.getElementById("registrationForm");

registrationForm.addEventListener("submit", function (event) {

    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    const passwordError = document.getElementById("passwordError");

    passwordError.textContent = "";

    if (password.length < 8) {
        event.preventDefault();

        passwordError.textContent =
            "Password must contain at least 8 characters.";

        return;
    }

    if (password !== confirmPassword) {
        event.preventDefault();

        passwordError.textContent =
            "Passwords do not match.";

        return;
    }
});