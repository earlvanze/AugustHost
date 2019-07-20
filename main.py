from __future__ import print_function
import requests
import os
import json
import traceback
from flask import Flask, flash, render_template, redirect, url_for, session, request, jsonify
from datetime import datetime
#from bnb import *
from gunicornconf import *

AUGUST_API_KEY = '79fd0eb6-381d-4adf-95a0-47721289d1d9'
AUGUST_EMAIL = '88madisonave@gmail.com'
AUGUST_PASS = ''    # PRIVATE!! REMOVE BEFORE POSTING TO GITHUB

with open('august_auth.json', 'r') as file:
        json_repr = file.readline()
        data = json.dumps(json_repr)
        AUGUST_EMAIL = data['email']
        AUGUST_PASS = data['password']

# Flask App configuration
app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(24)


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print(request.get_json())
        return jsonify(data={'message': "Success"})
    return render_template('index.html')


def auth():
    response = requests.post(
        'https://api-production.august.com/session',
        headers = {'Content-Type': 'application/json', 'x-august-api-key': AUGUST_API_KEY},
        json = {'identifier': 'phone:+15188828383', 'installId':'0', 'password': AUGUST_PASS}
    )

    access_token = response.headers['x-august-access-token']

    response = requests.post(
        'https://api-production.august.com/validation/email',
        headers = {'Content-Type': 'application/json', 'x-august-api-key': AUGUST_API_KEY, 'x-august-access-token': access_token},
        json = {'value': AUGUST_EMAIL}
    )
    verification_code = input("Please enter the verification code from your email: ")
    print("verifying...")
    response = requests.post(
        'https://api-production.august.com/validate/email',
        headers = {'Content-Type': 'application/json', 'x-august-api-key': AUGUST_API_KEY, 'x-august-access-token': access_token},
        json = {'email': AUGUST_EMAIL, 'code': verification_code}
    )
    access_token = response.headers['x-august-access-token']
    print(response)
    with open('access_token.txt', 'w+') as file:
        file.write(access_token)
    return access_token


def get_locks(august_access_token):
    locks = []
#    print(august_access_token)
    print("getting locks...")
    response = requests.get(
        'https://api-production.august.com/users/locks/mine',
        headers = {'Content-Type': 'application/json', 'x-august-api-key': AUGUST_API_KEY, 'x-august-access-token': august_access_token}
    )
    try:
        for k, v in response.json().items():
            v["LockId"] = k
            locks.append(v)
    except TypeError:
        print(v)
    return locks


def get_pins(lock_id, august_access_token):
    print("getting PINs...")
    response = requests.get(
        f'https://api-production.august.com/locks/{lock_id}/pins',
        headers = {'Content-Type': 'application/json', 'x-august-api-key': AUGUST_API_KEY, 'x-august-access-token': august_access_token}
    )
    return list(response.json().items())


def get_expired_pins(loaded_pins):
    expired_pins = []
    print(datetime.now().isoformat())
    for pin in loaded_pins:
#        print(pin)
        try:
            if DictQuery(pin).get('accessEndTime') < datetime.now().isoformat() and DictQuery(pin).get('accessType') != 'always':
                expired_pins.append(pin)
        except:
#            traceback.print_exc()
            continue
    return expired_pins


def delete_expired_pins(expired_pins, august_access_token):
    for entry in expired_pins:
        lock_id = DictQuery(entry).get('lockID')
        user_id = DictQuery(entry).get('userID')
        pin = DictQuery(entry).get('pin')
        requests.put(
            f'https://api-production.august.com/locks/{lock_id}/users/{user_id}/pin',
            headers={'Content-Type': 'application/json', 'x-august-api-key': AUGUST_API_KEY,
                     'x-august-access-token': august_access_token},
            json={
	            "state": "delete",
	            "action": "intent",
	            "pin": pin
            }
        )

        response = requests.put(
            f'https://api-production.august.com/locks/{lock_id}/users/{user_id}/pin',
            headers={'Content-Type': 'application/json', 'x-august-api-key': AUGUST_API_KEY,
                     'x-august-access-token': august_access_token},
            json={
                "state": "delete",
                "action": "commit",
                "pin": pin
            }
        )
        print(response.json())
    print("Expired PINs deleted")

def batch_delete_expired_pins(loaded_pins, locks, lock_num, august_access_token):
    # Find and Delete Expired PINs
    expired_pins = get_expired_pins(loaded_pins)
    print("\nExpired PINs:")
    print(*expired_pins, sep="\n")
    delete_expired_pins(expired_pins, august_access_token)

    # Confirm
    pins = get_pins(locks[lock_num]['LockId'], august_access_token)
    loaded_pins = pins[1][1]
    expired_pins = get_expired_pins(loaded_pins)
    print("\nExpired PINs:")
    print(*expired_pins, sep="\n")



def get_pin_by_first_name(first_name, pins):
    results = list(filter(lambda person: person['firstName'].title() == first_name.title(), pins))
    for result in results:
        first = DictQuery(result).get('firstName')
        last = DictQuery(result).get('lastName')
        pin = DictQuery(result).get('pin')
        accessStartTime = DictQuery(result).get('accessStartTime')
        print(first, last, pin, accessStartTime)
    return results


def august_main():
#    get_reservations()
#    browser.quit()

    if os.path.exists('access_token.txt'):
        with open('access_token.txt', 'r') as file:
            august_access_token = file.readline()
    else:
        august_access_token = auth()
    locks = get_locks(august_access_token)
    for i in range(0, (len(locks))):
        print(f'{i+1}) ', locks[i]['LockName'])
    lock_num = int(input("Select a lock: "))-1
    while(lock_num not in [0, 1, 2]):
        lock_num = int(input("Invalid selection. Select a lock: "))
    pins = get_pins(locks[lock_num]['LockId'], august_access_token)
    loaded_pins = pins[1][1]
    batch_delete_expired_pins(loaded_pins, locks, lock_num, august_access_token)

    # Look up guest by first name so you can retrieve PIN or modify access (TO-DO)
    first_name = input("Enter guest's first name: ")
    print(get_pin_by_first_name(first_name, loaded_pins))


# Used to search for keys in nested dictionaries and handles when key does not exist
# Example: DictQuery(dict).get("dict_key/subdict_key")
class DictQuery(dict):
    def get(self, path, default = None):
        keys = path.split("/")
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [ v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break;

        return val


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    august_main()

    # This allows us to use a plain HTTP callback
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
    options = {
        'bind': '%s:%s' % ('127.0.0.1', '8080'),
        'workers': number_of_workers(),
    }
    app.run(host='0.0.0.0', port=8080, ssl_context='adhoc')
    StandaloneApplication(app, options).run()

if __name__ == '__main__':
    main()