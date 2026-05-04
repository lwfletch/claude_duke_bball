"""Set image_url for all players to their S3 location."""
import boto3

BUCKET_URL = "https://dukebballstack-playerimagesbucket3cae4322-isr89xndwzey.s3.amazonaws.com"

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("duke-player-stats")

resp = table.scan(ProjectionExpression="player_id, #n, season",
                  ExpressionAttributeNames={"#n": "name"})

for item in resp.get("Items", []):
    slug = item["name"].lower().replace(" ", "-")
    image_url = f"{BUCKET_URL}/players/{slug}.jpg"

    table.update_item(
        Key={"player_id": item["player_id"], "season": item["season"]},
        UpdateExpression="SET image_url = :url",
        ExpressionAttributeValues={":url": image_url},
    )
    print(f"Updated {item['name']} -> {image_url}")

print("Done.")
