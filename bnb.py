import requests
import traceback
import airbnb
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

if os.path.exists('airbnb_token.txt'):
    with open('airbnb_token.txt', 'r') as file:
        airbnb_token = file.readline()
        api = airbnb.Api(access_token=airbnb_token)
else:
    if os.path.exists('airbnb_auth.json'):
        with open('airbnb_auth.json', 'r') as file:
            json_repr = file.readline()
            data = json.loads(json_repr)
            username_str = data['email']
            user_id_str = data['user_id']
            password_str = data['password']
    else:
        august_email = input("Airbnb Email Address: ")
        august_phone = input("Airbnb User ID (e.g. 12345678): ")
        august_pass = input("Airbnb Password: ")
    api = airbnb.Api(username_str, password_str)

bnbhostapi = {
  'username': user_id_str,
  'password': password_str,
  'user_id': user_id_str,
  'headers': {
    'cache-control': 'no-cache',
    'user-agent': 'Airbnb/17.50 iPad/11.2.1 Type/Tablet',
    'content-type': 'application/json',
    'accept': 'application/json',
    'accept-encoding': 'br, gzip, deflate',
    'accept-language': 'en-us',
    'x-airbnb-oauth-token': '',
    'x-airbnb-api-key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
    'x-airbnb-locale': 'en',
    'x-airbnb-currency': 'USD',
  }
}


def apilogin():
    bnbhostapi['headers']['Content-Type'] = 'application/x-www-form-urlencoded'
    response = requests.post(
        'https://api-production.august.com/session',
        headers=bnbhostapi['headers'],
        json={
            'grant_type': 'password',
            'password': bnbhostapi['password'],
            'username': bnbhostapi['username'],
        }
    )
    print(response.headers)
    oauth_token = response.headers['x-airbnb-oauth-token']
    with open('airbnb_token.txt', 'w+') as file:
        file.write(oauth_token)
    print(response.json())


#apilogin()



options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/Users/Vanze/Library/Application Support/Google/Chrome/Default")
browser = webdriver.Chrome('./chromedriver', options = options)

delay = 30

def login():
    browser.get('https://www.airbnb.com/login')

    signin_form = WebDriverWait(browser, delay).until(
        EC.presence_of_element_located((By.CLASS_NAME, "login-form")))

    # fill in username and password and hit the next button

    username = signin_form.find_element_by_id("signin_email")
    username.send_keys(username_str)

    password = signin_form.find_element_by_id("signin_password")
    password.send_keys(password_str)

    signin_form.submit()


def get_reservations():
    browser.get('https://www.airbnb.com/hosting/reservations/upcoming')
    reservations_table = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, '_iqk9th')))
    reservation_rows = WebDriverWait(browser, delay).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))
    reservation_codes = []
    for row in reservation_rows:
        row.find_element_by_class_name("_1129jucd").click()
        menu = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, '_1y3t7zhf')))
        html = menu.find_element_by_class_name('_8b6uza1').get_attribute('outerHTML')
        reservation_code = BeautifulSoup(html, 'html.parser').text.split(':')[1]
        row.find_element_by_class_name("_dus6q3a").click()
        reservation_codes.append(reservation_code)
        print(reservation_code)


#login()
#get_reservations()
browser.quit()

api.get_reviews(33558235)