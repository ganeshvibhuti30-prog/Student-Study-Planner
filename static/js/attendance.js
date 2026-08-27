const conductedInput = document.getElementById("conducted");
const attendedInput = document.getElementById("attended");
const calculateBtn = document.getElementById("calculateBtn");

const percentageDisplay = document.getElementById("percentage");
const statusDisplay = document.getElementById("status");

calculateBtn.addEventListener("click", function () {

    const conducted = Number(conductedInput.value);
    const attended = Number(attendedInput.value);

    if (conducted <= 0) {
        alert("Please enter the number of classes conducted.");
        return;
    }

    if (attended < 0) {
        alert("Attended classes cannot be negative.");
        return;
    }

    if (attended > conducted) {
        alert("Attended classes cannot be greater than conducted classes.");
        return;
    }

    const percentage = (attended / conducted) * 100;

    percentageDisplay.textContent = percentage.toFixed(2) + "%";

    if (percentage >= 75) {
        statusDisplay.textContent = "Attendance is good.";
    } else {
        statusDisplay.textContent = "Attendance is below 75%.";
    }
});