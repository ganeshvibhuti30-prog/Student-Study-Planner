function validateStudyForm() {
    const subject = document.getElementById("subject").value;
    const topic = document.getElementById("topic").value;
    const date = document.getElementById("date").value;
    const duration = document.getElementById("duration").value;

    if (subject === "") {
        alert("Please select a subject.");
        return false;
    }

    if (topic.trim() === "") {
        alert("Please enter a topic.");
        return false;
    }

    if (date === "") {
        alert("Please select a date.");
        return false;
    }

    if (duration === "" || duration <= 0) {
        alert("Please enter a valid study duration.");
        return false;
    }

    return true;
}