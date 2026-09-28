import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

# The channel /checkact reads activity-check messages from.
ACTIVITY_CHANNEL_ID = int(os.getenv("ACTIVITY_CHANNEL_ID", "0"))

# One or more staff role IDs, separated by commas in .env
# e.g. STAFF_ROLE_IDS=1513641158855626842,1520000000000000000
STAFF_ROLE_IDS = [
    int(role_id.strip())
    for role_id in os.getenv("STAFF_ROLE_IDS", "0").split(",")
    if role_id.strip()
]

# Default number of past checks /checkact looks at if no number is given
DEFAULT_CHECK_COUNT = 1

# Minimum fraction of checks a member must have reacted to, to get a ✅
# 0.5 = 50%. Change this number any time, no code needed elsewhere.
PASS_THRESHOLD = 1.0
