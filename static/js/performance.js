document.addEventListener("DOMContentLoaded", function () {

    const progressBars =
        document.querySelectorAll(".progress-bar");

    progressBars.forEach(function (bar) {

        let percentage =
            parseFloat(bar.dataset.percentage);

        if (isNaN(percentage)) {
            percentage = 0;
        }

        if (percentage < 0) {
            percentage = 0;
        }

        if (percentage > 100) {
            percentage = 100;
        }

        bar.style.width = percentage + "%";


        // Remove previous status classes
        bar.classList.remove("good", "average", "low");


        // Add color based on performance
        if (percentage >= 75) {

            bar.classList.add("good");

        } else if (percentage >= 50) {

            bar.classList.add("average");

        } else {

            bar.classList.add("low");

        }

    });

});