"""Patch existing players with height, hometown, and image_url fields."""
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("duke-player-stats")

UPDATES = {
    "Cooper Flagg": {
        "height": "6'9\"",
        "hometown": "Newport, ME",
        "image_url": "",  # add a real URL here if you have one
    },
    "Kon Knueppel": {
        "height": "6'6\"",
        "hometown": "Milwaukee, WI",
        "image_url": "",  # add a real URL here if you have one
    },
}

# Scan to find players by name
resp = table.scan(FilterExpression=Attr("name").is_in(list(UPDATES.keys())))

for item in resp.get("Items", []):
    data = UPDATES[item["name"]]
    update_kwargs = dict(
        Key={"player_id": item["player_id"], "season": item["season"]},
        UpdateExpression="SET #h = :h, hometown = :ht, image_url = :img",
        ExpressionAttributeNames={"#h": "height"},  # height is a reserved word
        ExpressionAttributeValues={
            ":h": data["height"],
            ":ht": data["hometown"],
            ":img": data["image_url"],
        },
    )
    table.update_item(**update_kwargs)
    print(f"Updated {item['name']} ({item['season']})")

print("Done.")
