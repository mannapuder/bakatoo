import requests
from pprint import pp

resp = requests.post(
        'https://api.audd.io',
        data={
            'api_token': 'd10b34bdde19579f58c0903de2e40c3a',  # don't make me poor
            'return': 'apple_music,spotify'
        },
        files={
            'file': open(r'A:\Projects\PycharmProjects\ANNA_BAKATÖÖ\uploads\3766d878-ab7f-47fd-9f18-2b3132703175main_theme.wav', 'rb')
        }
    )

pp(resp.json())