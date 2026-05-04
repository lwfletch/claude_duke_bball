"""GET /players and GET /players/{player_id}"""
import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    player_id = (event.get("pathParameters") or {}).get("player_id")

    if player_id:
        # Get all seasons for a specific player
        resp = table.query(
            KeyConditionExpression=Key("player_id").eq(player_id)
        )
        items = resp.get("Items", [])
        if not items:
            return _response(404, {"message": f"Player {player_id} not found"})
        return _response(200, items)
    else:
        # List all players (scan — acceptable for small roster)
        resp = table.scan()
        return _response(200, resp.get("Items", []))


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }
