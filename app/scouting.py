import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import io

# Use a service account.
cred = credentials.Certificate(
    'creds/mvrt115-scout-firebase-adminsdk-41jrn-0defa32dac.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

teams_ref = db.collection(u'years/2023/regionals/cur/teams')


def get_pit_info(team_num) -> Optional[Dict[str, Any]]:
    team_doc = teams_ref.document(f'{team_num}')
    pit_doc = team_doc.collection('pitScoutData').document('pitScoutAnswers')
    snapshot = pit_doc.get()
    if snapshot.exists:
        return snapshot.to_dict()
    return None


def get_team_stats(team_num) -> Optional[Dict[str, Any]]:
    team_doc = teams_ref.document(f'{team_num}')
    snapshot = team_doc.get()
    if snapshot.exists:
        return snapshot.to_dict()
    return None


def make_plot(team_num, fields) -> io.BytesIO:
    # fields = ['Total Cycles', 'Teleop Cubes']
    field_query = [f'`{f}`' for f in fields]
    print(field_query)
    q = teams_ref.document(f'{team_num}').collection(
        'matches').select(field_query)
    all_data = []

    for s in q.get():
        match_num = int(s.id)
        data = s.to_dict()
        data['match'] = match_num
        all_data.append(data)

    all_data.sort(key=lambda d: d['match'])
    df = pd.DataFrame(all_data)

    plt.figure()
    plt.title(f"Team {team_num}")
    for field in fields:
        plt.scatter(df['match'], df[field], label=field)
    plt.xlabel("Match")
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf


def team_scout_comments(team_num) -> List[Tuple[int, str]]:
    q = teams_ref.document(f'{team_num}').collection(
        'matches').select(['Comments'])
    all_data = []

    for s in q.get():
        match_num = int(s.id)
        comment = s.to_dict()['Comments'].strip()
        if comment:
            all_data.append((match_num, comment))

    all_data.sort()
    return all_data


def add_team_comment(team_num, comment, match: Optional[str] = None, author: Optional[str] = None):
    ref = teams_ref.document(f'{team_num}').collection('comments')

    new_dict = {
        'comment': comment,
        'added': firestore.SERVER_TIMESTAMP
    }
    if author:
        new_dict['author'] = author
    try:
        if match:
            new_dict['match'] = match
    except:
        pass

    ref.add(new_dict)


def team_comments(team_num) -> List[str]:
    q = teams_ref.document(f'{team_num}').collection(
        'comments').order_by("added")
    all_data = []

    for s in q.get():
        data = s.to_dict()

        data_str = ''
        if 'match' in data:
            m = data.get('match')
            data_str += f"[match {m}] "

        data_str += data.get('comment')

        if 'author' in data:
            a = data.get('author')
            data_str += f" - {a}"

        all_data.append(data_str)

    return all_data
