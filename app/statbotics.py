import requests

API_URL = 'https://api.statbotics.io/v2'
COMP_ID = '2023cur'


def match_info(match_id: str):
    try:
        resp = requests.get(f"{API_URL}/match/{COMP_ID}_{match_id}")
        return resp.json()
    except:
        return None

def schedule(team: int):
    try:
        resp = requests.get(f"{API_URL}/matches/team/{team}/event/{COMP_ID}")
        return resp.json()
    except:
        return None

