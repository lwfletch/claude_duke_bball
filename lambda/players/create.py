"""POST /players — create a new player with stats for a season"""
import json
import os
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

REQUIRED_FIELDS = ["name", "season", "position", "jersey_number"]


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"message": "Invalid JSON body"})

    missing = [f for f in REQUIRED_FIELDS if not body.get(f)]
    if missing:
        return _response(400, {"message": f"Missing required fields: {missing}"})

    player_id = body.get("player_id") or str(uuid.uuid4())

    item = {
        "player_id": player_id,
        "season": body["season"],
        "name": body["name"],
        "position": body["position"],
        "jersey_number": str(body["jersey_number"]),
        "stats": {
            "games_played": int(body.get("games_played", 0)),
            "points_per_game": float(body.get("points_per_game", 0.0)),
            "rebounds_per_game": float(body.get("rebounds_per_game", 0.0)),
            "assists_per_game": float(body.get("assists_per_game", 0.0)),
            "steals_per_game": float(body.get("steals_per_game", 0.0)),
            "blocks_per_game": float(body.get("blocks_per_game", 0.0)),
            "field_goal_pct": float(body.get("field_goal_pct", 0.0)),
            "three_point_pct": float(body.get("three_point_pct", 0.0)),
            "free_throw_pct": float(body.get("free_throw_pct", 0.0)),
            "minutes_per_game": float(body.get("minutes_per_game", 0.0)),
        },
        "created_at": datetime.utcnow().isoformat(),
    }

    table.put_item(Item=item)
    return _response(201, item)


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }
