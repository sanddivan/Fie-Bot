# File: fiecommands.py
import random
from datetime import datetime, timedelta, UTC
from fieemotes import emote
from fieconstants import CHARACTER_LEVEL_IMAGES, LEVEL_THRESHOLDS, rank_points, WHITELISTED_USERS
from pathlib import Path
from dotenv import load_dotenv

import math
import statistics
import json
import requests
import os

SCORES_FILE = Path("player_scores.json")
XP_FILE = Path("xp_data.json")
CHARACTER_PROFILES_FILE = Path("character_profiles.json")
load_dotenv()
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY')


# ********************************************************************************* #
# FIE UTILITIES FUNCTIONS:                                                          #
#                                                                                   #
# These are the helper functions for the non-game fie-commands (e.g. 'fie time').   #
# Try to name them after the commands they represent, if said commands are short    #
# enough. Like for 'fie time', the function's name would be fie_time(). Just to     #
# make it easier to navigate the code for debugging, extending, etc.                #
#                                                                                   #
# The exception to this rule is 'fie_response()', as that one handles Fie's replies #
# when someone says specific phrases in the server, rather than there being a       #
# command named 'fie response'.                                                     #
# ********************************************************************************* #

def fie_time(dest_channel_id: int) -> str:
    # This is okay for now. If we want to add more timezones in the future, then
    # there are better approaches to take. And I'm getting a very cool idea but
    # need to cook it more :)
    utc = datetime.now(UTC)
    azores = utc - timedelta(hours=1)

    if dest_channel_id == 420709830622183434 or dest_channel_id == 420706417721475082:
        costa_rica = utc - timedelta(hours=6)
        egypt = utc + timedelta(hours=3)
        kuwait = utc + timedelta(hours=3)

        return (f"Costa Rica (UTC-6): {datetime_to_casual(costa_rica)}\n"
                f"Azores (UTC-1): {datetime_to_casual(azores)}\n"
                f"Egypt (UTC+3): {datetime_to_casual(egypt)}\n"
                f"Kuwait (UTC+3): {datetime_to_casual(kuwait)}")

    elif dest_channel_id == 455812354790260747 or dest_channel_id == 451108529617764362:
        portugal = utc + timedelta(hours=0)
        norway = utc + timedelta(hours=1)
        japan = utc + timedelta(hours=9)

        return (f"Azores: {datetime_to_casual(azores)}\n"
                f"Portugal: {datetime_to_casual(portugal)}\n"
                f"Norway: {datetime_to_casual(norway)}\n"
                f"Japan: {datetime_to_casual(japan)}\n")

    us_west = utc - timedelta(hours=7)
    us_east = utc - timedelta(hours=4)
    aus_west = utc + timedelta(hours=8)
    uk = utc + timedelta(hours=0)
    return (f"US West Coast (UTC-7): {datetime_to_casual(us_west)}\n"
            f"US East Coast (UTC-4): {datetime_to_casual(us_east)}\n"
            f"Azores (UTC): {datetime_to_casual(azores)}\n"
            f"UK (UTC+1): {datetime_to_casual(uk)}\n"
            f"Western Australia (UTC+8): {datetime_to_casual(aus_west)}")


def fie_solve(operation: str) -> str:
    # TODO: Handle incorrect data types. Right now, this function is unprotected
    #       against cases like 'fie solve 5 * lol'. So, we need to make sure all
    #       input operands are valid numbers.

    result = None
    tokens = operation.split()[2:]
    print(tokens)

    # If we have less than two tokens then we're either missing an operator or
    # the operands.
    if len(tokens) < 2:
        return f"Hey dummy, your operation '{" ".join(tokens)}' is malformed."

    # Cases starting with the operator or math function name.
    match tokens[0]:
        case "sqrt": result = math.sqrt(int(tokens[1]))
        case "mean" | "average": result = statistics.fmean(list(map(float, tokens[1:])))
        case _ if tokens[1] == "!": result = math.factorial(int(tokens[0]))

    # At this point, if we didn't match any of the above cases, then we only have
    # bi-operand operations left available. So, if we have less than 3 operands,
    # then the operation is incomplete, and if we have more than 3 operands, then
    # Fie won't like it :)

    if result is None:
        if len(tokens) < 3:
            return f"Hey dummy, your operation '{" ".join(tokens)}' is malformed."

        if len(tokens) > 3:
            return f"Hey, my brain can only do so much at once! Give me a break {emote("FROWN")}"

        # Cases starting with an operand.
        match tokens[1]:
            case "+": result = float(tokens[0]) + float(tokens[2])
            case "-": result = float(tokens[0]) - float(tokens[2])
            case "*": result = float(tokens[0]) * float(tokens[2])
            case "/": result = float(tokens[0]) / float(tokens[2])
            case "^": result = float(tokens[0]) ** float(tokens[2])
            case _: return f"Hey dummy, what is that '{tokens[1]}' operator?"

    return f"The result is {result}!"


def fie_days_until(target_day_msg: str) -> str:
    today = datetime.now()
    tokens = target_day_msg.split()[5:]
    days_until_msg = ""

    # A specific date was given, so calculate how long until or how long has passed
    # since said date.
    if len(tokens) > 0:
        target = datetime.strptime(tokens[0], "%d-%m-%Y")
        delta = target - today

        days_until_msg = \
            ({True: f"There are {delta.days + 1} days until {target}",
              False: f"{delta.days * (-1) + 1} days have passed since {target}"}) \
              [delta.days >= 0]

    # No specific date given, so Fie will show the days until or after some
    # important dates.
    else:
        christmas = datetime(today.year, 12, 25)
        christmas_msg = "Days until Christmas"

        # If Christmas has already passed this year, then Fie will tell how many
        # days left until next year's Christmas.
        until_christmas = \
            ({True: (christmas - today).days,
              False: (datetime(today.year + 1, 12, 25) - today).days}) \
              [christmas > today]

        sky_first = datetime(2025, 9, 19)
        until_sky_first = (sky_first - today).days

        kai = datetime(2026, 1, 15)
        until_kai = (kai - today).days

        sky_1st = ({True: "Days until Sky the 1st Remake",
                          False: "Days since Sky the 1st Remake"}) \
                          [sky_first > today]

        kai_msg = ({True: "Days until Beyond the Horizon",
                          False: "Days since Sky the 1st Remake "}) \
            [kai > today]

        easter = datetime(today.year, 4, 20)
        easter_msg = "Days until Easter"

        # If Easter has already passed this year, then Fie will tell how many
        # days left until next year's Easter.
        until_easter = \
            ({True: (easter - today).days,
              False: (datetime(today.year + 1, 4, 20) - today).days}) \
                [easter > today]

        days_until_msg = (f"{christmas_msg}: {until_christmas + 1}\n"
                          #f"{easter_msg}: {until_easter + 1}\n"
                          #f"{sky_1st}: {until_sky_first + 1}\n"
                          f"{kai_msg}: {until_kai + 1}\n"
                          f"Days until Rean stops being dense: ∞")
    return days_until_msg


def fie_what_is(question_msg: str) -> str:
    tokens = question_msg.split()[2:]
    fun_fact = ""

    if len(tokens) == 0:
        return "What's what?"

    match tokens[0]:
        case "zemuria":
            fun_fact = ("Zemuria is the continent made up of 37 regions on which the"
                        " series takes place. It's the only known continent so far.")

        case "zemurian" if (len(tokens) > 1 and tokens[1] == "ore"):
            fun_fact = ("Zemurian Ore is an extremely rare material found in Zemuria."
                        " It's usually used in the series to craft very strong weapons!")

        case "zemurian":
            fun_fact = ("Zemurian is how the inhabitants and otherwise belonging beings"
                        " to the continent of Zemuria are known as.")

        case _:
            fun_fact = "Mmm... I will have to research that and get back to you later."

    return fun_fact


def fie_leaderboard() -> str:
    leaderboard = {}

    for player, maps in player_scores.items():
        total = sum(rank_points[rank] for rank in maps.values())
        leaderboard[player] = total

    sorted_board = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    if not sorted_board:
        return "No scores yet! Go play something!!"

    output = "**Leaderboard:**\n"
    for i, (player, score) in enumerate(sorted_board, start=1):
        output += f"{i}. {player} - {score} points\n"

    return output

def get_character_for_user(user_id: str) -> str:
    return character_profiles.get(user_id, character_profiles.get("default", "fie"))

def add_xp(user_id: str, amount: int) -> tuple[str, str] | str | None:
    if user_id not in WHITELISTED_USERS:
        return None  # Skip XP processing entirely

    char_name = get_character_for_user(user_id)
    level_images = CHARACTER_LEVEL_IMAGES.get(char_name)

    if not level_images:
        return f"{char_name} doesn't have any level images configured."

    max_level = len(level_images)

    user = xp_data.get(user_id, {
        "characters": {},
        "maxed_characters": [],
        "current_character": char_name
    })

    characters = user.get("characters", {})
    char_data = characters.get(char_name, {
        "xp": 0,
        "level": 1,
        "image": level_images[1]
    })

    # Add XP
    char_data["xp"] += amount

    # Determine new level
    new_level = char_data["level"]
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if char_data["xp"] >= threshold:
            new_level = i + 1
    new_level = min(new_level, max_level)

    level_up = new_level > char_data["level"]
    char_data["level"] = new_level
    char_data["image"] = level_images.get(new_level, char_data["image"])
    characters[char_name] = char_data

    # Update maxed character list if needed
    if new_level == max_level and char_name not in user.get("maxed_characters", []):
        user.setdefault("maxed_characters", []).append(char_name)

    user.pop("xp", None)
    user.pop("level", None)
    user.pop("image", None)

    # Save updates
    user["characters"] = characters
    user["current_character"] = char_name
    xp_data[user_id] = user
    save_xp_data(xp_data)

    if level_up:
        return f"<@{user_id}> leveled up {char_name.capitalize()} to level {new_level}! ", char_data["image"]
    else:
        return f"<@{user_id}> gained {amount} XP for {char_name.capitalize()}. Now at {char_data['xp']} XP, Level {char_data['level']}"


def fie_level(user_id: str, user_name: str) -> tuple[str, str] | str:
    user = xp_data.get(user_id)

    if not user or "current_character" not in user:
        return f"{user_name} hasn't selected a character yet."

    char_name = user["current_character"]
    char_data = user.get("characters", {}).get(char_name)

    if not char_data:
        return f"{user_name} hasn't gained any XP for {char_name.capitalize()} yet."

    level_text = f"{user_name} is Level {char_data['level']} having {char_data['xp']} XP with {char_name.capitalize()}!"

    if user.get("maxed_characters"):
        maxed = ", ".join(name.capitalize() for name in user["maxed_characters"])
        level_text += f"\n**Maxed characters:** {maxed}"

    return (level_text, char_data["image"])

def fie_switch_character(user_id: str, new_character: str) -> str:
    new_character = new_character.lower()
    if new_character not in CHARACTER_LEVEL_IMAGES:
        return f"I don't know who '{new_character}' is..."

    character_profiles[user_id] = new_character
    with open(CHARACTER_PROFILES_FILE, "w") as f:
        json.dump(character_profiles, f, indent=2)

    return f"Switched active character to {new_character.capitalize()}!"

def fie_characters(user_id: str, user_name: str) -> str:
    user = xp_data.get(user_id)
    if not user or not user.get("characters"):
        return f"{user_name} hasn’t leveled any characters yet."

    output = f"**{user_name}'s characters:**\n"
    for char, data in user["characters"].items():
        output += f"- {char.capitalize()}: Level {data['level']} ({data['xp']} XP)\n"

    if user.get("maxed_characters"):
        maxed = ", ".join(c.capitalize() for c in user["maxed_characters"])
        output += f"\n**Maxed:** {maxed}"

    return output


def get_team_id(team_name: str, competition: str) -> int | None:
    """Fetch team ID from competition and name."""
    url = f"https://api.football-data.org/v4/competitions/{competition}/teams"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    response = requests.get(url, headers=headers)
    data = response.json()

    for team in data.get("teams", []):
        if team_name.lower() in team["name"].lower():
            print(f"Found team: {team['name']} (ID: {team['id']})")
            return team["id"]

    print("Team not found in this competition.")
    return None

def fie_football(team_name: str, count: int = 5) -> str:

    if team_name.lower() == "manchester united":
        team_id = 66
    elif team_name.lower() == "benfica":
        team_id = 1903
    elif team_name.lower() == "arsenal":
        team_id = 57
    elif team_name.lower() == "bayern":
        team_id = 5
    elif team_name.lower() == "vasco":
        team_id = 1780


    else:
        return "Please enter a **relevant** team name."

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    response = requests.get(url, headers=headers)
    data = response.json()

    print(response.status_code)
    print(response.url)
    print(response.json())

    matches = data.get("matches", [])
    if not matches:
        return "No upcoming fixtures found."

    lines = ["Upcoming Fixtures:"]
    for match in matches[:count]:
        date = match["utcDate"][:10]
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        lines.append(f"{date}: {home} vs {away}")
    return "\n".join(lines)

# **************************************************** #
# OTHER COMMAND UTILITIES:                             #
# Any other helper functions for the commands go here! #
# **************************************************** #

def datetime_to_casual(input_dt: datetime) -> str:
    return input_dt.strftime("%H:%M:%S")

def load_scores():
    if SCORES_FILE.exists():
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_xp_data():
    if XP_FILE.exists():
        with open(XP_FILE, "r") as f:
            return json.load(f)
    return {}

def save_xp_data(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_character_profiles():
    if CHARACTER_PROFILES_FILE.exists():
        with open(CHARACTER_PROFILES_FILE, "r") as f:
            return json.load(f)
    return {}

player_scores = load_scores()
xp_data = load_xp_data()
character_profiles = load_character_profiles()

