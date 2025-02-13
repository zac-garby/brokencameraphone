import requests
from datetime import datetime, timezone

def send_disc_notif(endpoint: str, subject: str, desc: str, game: str, time = None):
    """
    This will send a notification to a Discord webhook endpoint.

    Parameters:
    endpoint (str): The URL endpoint.
    subject (str): Subject of the notification - e.g new game.
    desc (str): Notification main body. Can be multiline.
    game (str): Game code. Will mean that the embed links to the correct game.
    datetime (int): UNIX timestamp to display the datetime in the footer of the embed.

    Returns:
    bool: True if success, False otherwise.
    """

    timestamp = time if time is not None else datetime.now(timezone.utc).timestamp()  # Default to current timestamp if time is None

    message = {
        "content": "", # No content needed, all on an embed
        "username": "WCP Notification", # The name of the webhook "bot"
        "avatar_url": "https://whisperingcameraphone.com/static/icons/android-chrome-512x512.png", # Profile pic
        "embeds": [
            {
                "title": subject,
                "description": desc,
                "author": {
                    "name": "Whispering Cameraphone",
                    "url": f"https://whisperingcameraphone.com/game/{game}"
                },
                "url": f"https://whisperingcameraphone.com/game/{game}",
                "timestamp": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "color": 13261670,
                "footer": {
                    "text": "WCP",
                    "icon_url": "https://whisperingcameraphone.com/static/icons/android-chrome-512x512.png"
                },
                "image": {
                    "url": "https://nextcloud.olivermalkin.co.uk/index.php/apps/files_sharing/publicpreview/XKiT83HLz6wdAgk?file=/&fileId=1976&x=2560&y=1440&a=true&etag=2c75e584ada7d128afb43978e3577804",
                }
            }
        ]
    }

    request = requests.post(url=endpoint, json=message)

    if request.status_code == 204: # Discord replies with 204
        return True
    else:
        return False
