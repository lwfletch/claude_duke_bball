"""DELETE /players/{player_id} — delete all records for a player"""
import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    player_id = (event.get("pathParameters") or {}).get("player_id")
    if not player_id:
        return _response(400, {"message": "Missing player_id"})

    # Query all seasons for the player then batch delete
    resp = table.query(
        KeyConditionExpression=Key("player_id").eq(player_id),
        ProjectionExpression="player_id, season",
    )
    items = resp.get("Items", [])

    if not items:
        return _response(404, {"message": f"Player {player_id} not found"})

    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"player_id": item["player_id"], "season": item["season"]})

    return _response(200, {"message": f"Deleted player {player_id} ({len(items)} season record(s))"})


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }
