GAMEMODES = {
    0: {
        "name": "Vanilla",
        "description": "Vanilla is your standard Whispering Cameraphone game. One chain per player, each starting with a prompt and alternating photos and prompts.",
        "options": [
            { "name": "skip-initial", "text": "Start with photos?",
              "type": "bool", "db_column": "opt_vanilla_skip_initial" },
            { "name": "final-prompts", "text": "Finish with text prompts?",
              "type": "bool", "db_column": "opt_vanilla_final_prompts" },
        ]
    },
    1: {
        "name": "Overruled",
        "description": "Like Vanilla, but each starting player also gives an overarching 'rule' for their entire chain. Perhaps 'only drawings!', or 'no photo editing allowed!', or 'each photo must be a baked good!'.",
        "options": [
            { "name": "skip-initial", "text": "Start with photos?",
              "type": "bool", "db_column": "opt_vanilla_skip_initial" },
            { "name": "final-prompts", "text": "Finish with text prompts?",
              "type": "bool", "db_column": "opt_vanilla_final_prompts" },
        ]
    },
    2: {
        "name": "Camera Roll",
        "description": "Who needs words! Chains in a Camera Roll game begin and end with photos (and the middle part is... also just photos). Optionally, start off with a text prompt.",
        "options": [
            { "name": "initial-prompts", "text": "Begin with a text prompt?",
              "type": "bool", "db_column": "opt_photos_initial_prompts" },
        ]
    },
    3: {
        "name": "Animation",
        "description": "A little like Camera Roll, but the photo chain will be played back as an animated GIF. Optionally start with a prompt.",
        "options": [
            { "name": "initial-prompts", "text": "Begin with a text prompt?",
              "type": "bool", "db_column": "opt_animation_onion_skin" },
            { "name": "onion-skin", "text": "Enable onion skinning?",
              "type": "bool", "db_column": "opt_animation_onion_skin" },
        ]
    }
}
