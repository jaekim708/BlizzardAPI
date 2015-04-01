from flask import Flask, jsonify, request, abort, make_response, render_template
from enum import Enum

"""
Big:
    move to database
    figure out how to host website

Small:
    clean up error message that occurs if not all required fields are provided
    error if delete function called w/Empty usernames
    should account deletion irreversibly delete all characters?

    check user/character name validity

    Undeletion -
        prevent undeletion of horde chars while alliance, vice versa
        modify active status & active chars fields of char & user

    check username at least 1 character.
"""
app = Flask(__name__)

accounts = [
    {
        'account_id': 0,
        'username': 'bob',
        'faction': 'alliance',
        'char_ids': [0],
        'deleted_char_ids': [],
        'link': '{http://127.0.0.1:5000/account/bob}'

    }

]

characters = [
    {
        'char_id': 0,
        'name': 'Leeroy Jenkins',
        'level': 85,
        'race': 'human',
        'class': 'warrior',
        'faction': 'alliance',
        'active': True

    }
]

FACTIONS = {'horde': ['orc', 'tauren', 'blood elf'],
            'alliance': ['human', 'gnome', 'worgen']}


@app.route('/about', methods=['GET'])
def about():
    """
    curl http://127.0.0.1:5000/account
    """
    return jsonify({'author': 'Jae Il Kim', 'source': './app.py'})

@app.route('/account', methods=['POST', 'GET'])
def account():
    """
    curl -H "Content-type: application/json" -X POST http://127.0.0.1:5000/account -d '{"username" : "Jae"}'
    curl -H "Content-type: application/json" -X POST http://127.0.0.1:5000/account
    """
    if request.method == 'POST':
        try:
            new_username = request.get_json(force=True)['username']
        except KeyError, e:
            raise InvalidInput('Ill-formed or misspelled request.',
                               status_code=404)
        new_acc_id = len(accounts)

        if new_username == None or new_username == '':
            raise InvalidInput('Account name not specified.', status_code=400)

        if len([acc for acc in accounts if
                acc['username'] == new_username]) != 0:
            raise InvalidInput('Account name already taken.', status_code=400)

        new_user = {
            'account_id': new_acc_id,
            'username': new_username,
            'char_ids': [],
            'faction': None,
            'link': '{http://127.0.0.1:5000/account/' + new_username + '}'
        }
        accounts.append(new_user)
        return jsonify({'account_id' : new_acc_id})
    if request.method == 'GET':
        return jsonify({'accounts': accounts})

@app.route('/account/<account_name>/characters', methods=['POST'])
def new_char(account_name):
    """
    curl -H "Content-type: application/json" -X POST http://127.0.0.1:5000/account/Jae/characters -d '{"name": "Jar", "race": "orc", "class": "warrior", "faction": "horde", "level": 80}'
    """
    try:
        char_name = request.get_json(force=True)['name']
        char_race = request.get_json(force=True)['race'].lower()
        char_class = request.get_json(force=True)['class'].lower()
        char_faction = request.get_json(force=True)['faction'].lower()
        char_level = request.get_json(force=True)['level']
    except KeyError, e:
        raise InvalidInput('Ill-formed or misspelled request.',
                           status_code=404)

    user_acc = [acc for acc in accounts if acc['username'] == account_name]
    if len(user_acc) == 0:
        raise InvalidInput('Specified user not found.', status_code=404)
    user_acc = user_acc[0]

    if char_level < 1 or char_level > 85:
        raise InvalidInput('Character levels must be between 1 and 85',
                           status_code=400)

    if ((char_race in FACTIONS['horde'] and char_faction == 'alliance') or
            (char_race in FACTIONS['alliance'] and char_faction == 'horde')):
        raise InvalidInput('The new character\'s race is not compatible with '
                           'its given faction.', status_code=400)

    if (char_class == 'druid' and
            (char_race != 'tauren' and char_race != 'worgen')):
        raise InvalidInput('Only Tauren or Worgen can be druids.',
                           status_code=400)
    if (char_class == 'warrior' and char_race == 'blood elf'):
        raise InvalidInput('Blood elves cannot be warriors.', status_code=400)

    account_faction = user_acc['faction']
    if account_faction is not None and account_faction != char_faction:
        raise InvalidInput('Account already has characters that are the '
                           'opposite faction of the new character.',
                           status_code=400)

    new_char_id = len(characters)
    new_char = {
        'char_id': new_char_id,
        'name': char_name,
        'level': char_level,
        'race': char_race,
        'class': char_class,
        'faction': char_faction
    }
    characters.append(new_char)
    user_acc['char_ids'].append(new_char_id)
    user_acc['faction'] = char_faction
    return jsonify({'character_id': new_char_id})


@app.route('/account/<account_name>', methods=['DELETE'])
def delete_account(account_name):
    """
     curl -H "Content-type: application/json" -X DELETE http://127.0.0.1:5000/account/bob
    """
    user_acc = [acc for acc in accounts if acc['username'] == account_name]

    if len(user_acc) == 0:
        raise InvalidInput('Specified user not found.', status_code=404)
    user_acc = user_acc[0]

    for char_id in user_acc['char_ids']:
        del characters[char_id]
    del accounts[user_acc['account_id']]

    return jsonify({'message': 'Account -' + account_name +
                               '- successfully deleted.'})

@app.route('/account/<account_name>/characters/<char_name>', methods=['DELETE'])
def delete_character(account_name, char_name):
    """
    curl -H "Content-type: application/json" -X DELETE http://127.0.0.1:5000/account/bob/characters/Leeroy%20Jenkins
    """
    user_acc = [acc for acc in accounts if acc['username'] == account_name]

    if len(user_acc) == 0:
        raise InvalidInput('Specified user not found.', status_code=404)
    user_acc = user_acc[0]

    user_chars = user_acc['char_ids']
    character = [characters[c] for c in user_chars
                 if characters[c]['name'] == char_name]

    if len(character) == 0:
        raise InvalidInput('Specified character not found.', status_code=404)
    char_to_del = character[0]

    del user_acc['char_ids'][char_to_del['char_id']]
    user_acc['deleted_char_ids'].append(char_to_del['char_id'])

    if len(user_acc['char_ids']) == 0:
        user_acc['faction'] = None

    char_to_del['active'] = False

    return jsonify({'message': 'Character -' + char_name +
                               '- belonging to -' + account_name +
                               '- was successfully deleted.'})

@app.route('/account/<account_name>/characters', methods=['GET'])
def get_chars(account_name):
    """
    curl -H "Content-type: application/json" -X GET http://127.0.0.1:5000/account/bob/characters

    """
    user_acc = [acc for acc in accounts if acc['username'] == account_name]
    if len(user_acc) == 0:
        raise InvalidInput('Specified user not found.', status_code=404)
    user_acc = user_acc[0]

    acc_char_ids = user_acc['char_ids']
    acc_chars = [c for c in characters if c['char_id'] in acc_char_ids]

    if len(user_acc['char_ids']) == 0:
        return jsonify({'message': 'This does not have any active characters.'})
    else:
        return jsonify({'account_id': user_acc['account_id'],
                        'characters': acc_chars})


class InvalidInput(Exception):
    """
    From http://flask.pocoo.org/docs/0.10/patterns/apierrors/
    """
    def __init__(self, message, status_code, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['Error'] = self.message
        return rv

@app.errorhandler(InvalidInput)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    app.run(debug=True)


