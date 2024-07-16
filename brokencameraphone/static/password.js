// elements to display whats missing
var length = document.getElementById("length");
var match = document.getElementById("match");

// Input elements
var messageBox = document.getElementById("message");
var submitButton = document.getElementById("submit");
var password = document.getElementById("passwd");
var passwordCheck = document.getElementById("passwd_check");

// All must be true for the password to be correct
var passwordLongEnough = false
var passwordsMatch = false

function onPasswordChange() {
    messageBox.classList.toggle("hidden", passwordLongEnough && passwordsMatch)
}

password.onfocus = onPasswordChange
passwordCheck.onfocus = onPasswordChange

// When the user starts to type something inside the password field
password.oninput = function () {
    passwordLongEnough = password.value.length >= 6
    length.classList.toggle("hidden", passwordLongEnough)

    passwordsMatch = password.value == passwordCheck.value
    match.classList.toggle("hidden", passwordsMatch)

    onPasswordChange()
}

passwordCheck.oninput = function () {
    passwordsMatch = password.value == passwordCheck.value
    match.classList.toggle("hidden", passwordsMatch)

    onPasswordChange()
}
