from __future__ import print_function

import base64
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

from . import utils, mathlib
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
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(cred_path,'client_secret.json'), SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open(cred_file, 'w') as token:
        token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    
    # Create a message object
    message = MIMEMultipart()
    
    # Set the message body
    message['To'] = cfg['MERCURIUS']['recipient'] 
    message['From'] = cfg['MERCURIUS']['sender']
    message['Subject'] = title
    
    text = MIMEText(content, 'html')
    message.attach(text)

    # Attach a file, if any
    attach_files=utils.parse_file_names(cfg['SCHEMER']['attach_files'])
    if attach_files !=[]:
        for attach_file in attach_files:
            with open(attach_file, 'rb') as file:
                attachment = MIMEImage(file.read(), _subtype='png')
                attachment.add_header(
                    'Content-Disposition', 'attachment', filename=attach_file.split('/')[-1])
                message.attach(attachment)
    # Encode the message in base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Send the message
    try:
        send_message = service.users().messages().send(
            userId='me', body={'raw': raw_message}).execute()
        print(F'Sent message: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message

def parse_financing_meta(minerva, meta_dic):
    try:
        nominate_curr=minerva.cfg['S_fund_financing']['nominated_currency'].lower()
    except KeyError:
        nominate_curr='cny'
    track=minerva.track
    meta_dic['约定年化利率']=utils.fmt_value(
        mathlib.dr2ar(minerva.fin_nrdr)-1,vtype='pct')
    #meta_dic['付息频率']=fin_act.loc[fin_act['action']=='payment']['value'].values[0]
    meta_dic['今日应记利息']=utils.fmt_value(minerva.fin_daily_interest,vtype=nominate_curr)
    meta_dic['当前本金结余']=utils.fmt_value(
        minerva.fin_fund,vtype=nominate_curr,pos_sign=False)
    meta_dic['当前出借天数']=str((track.index[-1]-track.index[0]).days+1)+'天'
    meta_dic['约定付息频率']=minerva.fin_pay_frq
    meta_dic['当前本息总额']=utils.fmt_value(
        minerva.fin_fund+minerva.fin_acc_unpaid,vtype=nominate_curr,pos_sign=False)    
    meta_dic['累积已付利息']=utils.fmt_value(
        minerva.fin_acc_pay,vtype=nominate_curr)
    meta_dic['当前未付利息']=utils.fmt_value(
        minerva.fin_acc_unpaid,vtype=nominate_curr) 
    meta_dic['累积本息总额']=utils.fmt_value(
        minerva.fin_fund+minerva.fin_acc_pay+minerva.fin_acc_unpaid,vtype=nominate_curr,pos_sign=False)    
    meta_dic['累积总回报率']=utils.fmt_value(
        track.iloc[-1]["accum_return"]-1,vtype='pct')+' （时间加权）'
    return meta_dic
    
if __name__ == '__main__':
    gmail_send_message()