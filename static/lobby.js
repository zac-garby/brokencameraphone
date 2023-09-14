var playerList = []

function onLoad() {
    updatePlayerList()
}

function getJoincode() {
    var parts = location.href.split("/")
    return parts[parts.length - 1]
}

function updatePlayerList() {
    var req = new XMLHttpRequest()

    req.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var resp = JSON.parse(req.responseText)

            if (resp["error"] !== undefined) {
                console.error(resp["error"])
            } else {
                playerList = resp["players"]
                renderPlayerList()
            }

            window.setTimeout(updatePlayerList, 2000)
        }
    }

    req.open("GET", "/api/lobby/" + getJoincode(), true)
    req.send()
}

function renderPlayerList() {
    var ul = document.getElementById("players")
    ul.innerHTML = ""

    for (var player of playerList) {
        var li = document.createElement("li")
        li.innerHTML = player["display_name"]
        if (player["is_owner"]) {
            li.innerHTML = "👑 " + li.innerHTML
        }
        ul.appendChild(li)
    }
}