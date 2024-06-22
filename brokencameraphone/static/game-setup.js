function onLoad() {
    updatePlayerList()

    window.gamemodeDescription = document.getElementById("gamemode-description")

    for (var inp of document.querySelectorAll("input[name=gamemode]")) {
        inp.addEventListener("change", function(event) {
            updateSelectedGamemode(event.target)
        })
    }

    updateSelectedGamemode(document.getElementById("gamemode-0"))
}

function updateSelectedGamemode(target) {
    gamemodeDescription.textContent = target.attributes["data-description"].value

    for (var opts of document.querySelectorAll("div.gamemode-options")) {
        opts.classList.toggle("hidden", opts.id !== "options-" + target.value)
    }
}
