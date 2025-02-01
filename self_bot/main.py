import json
import time
import requests
from typing import Any
from discord.ext import commands
from discord import Message

TOKEN: str = "MTE4NTQxNzkzNzU5OTg2MDc4Nw.G8uce6.4JM5T1RQAZm8WrB0anE2eRWoThLKwJBx50Wurk" # replace w your token
API_BASE_URL: str = "https://discord.com/api/v9"

headers = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}

bot = commands.Bot(command_prefix=",", self_bot=True)
# due to new poetry change, you must do `pip install poetry` to install poetry package
# start up the self-bot using `poetry run python self_bot/main.py`

def get_friends() -> list[dict[str, Any]]:
    """Fetches the list of relationships for the user account.
    
    Returns only type=1 (actual 'friend' relationships).
    """
    url = f"{API_BASE_URL}/users/@me/relationships"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        relationships = response.json()
        return [rel for rel in relationships if rel.get("type") == 1]
    else:
        print(f"Failed to fetch friends. Status code: {response.status_code}")
        return []

@bot.event
async def on_ready():
    if bot.user is not None:
        print(f"Logged in as {bot.user.name} ({bot.user.id})")
    else:
        print("Bot user is None, unable to retrieve name or ID.")

@bot.event
async def on_message(message: Message):
    await bot.process_commands(message)

@bot.command()
async def savefriends(ctx: commands.Context):
    """Fetches all friends and saves only the username to friends.json.
    
    Usage:
      ,savefriends
    """
    friends = get_friends()
    user_list = []
    for friend in friends:
        user_data = friend.get("user", {})
        user_list.append({"username": user_data.get("username")})

    filename = "friends.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(user_list, f, indent=4)
        await ctx.message.add_reaction("✅")
        print(f"Saved {len(user_list)} friend usernames to '{filename}'")
    except Exception as e:
        print(f"Error saving to file: {e}")
        await ctx.send(f"Error saving: {e}")

def add_friend_by_username(username: str) -> bool:
    """Attempts to add a friend by username using the new handle system.

    NOTE: This may fail if the account has not migrated to new handles 
    or if the user's privacy settings block it.
    """
    url = f"{API_BASE_URL}/users/@me/relationships"
    payload = {"username": username}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code in (200, 204):
        return True
    else:
        print(
            f"Failed to add friend '{username}'. "
            f"Status code: {response.status_code}, response: {response.text}"
        )
        return False

@bot.command()
async def addfriends(ctx: commands.Context):
    """Reads the 'friends.json' file and attempts to add each username as a friend.
    
    Usage:
      ,addfriends
    """
    filename = "friends.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            friends_list = json.load(f)
    except FileNotFoundError:
        await ctx.send(f"File '{filename}' not found. Please run ,savefriends first.")
        return

    success_count = 0
    failure_count = 0

    for friend_obj in friends_list:
        username = friend_obj.get("username")
        if not username:
            continue

        success = add_friend_by_username(username)
        if success:
            success_count += 1
            print(f"Sent friend request to: {username}")
        else:
            failure_count += 1
        time.sleep(1.5)

    await ctx.send(
        f"Attempted to add {success_count + failure_count} users. "
        f"Successes: {success_count}, Failures: {failure_count}"
    )

bot.run(TOKEN)
