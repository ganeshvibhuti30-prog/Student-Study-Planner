document.addEventListener("DOMContentLoaded", function () {

    const countdowns = document.querySelectorAll(".countdown");

    function updateCountdowns() {

        countdowns.forEach(function (countdown) {

            const examDate = countdown.dataset.date;
            const examTime = countdown.dataset.time;

            const examDateTime = new Date(
                examDate + "T" + examTime
            );

            const now = new Date();

            const difference = examDateTime - now;

            if (difference <= 0) {
                countdown.textContent = "Exam time has arrived!";
                return;
            }

            const days = Math.floor(
                difference / (1000 * 60 * 60 * 24)
            );

            const hours = Math.floor(
                (difference / (1000 * 60 * 60)) % 24
            );

            const minutes = Math.floor(
                (difference / (1000 * 60)) % 60
            );

            const seconds = Math.floor(
                (difference / 1000) % 60
            );

            countdown.textContent =
                "Countdown: " +
                days + " days " +
                hours + " hours " +
                minutes + " minutes " +
                seconds + " seconds";

        });

    }

    updateCountdowns();

    setInterval(updateCountdowns, 1000);

});