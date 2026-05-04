import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("duke-player-stats")

player = {
    "player_id": str(uuid.uuid4()),
    "season": "2024-25",
    "name": "Isaiah Evans",
    "position": "Guard",
    "jersey_number": "3",
    "height": "6'6\"",
    "hometown": "Fayetteville, NC",
    "image_url": "",
    "stats": {
        "games_played": 36,
        "points_per_game": "6.8",
        "rebounds_per_game": "1.1",
        "assists_per_game": "0.5",
        "steals_per_game": "0.2",
        "blocks_per_game": "0.2",
        "field_goal_pct": "0.430",
        "three_point_pct": "0.416",
        "free_throw_pct": "0.833",
        "minutes_per_game": "13.0",
    },
    "created_at": datetime.utcnow().isoformat(),
}

table.put_item(Item=player)
print(f"Added player: {player['name']} (player_id: {player['player_id']})")
