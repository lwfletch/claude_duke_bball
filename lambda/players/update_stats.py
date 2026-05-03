"""PUT /players/{player_id}/stats — update stats for a player/season"""
import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

STAT_FIELDS = [
    "games_played", "points_per_game", "rebounds_per_game",
    "assists_per_game", "steals_per_game", "blocks_per_game",
    "field_goal_pct", "three_point_pct", "free_throw_pct", "minutes_per_game",
]


def handler(event, context):
    player_id = (event.get("pathParameters") or {}).get("player_id")
    if not player_id:
        return _response(400, {"message": "Missing player_id"})

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"message": "Invalid JSON body"})

    season = body.get("season")
    if not season:
        return _response(400, {"message": "Missing required field: season"})

    # Build update expression for only the provided stat fields
    updates = {k: body[k] for k in STAT_FIELDS if k in body}
    if not updates:
        return _response(400, {"message": "No valid stat fields provided"})

    set_expr = ", ".join(f"stats.{k} = :v_{k}" for k in updates)
    expr_values = {f":v_{k}": v for k, v in updates.items()}
    expr_values[":updated_at"] = datetime.utcnow().isoformat()

    try:
        resp = table.update_item(
            Key={"player_id": player_id, "season": season},
            UpdateExpression=f"SET {set_expr}, updated_at = :updated_at",
            ExpressionAttributeValues=expr_values,
            ConditionExpression="attribute_exists(player_id)",
            ReturnValues="ALL_NEW",
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return _response(404, {"message": f"Player {player_id} / season {season} not found"})

    return _response(200, resp["Attributes"])


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }
