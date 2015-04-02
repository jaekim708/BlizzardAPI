import BlizzardAPI
import requests as r
import json

url = 'http://localhost:5000'
d = r.get(url + '/about')
assert(d.text == '{"source": "BlizzardAPI.py", "author": "Jae Il Kim"}')

d = r.post(url + '/account', data=json.dumps({"username" : "Jae"}))
assert(d.text == '{"account_id": 0}')

d = r.get(url + '/account')
assert(d.text == '[{"username": "Jae", '
                 '"deleted_char_ids": [], '
                 '"account_id": 0, '
                 '"faction": null, '
                 '"link": "{http://127.0.0.1:5000/account/Jae}", '
                 '"char_ids": []}]')

d = r.post(url + '/account', data=json.dumps({"username" : "Jae2"}))
assert(d.text == '{"account_id": 1}')


d = r.get(url + '/account')
assert(d.text == '[{"username": "Jae", '
                 '"deleted_char_ids": [], '
                 '"account_id": 0, '
                 '"faction": null, '
                 '"link": "{http://127.0.0.1:5000/account/Jae}", '
                 '"char_ids": []}, '
                 '{"username": "Jae2", '
                 '"deleted_char_ids": [], '
                 '"account_id": 1, '
                 '"faction": null, '
                 '"link": "{http://127.0.0.1:5000/account/Jae2}", '
                 '"char_ids": []}]')

d = r.delete(url + '/account/Jae2')
assert(d == '<Response [200]>')
assert(d.text == '{"message": "Account -Jae2- successfully deleted."}')

