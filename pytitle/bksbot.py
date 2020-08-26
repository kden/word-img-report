import os
import requests

CATALOG_URL="https://catalog.bookshare.org"
BKS_USERNAME = os.environ.get('V2_API_USERNAME', 'Missing')
BKS_PASSWORD = os.environ.get('V2_API_PASSWORD', 'Missing')
X_BOOKSHARE_ORIGIN = os.environ.get('X_BOOKSHARE_ORIGIN', '12345678')
BKS_HEADERS = {'X-Bookshare-Origin': X_BOOKSHARE_ORIGIN}

login_params = {
    'j_userName': BKS_USERNAME,
    'j_password': BKS_PASSWORD,
    'signInSubmit': "Sign In"
}


def get_session():
    s = requests.Session()
    return refresh_login(s)


def refresh_login(s):
    s.headers.update(BKS_HEADERS)
    login_response = s.post(CATALOG_URL + '/login', params=login_params)

    print("Login Response: " + str(login_response.status_code))
    if login_response.status_code != 200:
        print(login_response.content)
        return None
    return s