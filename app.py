from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url, asynchronous
from tornado.escape import json_encode, json_decode
from tornado.concurrent import Future
from tornado.process import fork_processes
from tornado import gen

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
"""


accounts = [
    {
        'account_id': 0,
        'username': 'bob',
        'faction': 'Alliance',
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
        'race': 'Human',
        'class': 'Warrior',
        'faction': 'Alliance',
        'active': True

    }
]

FACTIONS = {'horde': ['orc', 'tauren', 'blood elf'],
            'alliance': ['human', 'gnome', 'worgen']}

class BaseHandler(RequestHandler):
    def write_error(self, status_code, message=None, **kwargs):
        if(message is not None):
            self.write(json_encode({'Error code': status_code,
                                    'Description': message}))
        else:
            self.write(json_encode({'Error code': status_code}))
        self.set_status = status_code
        self.finish()

class AboutHandler(BaseHandler):
    """
    curl http://127.0.0.1:5000/account
    """
    @gen.coroutine
    def get(self):
        response = yield self.get_about()
        self.write(response)

    def get_about(self):
        raise gen.Return(json_encode({'author': 'Jae Il Kim',
                                      'source': './app.py'}))

class AccountHandler(BaseHandler):
    """
    curl -X POST http://127.0.0.1:5000/account -d '{"username" : "Jae"}'
    curl -X GET http://127.0.0.1:5000/account
    """
    @gen.coroutine
    def get(self):
        response = yield self.get_account()
        self.write(response)

    @gen.coroutine
    def get_account(self):
        raise gen.Return(json_encode(accounts))

    @gen.coroutine
    def post(self):
        response = yield self.post_account(self.request.body)
        self.write(response)

    @gen.coroutine
    def post_account(self, input):
        self.set_header("Content-Type", "application/json")
        input = json_decode(self.request.body)
        try:
            new_username = input['username']
        except KeyError, e:
            self.write_error(404, 'Ill-formed or misspelled request.')
            return

        new_acc_id = len(accounts)

        if new_username == None or new_username == '':
            self.write_error(400, 'Account name not specified.')
            return

        if len([acc for acc in accounts if
                acc['username'] == new_username]) != 0:
            self.write_error(400, 'Account name already taken.')
            return

        new_user = {
            'account_id': new_acc_id,
            'username': new_username,
            'char_ids': [],
            'faction': None,
            'deleted_char_ids': [],
            'link': '{http://127.0.0.1:5000/account/' + new_username + '}'
        }
        accounts.append(new_user)
        raise gen.Return(json_encode({'account_id' : new_acc_id}))


class CharactersHandler(BaseHandler):
    """
    curl -X POST http://127.0.0.1:5000/account/Jae/characters -d '{"name": "Jar", "race": "orc", "class": "warrior", "faction": "horde", "level": 80}'
    curl -X GET http://127.0.0.1:5000/account/bob/characters
    """
    @gen.coroutine
    def get(self, account_name):
        response = yield self.get_characters(account_name)
        self.write(response)

    @gen.coroutine
    def get_characters(self, account_name):
        user_acc = [acc for acc in accounts if acc['username'] == account_name]
        if len(user_acc) == 0:
            self.write_error(404, 'Specified user not found.')
            return
        user_acc = user_acc[0]

        acc_char_ids = user_acc['char_ids']
        acc_chars = [c for c in characters if c['char_id'] in acc_char_ids]

        if len(user_acc['char_ids']) == 0:
            raise gen.Return(json_encode(
                {'message': 'This account does not have any active '
                            'characters.'}))
        else:
            raise gen.Return(json_encode(
                {'account_id': user_acc['account_id'],'characters': acc_chars}))

    @gen.coroutine
    def post(self, account_name):
        response = yield self.post_characters(self.request.body, account_name)
        self.write(response)

    @gen.coroutine
    def post_characters(self, input, account_name):
        try:
            input_dict = json_decode(input)
            char_name = input_dict['name']
            char_race = input_dict['race']
            char_class = input_dict['class']
            char_faction = input_dict['faction']
            char_level = input_dict['level']
        except KeyError, e:
            self.write_error(404, 'Ill-formed or misspelled request.')
            return

        user_acc = [acc for acc in accounts if acc['username'] == account_name]
        if len(user_acc) == 0:
            self.write_error(404, 'Specified user not found.')
            return
        user_acc = user_acc[0]

        if char_level < 1 or char_level > 85:
            self.write_error(400, 'Character levels must be between 1 and 85')
            return

        if ((char_race in FACTIONS['horde'] and char_faction == 'alliance') or
                (char_race in FACTIONS['alliance'] and char_faction == 'horde')):
            self.write_error(400, 'The new character\'s race is not '
                                  'compatible with its given faction.')
            return

        if (char_class == 'druid' and
                (char_race != 'tauren' and char_race != 'worgen')):
            self.write_error(400, 'Only Tauren or Worgen can be druids.')

        if (char_class == 'warrior' and char_race == 'blood elf'):
            self.write_error(400, 'Blood elves cannot be warriors.')
            return

        account_faction = user_acc['faction']
        if account_faction is not None and account_faction != char_faction:
            self.write_error(400, 'Account already has characters that are the '
                                  'oopposite faction of the new character.')
            return

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
        raise gen.Return(json_encode({'character_id': new_char_id}))

class AccDeleteHandler(BaseHandler):
    """
    curl -X DELETE http://127.0.0.1:5000/account/bob
    """
    @gen.coroutine
    def delete(self, account_name):
        response = yield self.delete_account(account_name)
        self.write(response)

    @gen.coroutine
    def delete_account(self, account_name):
        user_acc = [acc for acc in accounts if acc['username'] == account_name]

        if len(user_acc) == 0:
            self.write_error(404, 'Specified user not found.')
            return
        user_acc = user_acc[0]

        for char_id in user_acc['char_ids']:
            del characters[char_id]
        del accounts[user_acc['account_id']]

        raise gen.Return(json_encode({'message': 'Account -' + account_name +
                                   '- successfully deleted.'}))


class CharDeleteHandler(BaseHandler):
    """
    curl -X DELETE http://127.0.0.1:5000/account/bob/characters/Leeroy%20Jenkins
    """
    @gen.coroutine
    def delete(self, account_name, char_name):
        response = yield self.delete_char(account_name, char_name)
        self.write(response)

    @gen.coroutine
    def delete_char(self, account_name, char_name):
        user_acc = [acc for acc in accounts if acc['username'] == account_name]

        if len(user_acc) == 0:
            self.write_error(404, 'Specified user not found.')
            return
        user_acc = user_acc[0]

        user_chars = user_acc['char_ids']
        character = [characters[c] for c in user_chars
                     if characters[c]['name'] == char_name]

        if len(character) == 0:
            self.write_error(404, 'Specified character not found.')
            return
        char_to_del = character[0]

        user_acc['char_ids'].remove(char_to_del['char_id'])
        user_acc['deleted_char_ids'].append(char_to_del['char_id'])

        if len(user_acc['char_ids']) == 0:
            user_acc['faction'] = None

        char_to_del['active'] = False

        raise gen.Return(json_encode({'message': 'Character -' + char_name +
                                   '- belonging to -' + account_name +
                                   '- was successfully deleted.'}))

def make_app():
    return Application([url(r"/about", AboutHandler),
                        url(r"/account", AccountHandler),
                        url(r"/account/(\w+)/characters", CharactersHandler),
                        url(r"/account/(\w+)", AccDeleteHandler),
                        url(r"/account/(\w+)/characters/(\w+)",
                            CharDeleteHandler)], debug=True)

def main():
    app = make_app()
    #server = tornado.httpserver.HTTPServer(app)
    #server.bind(5000)
    #server.start(0)
    app.listen(5000)
    IOLoop.current().start()

if __name__ == '__main__':
    main()
