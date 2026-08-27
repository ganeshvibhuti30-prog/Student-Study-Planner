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

    });

});