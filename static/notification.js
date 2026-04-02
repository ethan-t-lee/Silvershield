/*************************
   Notification System
**************************/
function showNotification(isCorrect, message, target = "email") {

    let notification, title, text;

    if (target === "email") {
        notification = document.getElementById("desktopNotificationEmail");
        title = document.getElementById("notificationTitleEmail");
        text = document.getElementById("notificationMessageEmail");
    } else {
        notification = document.getElementById("desktopNotificationInternet");
        title = document.getElementById("notificationTitleInternet");
        text = document.getElementById("notificationMessageInternet");
    }

    // Reset classes
    notification.classList.remove("hidden", "correct", "wrong");

    // Apply correct/wrong styles
    if (isCorrect) {
        notification.classList.add("correct");
        title.innerText = "Correct!";
        text.innerText = message;
    } else {
        notification.classList.add("wrong");
        title.innerText = "Incorrect";
        text.innerText = message;
    }

    // Show popup (required small delay for animation)
    setTimeout(() => {
        notification.classList.remove("hidden");
    }, 10);

    // Auto-hide
    setTimeout(() => {
        notification.classList.add("hidden");
    }, 5000);
}
