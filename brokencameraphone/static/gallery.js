var playerList = []
var state = undefined
var currentShowingUser = -1
var roundAmount = 0
var submissions = []
var gameInfo

function onLoad() {
    makeRequest("/api/game/" + getJoincode(), req => {
        var resp = JSON.parse(req.responseText)

        if (resp.exists) {
            gameInfo = resp.info
            updateGallery()
        } else {
            console.error("couldn't get game! retrying in 2000ms")
            window.setTimeout(onLoad, 2000)
        }
    })
}

function getJoincode() {
    var parts = location.href.split("/")
    return parts[parts.length - 1]
}

function makeRequest(url, okCallback = undefined) {
    var req = new XMLHttpRequest()

    req.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            if (okCallback) okCallback(req)
        }
    }

    req.open("GET", url, true)
    req.send()
}

function advance() {
    makeRequest("/api/gallery/advance/" + getJoincode(), req => {
        var resp = JSON.parse(req.responseText)

        if (!resp.ok) {
            console.error("Could not advance gallery")
        }
    })
}

function updateGallery() {
    makeRequest("/api/gallery/view/" + getJoincode(), req => {
        var resp = JSON.parse(req.responseText)

        if (currentShowingUser != resp["current_showing_user"] ||
            roundAmount != resp["amount"]) {
            currentShowingUser = resp["current_showing_user"]
            roundAmount = resp["amount"]
            submissions = resp["submissions"]

            renderSubmissions()
        }

        updatePlayerList()

        window.setTimeout(updateGallery, 1000)
    })
}

function updatePlayerList() {
    makeRequest("/api/lobby/" + getJoincode(), req => {
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
    })
}

function renderSubmissions() {
    var ul = document.getElementById("submissions")
    ul.innerHTML = ""
    ul.classList.add("gallery-submissions")

    if (isGameOwner) {
        var allShown = submissions.length >= gameInfo.max_rounds * 2
        document.getElementById("gallery-controls").className = allShown ? "finished" : "unfinished"
    }
    
    for (var i = 0; i < submissions.length; i++) {
        var sub = submissions[i]

        var li = document.createElement("li")

        var user = document.createElement("h3")
        user.textContent = sub["display_name"]
        user.className = "username"
        li.appendChild(user)

        if (sub["prompt"]) {
            user.textContent += i + 1 == submissions.length
              ? " starts off with..."
              : " responds with..."

            var prompt = document.createElement("p")
            prompt.classList.add("prompt")
            prompt.textContent = '"' + sub["prompt"] + '"'
            li.appendChild(prompt)
        } else {
            user.textContent += " takes a picture of..."

            var photo = document.createElement("img")
            photo.classList.add("photo")
            photo.src = "/photo/" + sub["photo_path"]

            var link = document.createElement("a")
            link.href = "/photo/" + sub["photo_path"]
            link.appendChild(photo)
            li.appendChild(link)
        }

        var date = new Date(sub["timestamp"] * 1000)

        var dateEl = document.createElement("p")
        dateEl.classList.add("meta")
        dateEl.textContent =
            `${date.toDateString()} ${date.getHours()}:${date.getMinutes()}`
        li.appendChild(dateEl)

        ul.appendChild(li)

        first = false
    }
}

function renderPlayerList() {
    var ul = document.getElementById("players")
    ul.innerHTML = ""

    if (isGameOwner) {
        ul.classList.add("gallery-playerlist")
    }

    for (var player of playerList) {
        var li = document.createElement("li")
        li.innerHTML = player["display_name"]

        if (player["is_owner"]) {
            li.innerHTML = "👑 " + li.innerHTML
        }

        if (player["user_id"] == currentShowingUser) {
            li.classList.add("viewing")
        }

        if (player["has_submitted"] > 0) {
            li.classList.add("submitted")
        }

        if (isGameOwner) {
            const userId = player["user_id"]

            li.onclick = el => {
                makeRequest("/api/gallery/set/" + getJoincode() + "/" + userId, () => {
                    updateGallery()
                })
            }
        }

        ul.appendChild(li)
    }
}