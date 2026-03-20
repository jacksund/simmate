
// for a *real* progress bar, django-unicorn + polling should be used

function runFakeProgressBar(progressBarId, totalTimeInSeconds, countUp) {
    // Example usage:
    // runFakeProgressBar('test123', 10, false);
    if (countUp) { var i = 0; } else {var i = 100;}
    var intervalTimeInMilliseconds = 50; // Interval time in milliseconds
    var increment = 100 / (totalTimeInSeconds * 1000 / intervalTimeInMilliseconds);
    var progressBar = document.getElementById(progressBarId);
    var counterForward = setInterval(function () {
        if (countUp) { i += increment; } else { i -= increment; }
        if (i <= 100) {
            progressBar.style.width = i + '%';
        } else {
            progressBar.style.width = '100%';
            clearInterval(counterForward);
        }
    }, intervalTimeInMilliseconds);
}
