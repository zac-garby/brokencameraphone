var prompt_ideas = [
    "An idea location for a nuclear bunker.",
    "\"If I'm going to die, it's going to be here.\"",
    "A great place for a boss fight.",
    "An inanimate object which looks animate.",
    "3am in my city is like...",
    "The highest point you can get to.",
    "A super fancy meal.",
    "\"I woke up like this.\"",
    "The lowest point you can reach. Bonus points for below sea level.",
    "The most beautiful view imaginable.",
    "A selfie with a stranger.",
    "A photo of you doing some arts & crafts.",
    "A special skill of yours.",
    "A photo of you touching your toes!",
    "A photo taken from the top of a tree.",
    "\"This would be a great wall to climb.\"",
    "An artsy photo of some mundane architecture.",
    "Do something illegal and take a selfie whilst doing it."
]

function setExamplePrompt() {
    var textarea = document.getElementById("prompt")
    
    var i = Math.floor(Math.random() * prompt_ideas.length)
    textarea.placeholder = "e.g. " + prompt_ideas[i]
}
