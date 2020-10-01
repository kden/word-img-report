import email
import os
import re
from datetime import date, timedelta

import psycopg2
from imapclient import IMAPClient
import imaplib
from psycopg2.extras import DictCursor
from datetime import datetime

from pytitle.imap import parse_mail_date
from pytitle.pg import insert_row

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",
                       cursor_factory=DictCursor)
print("Connected to warehouse database")

OUTLOOK_USERNAME = 'cadenh@benetech.org\\bksexceptionslog@benetech.org' #os.environ.get('OUTLOOK_USERNAME', 'Missing')
OUTLOOK_PASSWORD = os.environ.get('OUTLOOK_PASSWORD', 'Missing')

WEBAPP_PATTERN = re.compile(r'\[Live:([a-z]+)\]')


date_counter = datetime.strptime("2020-08-21", '%Y-%m-%d')

# context manager ensures the session is cleaned up
with IMAPClient(host="outlook.office365.com") as client:
    print("Connecting to Outlook server...")
    client.login(OUTLOOK_USERNAME, OUTLOOK_PASSWORD)
    print("Connected to Outlook server")
    client.select_folder('Errors-Live')
    print("Selected folder Errors-Live")

    while date_counter < datetime.now() :
        # search criteria are passed in a straightforward way
        # (nesting is supported)
        print("Searching for messages on ", date_counter)
        messages = client.search([u'ON', date(date_counter.year, date_counter.month, date_counter.day)])
        print(str(len(messages)) + " message IDs retrieved")
        print("Fetching message data")
        n = 100
        sub_lists = [messages[i * n:(i + 1) * n] for i in range((len(messages) + n - 1) // n )]
        # fetch selectors are passed as a simple list of strings.]
        for sub_list in sub_lists:
            try:
                response = client.fetch(sub_list, ['FLAGS', 'RFC822.SIZE', 'RFC822'])
                # = client.fetch(messages)
                # `response` is keyed by message id and contains parsed,
                # converted response items.
                for message_id, data in response.items():
                    message = email.message_from_bytes(data[b'RFC822'])
                    print(message['Subject'] + " " + message['Date']+ " " + message['From']+ " " + message['To'])
                    try:
                        body_text = str(message.get_payload(0))
                    except TypeError:
                        print("TypeError on:")
                        print(message['Subject'] + " " + message['Date'] + " " + message['From'] + " " + message['To'])
                        body_text = str(message.get_payload())
                    mail_date = parse_mail_date(message['Date'])

                    new_record = {
                        'message_id': message['Message-ID'],
                        'subject': message['Subject'],
                        'to_address': message['To'],
                        'from_address':  message['From'],
                        'message_date':  mail_date.date(),
                        'message_datetime':  mail_date,
                        'application': '',
                        'body_text':  body_text,
                    }
                    match = WEBAPP_PATTERN.search(message['Subject'])
                    if match is not None:
                        new_record['application'] = match.group(1)
                    email_message_id = insert_row(con,'email_message','email_message_id',new_record )
            except IMAPClient.Error as e:
                print("Error on:")
                print(message['Subject'] + " " + message['Date'] + " " + message['From'] + " " + message['To'])
                print(e)

        date_counter = date_counter + timedelta(days=1)





