const registrationForm = document.getElementById("registrationForm");

registrationForm.addEventListener("submit", function (event) {

    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    const passwordError = document.getElementById("passwordError");

    passwordError.textContent = "";
    passwordError.style.display = "none";

    if (password.length < 8) {
        event.preventDefault();

        passwordError.textContent =
            "Password must contain at least 8 characters.";

        passwordError.style.display = "block";
        return;
    }

    if (password !== confirmPassword) {
        event.preventDefault();

        passwordError.textContent =
            "Passwords do not match.";

        passwordError.style.display = "block";
        return;
    }
});


// Password visibility toggle
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");

togglePassword.addEventListener("click", function () {

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        togglePassword.textContent = "Hide Password";
    } else {
        passwordInput.type = "password";
        togglePassword.textContent = "Show Password";
    }
});


// Confirm password visibility toggle
const confirmPasswordInput =
    document.getElementById("confirm_password");

const toggleConfirmPassword =
    document.getElementById("toggleConfirmPassword");

toggleConfirmPassword.addEventListener("click", function () {

    if (confirmPasswordInput.type === "password") {
        confirmPasswordInput.type = "text";
        toggleConfirmPassword.textContent = "Hide Password";
    } else {
        confirmPasswordInput.type = "password";
        toggleConfirmPassword.textContent = "Show Password";
    }
});