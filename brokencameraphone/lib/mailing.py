import boto3

from botocore.exceptions import ClientError
from flask import current_app, g

AWS_REGION = "eu-west-2"

EMAIL_SENDER = "Whispering Cameraphone <noreply@whisperingcameraphone.com>"
EMAIL_CHARSET = "UTF-8"

def get_aws():
    if "boto" not in g:
        g.boto = boto3.client("ses", region_name=AWS_REGION)
    
    return g.boto

def send_email(recipient, subject, content):
    client = get_aws()

    try:
        client.send_email(
            Destination={
                "ToAddresses": [
                    recipient,
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
        return False
    else:
        return True