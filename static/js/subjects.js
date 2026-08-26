const subjectForm = document.querySelector("form");

subjectForm.addEventListener("submit", function (event) {

    const creditsInput = document.getElementById("credits");
    const credits = Number(creditsInput.value);

    if (credits < 1 || credits > 4 || !Number.isInteger(credits)) {
        event.preventDefault();

        alert("Credits must be a whole number between 1 and 4.");

        creditsInput.focus();
    }
});