document.addEventListener("DOMContentLoaded", function () {

    const conductedInput = document.getElementById("classes_conducted");
    const attendedInput = document.getElementById("classes_attended");

    if (!conductedInput || !attendedInput) {
        return;
    }

    attendedInput.addEventListener("input", function () {

        const conducted = parseInt(conductedInput.value);
        const attended = parseInt(attendedInput.value);

        if (
            !isNaN(conducted) &&
            !isNaN(attended) &&
            conducted > 0
        ) {

            if (attended > conducted) {
                attendedInput.setCustomValidity(
                    "Attended classes cannot be greater than conducted classes."
                );
            } else {
                attendedInput.setCustomValidity("");
            }

        } else {

            attendedInput.setCustomValidity("");

        }
    });

});