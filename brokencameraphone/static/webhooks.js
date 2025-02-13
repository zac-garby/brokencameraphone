var friendly = document.getElementById("friendly_name");
var webhook = document.getElementById("webhook_name");

function changeSelector() {
    let dropdown = document.getElementById("webhook_selector").value;
    dropdown = dropdown.replace(/\s+/g, '');

    if (dropdown == "add_new") {
        friendly.value = "";
        webhook.value = "";
    }
    else {
        friendly.value = dropdown;
        webhook.value = userWebhooks[dropdown];
    }
}