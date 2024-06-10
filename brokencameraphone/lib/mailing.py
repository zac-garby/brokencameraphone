import brokencameraphone.lib.db as db

import boto3

from botocore.exceptions import ClientError
from datetime import datetime
from flask import current_app, g

AWS_REGION = "eu-west-2"

EMAIL_SENDER = "Whispering Cameraphone <noreply@whisperingcameraphone.com>"
EMAIL_CHARSET = "UTF-8"

# minimum time to wait between sending emails to the same person (seconds)
EMAIL_TIMEOUT = 60 * 2

def get_aws():
    if "boto" not in g:
        g.boto = boto3.client("ses", region_name=AWS_REGION)
    
    return g.boto

def send_email(recipient_user_id, subject, content):
    recipient = db.query(
    """
    select * from users
    where id = ?
    """, [recipient_user_id], one=True)

    if recipient == None:
        return False, "I can't find the user to email."

    last_time = recipient["last_email_timestamp"] # type: ignore
    cur_time = int(datetime.utcnow().timestamp())

    if last_time is not None and cur_time - last_time < EMAIL_TIMEOUT:
        return False, "Please wait a few minutes before requesting another email!"

    client = get_aws()

    try:
        client.send_email(
            Destination={
                "ToAddresses": [
                    recipient["email"], # type: ignore
                ],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": EMAIL_CHARSET,
                        "Data": content,
                    }
                },
                "Subject": {
                    "Charset": EMAIL_CHARSET,
                    "Data": subject,
                }
            },
            Source=EMAIL_SENDER
        )
    except ClientError as e:
        current_app.logger.error(e.response["Error"]["Message"])
        return False, "There was a problem sending an email."
    else:
        db.query(
        """
        update users
        set last_email_timestamp = ?
        where id = ?
        """, [cur_time, recipient_user_id], commit=True)
        return True, None