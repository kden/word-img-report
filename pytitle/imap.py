from datetime import datetime

def list_folders(client):
    folders = client.list_folders()
    for (flags, delimiter, name) in folders:
        print("Name: " + name)
        print("Delimiter: " + str(delimiter))
        print("Flags: " + str(flags))


def parse_mail_date(mail_date):
    # Wed, 01 Jan 2020 01:41:09 +0000 (UTC)
    result = None
    try:
        result = datetime.strptime(mail_date, '%a, %d %b %Y %H:%M:%S +0000 (UTC)')
    except ValueError as e:
        result = datetime.strptime(mail_date, '%a, %d %b %Y %H:%M:%S +0000')
    return result
