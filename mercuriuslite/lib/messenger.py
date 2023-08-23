from __future__ import print_function

import base64
from email.message import EmailMessage

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://mail.google.com/']

def gmail_send_message(cfg, title, content):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    #creds, _ = google.auth.default()
    cred_path=cfg['MERCURIUS']['cred_path']
    cred_file=os.path.join(cred_path,'token.json')
    if os.path.exists(cred_file):
        creds = Credentials.from_authorized_user_file(cred_file, SCOPES)
    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()
        message.set_content(content)

        message['To'] = cfg['MERCURIUS']['recipient'] 
        message['From'] = cfg['MERCURIUS']['sender']
        message['Subject'] = title

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


if __name__ == '__main__':
    gmail_send_message()