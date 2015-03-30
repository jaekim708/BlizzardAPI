__author__ = 'jae'

from flask import Flask, jsonify, request

app = Flask(__name__)

accounts = [
    {
        'accountID': 3,
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


@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'GET':
        return jsonify({'accounts': accounts}), 200

if __name__ == '__main__':
    app.run(debug=True)


