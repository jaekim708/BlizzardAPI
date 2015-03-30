__author__ = 'jae'

from flask import Flask, jsonify, request, json
from enum import Enum

app = Flask(__name__)

accounts = [
    {
        'accountID': 0,
        'username': 'bob',
        'faction': 'Alliance',
        'charIDs': [0],
        'link': '{http://127.0.0.1:5000/account/bob}'

    }

]

characters = [
    {
        'charID': 0,
        'name': 'Leeroy Jenkins',
        'level': 85,
        'race': 'Human',
        'class': 'Warrior',
        'faction': 'Alliance'


    }
]


@app.route('/about', methods=['GET'])
def about():
    return jsonify({'author': 'Jae Il Kim', 'source': './app.py'})

@app.route('/account', methods=['POST', 'GET'])
def account(name=None):
    if request.method == 'POST':
        new_acc_id = len(accounts)
        new_user = {
            'accountID': new_acc_id,
            'username': request.get_json()['username'],
        }
        accounts.append(new_user)
        return jsonify({'account_id' : new_acc_id})
    if request.method == 'GET':
        return jsonify({'accounts': accounts})



if __name__ == '__main__':
    app.run(debug=True)


