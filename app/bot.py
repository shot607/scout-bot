import discord
from typing import List, Callable, Optional, Dict, Any

import scouting
import statbotics

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


async def on_team_generic_request(request: List[str],
                                  message: discord.Message,
                                  team_number_pos: int,
                                  handler: Callable[[int], Optional[Dict[str, Any]]]):

    if len(request) < team_number_pos:
        await message.add_reaction('❓')
        return

    try:
        team = int(request[team_number_pos])
    except:
        await message.add_reaction('❓')
        return

    data = handler(team)
    print(data)

    if data is None:
        await message.channel.send(f"Can't find the relevant data for team {team}")

    msg = f"Team {team}\n"
    for key, val in data.items():
        msg += f"{key}: {val}\n"

    await message.channel.send(msg)


async def on_plot_request(request: List[str], message: discord.Message):
    if len(request) < 3:
        await message.add_reaction('❓')
        return

    try:
        team_num = int(request[2])
    except:
        await message.add_reaction('❓')
        return

    plot_fields = ' '.join(request[3:]).split("'")
    fields = plot_fields[1::2]
    print(fields)

    try:
        f = scouting.make_plot(team_num, fields)
        await message.channel.send(None, file=discord.File(f, 'plot.png'))
        f.close()
    except Exception as e:
        await message.reply(f"Unable to handle request ({e})")


async def on_comments_request(request: List[str], message: discord.Message):
    if len(request) < 3:
        await message.add_reaction('❓')
        return

    try:
        team_num = int(request[2])
    except:
        await message.add_reaction('❓')
        return

    scout_comments = scouting.team_scout_comments(team_num)
    gen_comments = scouting.team_comments(team_num)

    msg = f"__Team {team_num}__\n"
    msg += f"  **Scout Comments:**\n"
    for match, cmt in scout_comments:
        msg += f"   _[match {match}] {cmt}_\n"

    msg += f"  **General Comments:**\n"
    for cmt in gen_comments:
        msg += f"  _{cmt}_\n"

    await message.channel.send(msg)

async def on_schedule_request(words_clean: List[str], message: discord.Message):
    try:
        team_num = int(words_clean[2])
    except:
        await message.add_reaction('❓')
        return
    
    schedule = statbotics.schedule(team_num)
    msg = f"**Team {team_num}**\n"

    schedule.sort(key = lambda x: x['time'])

    for match in schedule:
        msg += f"  Match {match['comp_level']}{match['match_number']}\n"

        r1 = match['red_1']
        r1 = f"__{r1}__" if r1 == team_num else f"{r1}"
        r2 = match['red_2']
        r2 = f"__{r2}__" if r2 == team_num else f"{r2}"
        r3 = match['red_3']
        r3 = f"__{r3}__" if r3 == team_num else f"{r3}"
        b1 = match['blue_1']
        b1 = f"__{b1}__" if b1 == team_num else f"{b1}"
        b2 = match['blue_2']
        b2 = f"__{b2}__" if b2 == team_num else f"{b2}"
        b3 = match['blue_3']
        b3 = f"__{b3}__" if b3 == team_num else f"{b3}"

        r_score = match['red_score']
        b_score = match['blue_score']
        r_epa = match['red_epa_sum']
        b_epa = match['blue_epa_sum']
        r_score_s = f" **(Score {r_score})**" if r_score >= b_score else f" (Score {r_score})"
        b_score_s = f" **(Score {b_score})**" if b_score >= r_score else f" (Score {b_score})"
        r_epa_s = f" **(EPA {r_epa})**" if r_epa >= b_epa else f" (EPA {r_epa})"
        b_epa_s = f" **(EPA {b_epa})**" if b_epa >= r_epa else f" (EPA {b_epa})"

        msg += f"  Red {r1} {r2} {r3} "
        if match['status'] == 'Completed':
            msg += r_score_s
        else:
            msg += r_epa_s

        msg += f"  Blue {b1} {b2} {b3} "
        if match['status'] == 'Completed':
            msg += b_score_s
        else:
            msg += b_epa_s
        msg += "\n"

    await message.channel.send(msg)


async def on_add_comment(words_clean: List[str], message: discord.Message):
    team_match = words_clean[1]
    try:
        if ',' in team_match:
            team, match = team_match.split(',')
            team = int(team)
        else:
            team = int(team_match)
            match = None
    except:
        await message.add_reaction('❓')
        return

    comment = ' '.join(words_clean[2:])
    author = message.author.display_name
    scouting.add_team_comment(team, comment, match, author)
    await message.add_reaction('✅')

async def on_match_preview_request(words_clean: List[str], message: discord.Message):
    match_id = words_clean[2]
    try:
        match = statbotics.match_info(match_id)
        match_preview =  f"Match {match_id}\n"
        match_preview += f"  **Red:** {match['red_1']} {match['red_2']} {match['red_3']} (EPA: {match['red_epa_sum']})\n"
        match_preview += f"  **Blue:** {match['blue_1']} {match['blue_2']} {match['blue_3']} (EPA: {match['blue_epa_sum']}\n"
        match_preview += f"  _Predicted Winner:_ {match['epa_winner']} (probability {match['epa_win_prob']:.02f})\n"
        await message.channel.send(match_preview)
    except Exception as e:
        msg = str(e)
        await message.reply(f"Error: {msg}")

async def on_match_results_request(words_clean: List[str], message: discord.Message):
    match_id = words_clean[2]
    try:
        match = statbotics.match_info(match_id)
        match_results =  f"Match {match_id}\n"
        match_results += f"  **Red:** {match['red_1']} {match['red_2']} {match['red_3']} "
        match_results += f"(EPA: {match['red_epa_sum']}) (Score: {match['red_score']})\n"
        match_results += f"  **Blue:** {match['blue_1']} {match['blue_2']} {match['blue_3']} "
        match_results += f"(EPA: {match['blue_epa_sum']} (Score: {match['blue_score']})\n"
        match_results += f"  _Predicted Winner:_ {match['epa_winner']} (probability {match['epa_win_prob']:.02f})\n"
        match_results += f"  _Actual Winner:_ {match['winner']}\n"
        await message.channel.send(match_results)
    except Exception as e:
        msg = str(e)
        await message.reply(f"Error: {msg}")

async def send_help_message(message: discord.Message):
    help = f"""Bot Usage

    `@mvrt-scout pit data <team #>`
    `@mvrt-scout team stats <team #>`
    `@mvrt-scout team plot <team #> '<field name>' '<field name>' ...`
    `@mvrt-scout team comments <team #>`

    `@mvrt-scout match preview <match ID>`
    `@mvrt-scout match results <match ID>`

    `@mvrt-scout comment <team #> <your comment>`
    `@mvrt-scout comment <team #>,<match #> <your comment>`
    """

    await message.channel.send(help)


def is_mention_word(word: str) -> bool:
    return word.startswith('<@') and word.endswith('>')


@client.event
async def on_message(message: discord.Message):

    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        words = message.content.split(' ')
        words_clean = [w for w in words if w and not is_mention_word(w)]
        print(words_clean)

        if words_clean[0:2] == ['pit', 'data']:
            await on_team_generic_request(words_clean, message, 2, scouting.get_pit_info)

        elif words_clean[0:2] == ['team', 'stats']:
            await on_team_generic_request(words_clean, message, 2, scouting.get_team_stats)

        elif words_clean[0:2] == ['team', 'plot']:
            await on_plot_request(words_clean, message)

        elif words_clean[0:2] == ['team', 'comments']:
            await on_comments_request(words_clean, message)

        elif words_clean[0:2] == ['team', 'schedule']:
            await on_schedule_request(words_clean, message)

        elif words_clean[0:2] == ['match', 'preview']:
            await on_match_preview_request(words_clean, message)

        elif words_clean[0:2] == ['match', 'results']:
            await on_match_results_request(words_clean, message)

        elif words_clean[0:1] == ['comment']:
            await on_add_comment(words_clean, message)

        elif words_clean[0:1] == ['help']:
            await send_help_message(message)

        else:
            await message.add_reaction('❓')

with open('creds/discord.txt') as f:
    client.run(f.read())
