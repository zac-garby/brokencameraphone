var playerList = []
var state = undefined
var currentShowingUser = -1
var roundAmount = 0
var submissions = []

function onLoad() {
    updateGallery()
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

    for (var sub of submissions) {
        var li = document.createElement("li")

        var user = document.createElement("h3")
        user.textContent = sub["display_name"]
        user.className = "username"
        li.appendChild(user)

        if (sub["prompt"]) {
            user.textContent += " says..."

            var prompt = document.createElement("p")
            prompt.classList.add("prompt")
            prompt.textContent = '"' + sub["prompt"] + '"'
            li.appendChild(prompt)
        } else {
            user.textContent += " took a picture of..."

            var photo = document.createElement("img")
            photo.classList.add("photo")
            photo.src = "/photo/" + sub["photo_path"]

            var link = document.createElement("a")
            link.href = "/photo/" + sub["photo_path"]
            link.appendChild(photo)
            li.appendChild(link)
        }

        ul.appendChild(li)
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

        if (player["user_id"] == currentShowingUser) {
            li.classList.add("viewing")
        }

        if (player["is_owner"]) {
            li.innerHTML = "👑 " + li.innerHTML
        }

        if (player["has_submitted"] > 0) {
            li.classList.add("submitted")
        }

        if (isGameOwner) {
            const userId = player["user_id"]

            li.onclick = el => {
                makeRequest("/api/gallery/set/" + getJoincode() + "/" + userId, () => window.location.href = window.location.href)
            }
        }

        ul.appendChild(li)
    }
}