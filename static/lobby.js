var playerList = []
var state = undefined

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

                var newState = resp["state"]
                if (state !== undefined && state != newState) {
                    window.location.href = window.location.href
                    console.log("refreshing")
                }

                state = newState
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
        if (player["has_submitted"] > 0) {
            li.classList.add("submitted")
        }
        ul.appendChild(li)
    }
}