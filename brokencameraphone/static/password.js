// List elements to display whats missing
var letter = document.getElementById("letter");
var capital = document.getElementById("capital");
var number = document.getElementById("number");
var symbol = document.getElementById("symbol")
var length = document.getElementById("length");
var match = document.getElementById("match");

// Input elements
var messageBox = document.getElementById("message");
var submitButton = document.getElementById("submit");
var password = document.getElementById("passwd");
var passwordCheck = document.getElementById("passwd_check");

// All count must be true for the password to be correct
var count = [false, false, false, false, false, false];

// Show the message box when user clicks password
password.onfocus = function() {
    if(count.every(Boolean) === false){
        messageBox.classList.remove("hidden");
    }
}

passwordCheck.onfocus = function() {
    if(count.every(Boolean) === false){
        messageBox.classList.remove("hidden");
    }
}

// When the user starts to type something inside the password field
password.oninput = function() {
    // Lowercase letters
    var lowerCaseLetters = /[a-z]/g;
    if(password.value.match(lowerCaseLetters)) {
        letter.classList.add("hidden");
        count[0] = true;
    } else {
        letter.classList.remove("hidden");
        count[0] = false;
    }

    // Capital letters
    var upperCaseLetters = /[A-Z]/g;
    if(password.value.match(upperCaseLetters)) {
        capital.classList.add("hidden");
        count[1] = true;
    } else {
        capital.classList.remove("hidden");
        count[1] = false;
    }

    // Numbers
    var numbers = /[\d]/g;
    if(password.value.match(numbers)) {
        number.classList.add("hidden");
        count[2] = true;
    } else {
        number.classList.remove("hidden");
        count[2] = false;
    }

    // Symbols
    var symbols = /[\W_]/g;
    if(password.value.match(symbols)) {
        symbol.classList.add("hidden");
        count[3] = true;
    } else {
        symbol.classList.remove("hidden");
        count[3] = false;
    }

    // Length
    if(password.value.length >= 6) {
        length.classList.add("hidden");
        count[4] = true;
    } else {
        length.classList.remove("hidden");
        count[4] = false;
    }

    // All conditions met?
    if(count.every(Boolean)) {
        messageBox.classList.add("hidden");
        submitButton.disabled = false;
    } else {
        messageBox.classList.remove("hidden");
        submitButton.disabled = true;
    }
}

passwordCheck.oninput = function() {
    // Passwords match?
    if(password.value == passwordCheck.value){
        match.classList.add("hidden");
        count[5] = true;
    } else {
        match.classList.remove("hidden");
        count[5] = false;
    }

    // All conditions met?
    if(count.every(Boolean)) {
        messageBox.classList.add("hidden");
        submitButton.disabled = false;
    } else {
        messageBox.classList.remove("hidden");
        submitButton.disabled = true;
    }
}
