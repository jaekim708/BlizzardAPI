from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.escape import json_encode, json_decode
from tornado import gen

"""
Small:

    check user/character name validity

    Undeletion -
        modify active status & active chars fields of char & user
"""


accounts = [
    # {
    #     Sample Entry:
    #     'account_id': 0,
    #     'username': 'bob',
    #     'faction': 'Alliance',
    #     'char_ids': [0],
    #     'deleted_char_ids': [],
    #     'link': '{http://127.0.0.1:5000/account/bob}'
    #
    # }

]

characters = [
    # {
    #     Sample Entry:
    #     'char_id': 0,
    #     'name': 'LeeroyJenkins',
    #     'level': 85,
    #     'race': 'Human',
    #     'class': 'Warrior',
    #     'faction': 'Alliance',
    #     'active': True
    #
    # }
]

RACES = frozenset(['Orc', 'Tauren', 'Blood Elf', 'Human', 'Gnome', 'Worgen'])
CLASSES = frozenset(['Warrior', 'Druid', 'Death Knight', 'Mage'])
HORDE = frozenset(['Orc', 'Tauren', 'Blood Elf'])
ALLIANCE = frozenset(['Human', 'Gnome', 'Worgen'])

class BaseHandler(RequestHandler):
    def write_error(self, status_code, message=None, **kwargs):
        self.set_status = status_code
        if(message is not None):
            self.finish(json_encode({'Error code': status_code,
                                    'Description': message}))
        else:
            self.finish(json_encode({'Error code': status_code}))

    def write(self, chunk):
        if chunk is not None:
            super(BaseHandler, self).write(chunk)

class AboutHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        """
        Inputs:
            None
        Usage:
            curl http://127.0.0.1:5000/account

        Returns 200, with a body of {"author": "Jae Il Kim",
                                     "source": "BlizzardAPI.py"}
        """
        response = yield self.get_about()
        self.write(response)

    @gen.coroutine
    def get_about(self):
        raise gen.Return(json_encode(
            {'author': 'Jae Il Kim',
             'source': 'BlizzardAPI.py'}))

class AccountHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        """
        Inputs :
            None
        Usage:
            curl -X GET http://127.0.0.1:5000/account

        Returns 200, with a body containing the accounts field described
        at the top of this file.
        """
        response = yield self.get_account()
        self.write(response)

    @gen.coroutine
    def get_account(self):
        raise gen.Return(json_encode(accounts))

    @gen.coroutine
    def post(self):
        """
        Inputs:
            {"username" : "NewUsername"}
        Usage:
            curl -X POST http://127.0.0.1:5000/account
            -d '{"username" : "NewUsername"}'

        Returns 200, with a body of {"account_id" : new_acc_id}

        Creates a new account with the given username. Refer to the accounts
        field at the top of this file for the default values new accounts
        are assigned.

        Blizzard BattleTags (accounts here) are 3 to 12 characters long and
        cannot contain special characters, start with a number, or contain
        spaces. BattleTags are not necessarily unique, as the BattleTag Code
        (account_id here) can uniquely identify accounts with the same
        BattleTag.
        """
        response = yield self.post_account()
        self.write(response)

    @gen.coroutine
    def post_account(self):
        self.set_header("Content-Type", "application/json")
        input = json_decode(self.request.body)
        try:
            new_username = input['username']
        except KeyError, e:
            self.write_error(404, 'Ill-formed, incomplete, or misspelled '
                                  'request.')
            return

        if new_username == None:
            self.write_error(400, 'Please provide an account name.')
            return

        if len(new_username) > 12 or len(new_username) < 3:
            self.write_error(400, 'Account name must be between 3 to 12 '
                                  'characters.')
            return

        if new_username[0].isdigit():
            self.write_error(400, 'Account name cannot begin with a number')
            return

        if not new_username.isalnum:
            self.write_error(400, 'Account name cannot contain'
                                  'non-alphanumeric characters')
            return

        new_acc_id = len(accounts)
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
    @gen.coroutine
    def get(self, account_name):
        """
        Inputs:
            account name in URL
        Usage:
            curl -X GET http://127.0.0.1:5000/account/<account_name>/characters

        Returns 200, with a body containing the all the characters belonging to
        the specified account. Note that this function DOES return the
        deleted characters belonging to the accountholder. Refer to the top
        of this file for information on what the characters field holds.
        """
        response = yield self.get_characters(account_name)
        self.write(response)

    @gen.coroutine
    def get_characters(self, account_name):
        user_acc = [acc for acc in accounts if acc['username'] == account_name]
        if len(user_acc) == 0:
            self.write_error(404, 'Specified user not found.')
            return
        user_acc = user_acc[0]

        acc_char_ids = user_acc['char_ids'] + user_acc['deleted_char_ids']
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
        """
        Inputs:
            account name in URL, {"name": "char_name",
                                  "race": "char_race", "class": "char_class",
                                  "faction": "char_faction",
                                  "level": char_level}
        Usage:
            curl -X POST
            http://127.0.0.1:5000/account/<account_name>/characters
            -d '{"name": "char_name", "race": "char_race",
                 "class": "char_class", "faction": "char_faction",
                 "level": char_level}'


        Returns 200, with a body of {"character_id" : new_char_id}

        Creates a new character with the given traits and places it on
        the specified accountholder. Note that all traits specified in
        the characters field must be provided.

        Character creation must follow these rules:
            Character name must be fully unique among all other characters,
                be composed only of alphabetical letters, and between 3 to 12
                characters.
            Character level must be from 1 to 85.
            Allowed races are Orc, Tauren, Blood Elf, Human, Gnome, Worgen.
            Allowed classes are Warrior, Druid, Death Knight, Mage.
            Orc, Tauren, and Blood Elf races are exclusively Horde.
            Human, Gnome, and Worgen races are exclusively Alliance.
            Only Taurens and Worgen can be Druids.
            Blood Elves cannot be Warriors.
            A player can only have all Horde or all Alliance active characters.

        This function can also be used to undelete characters. The provided
        character trait inputs must exactly match the character traits of
        the deleted character. If the specified character is currently deleted,
        belongs to the accountholder, and the faction of the
        to-be-undeleted character is the same as the faction that the
        accountholder is currently aligned to, the character will be undeleted.
        """
        response = yield self.post_characters(self.request.body, account_name)
        self.write(response)

    @gen.coroutine
    def post_characters(self, input, account_name):
        try:
            input_dict = json_decode(input)
            char_name = input_dict['name']
            char_race = input_dict['race'].lower().capitalize()
            char_class = input_dict['class'].lower().capitalize()
            char_faction = input_dict['faction'].lower().capitalize()
            char_level = input_dict['level']
        except KeyError, e:
            self.write_error(404, 'Ill-formed, incomplete, or '
                                  'misspelled request.')
            return

        user_acc = [acc for acc in accounts if acc['username'] == account_name]
        if len(user_acc) == 0:
            self.write_error(404, 'Specified user not found.')
            return
        user_acc = user_acc[0]

        if char_name == None:
            self.write_error(400, 'Please provide an account name.')
            return

        if len(char_name) > 12 or len(char_name) < 3:
            self.write_error(400, 'Character name must be between 3 to 12 '
                                  'characters.')
            return

        if not char_name.isalpha:
            self.write_error(400, 'Character name must only be composed of '
                                  'alphabetical letters.')
            return

        char_check = [char for char in characters if char['name'] == char_name]
        if len(char_check) > 0:
            existing_char = char_check[0]
            if existing_char['username'] == account_name:
                if existing_char != input_dict:
                    self.write_error(400, 'To undelete a character, please '
                                          'provide the character\'s information'
                                          ' exactly as it was at the time of '
                                          'deletion.')
                    return
                if (user_acc['faction'] != None and
                        existing_char['faction'] == user_acc['faction']):
                    self.write_error(400, 'This character cannot be undeleted'
                                          ' because its faction does not '
                                          'match with the current faction of '
                                          'the account.')
                    return

                existing_char['active'] = True
                existing_char_id = existing_char['char_id']
                del user_acc['deleted_char_ids'][existing_char_id]
                user_acc['char_ids'].append(existing_char_id)
                user_acc['faction'] = existing_char['faction']

                raise gen.Return(json_encode({'character_id':
                                                  existing_char_id}))

            else:
                self.write_error(400, 'Provided character name has already '
                                      'been taken.')
                return

        if char_level < 1 or char_level > 85:
            self.write_error(400, 'Character levels must be between 1 and 85')
            return

        if char_race not in RACES:
            self.write_error(400, 'Please provide a valid character race.')
            return

        if char_class not in CLASSES:
            self.write_error(400, 'Please provide a valid character class.')
            return

        if (char_race in HORDE and char_faction == 'Alliance' or
                char_race in ALLIANCE  and char_faction == 'horde'):
            self.write_error(400, 'The new character\'s race is not '
                                  'compatible with its given faction.')
            return

        if (char_class == 'Druid' and
                (char_race != 'Tauren' and char_race != 'Worgen')):
            self.write_error(400, 'Only Tauren or Worgen can be druids.')
            return

        if (char_class == 'Warrior' and char_race == 'Blood Elf'):
            self.write_error(400, 'Blood Elves cannot be warriors.')
            return

        account_faction = user_acc['faction']
        if account_faction is not None and account_faction != char_faction:
            self.write_error(400, 'Account already has characters that are the '
                                  'opposite faction of the new character.')
            return

        new_char_id = len(characters)
        new_char = {
            'char_id': new_char_id,
            'name': char_name,
            'level': char_level,
            'race': char_race,
            'class': char_class,
            'faction': char_faction,
            'active': True
        }
        characters.append(new_char)
        user_acc['char_ids'].append(new_char_id)
        user_acc['faction'] = char_faction
        raise gen.Return(json_encode({'character_id': new_char_id}))

class AccDeleteHandler(BaseHandler):
    @gen.coroutine
    def delete(self, account_name):
        """
        Inputs:
            account name in URL
        Usage:
            curl -X DELETE http://127.0.0.1:5000/account/<account_name>


        Returns 200, with a body of
        {'message': 'Account -<account_name>- successfully deleted.'}

        Deletes the specified account. This also deletes all characters,
        active and deleted, associated to this account.
        """
        response = yield self.delete_account(account_name)
        self.write(response)

    @gen.coroutine
    def delete_account(self, account_name):
        user_acc = [acc for acc in accounts if acc['username'] == account_name]

        if len(user_acc) == 0:
            self.write_error(404, 'Specified user not found.')
            return
        user_acc = user_acc[0]

        for char_id in user_acc['char_ids'] + user_acc['deleted_char_ids']:
            del characters[char_id]
        del accounts[user_acc['account_id']]

        raise gen.Return(json_encode({'message': 'Account -' + account_name +
                                      '- successfully deleted.'}))


class CharDeleteHandler(BaseHandler):
    @gen.coroutine
    def delete(self, account_name, char_name):
        """
        Inputs:
            account name and character name in URL
        Usage:
            curl -X DELETE http://127.0.0.1:5000/account/<account_name>/
                           characters/<char_name>


        Returns 200, with a body of
        {'message': 'Character -<char_name>- belonging to -<account_name>-
                     was successfully deleted.'}

        Deletes the specified character of the specified account. Note that
        deleted characters are not deleted from memory but simply deactivated.
        The accountholder can later "undelete" this character to resume play
        on that character once more.
        """
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
                        url(r"/account/(.*)/characters", CharactersHandler),
                        url(r"/account/(.*)", AccDeleteHandler),
                        url(r"/account/(.*)/characters/(.*)",
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
