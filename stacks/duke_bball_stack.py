from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_s3 as s3,
    Duration,
)
from constructs import Construct


class DukeBballStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table for player stats
        table = dynamodb.Table(
            self, "DukePlayerStatsTable",
            table_name="duke-player-stats",
            partition_key=dynamodb.Attribute(
                name="player_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="season",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # S3 bucket for player images
        images_bucket = s3.Bucket(
            self, "PlayerImagesBucket",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            public_read_access=True,
            removal_policy=RemovalPolicy.RETAIN,
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET],
                allowed_origins=["*"],
                allowed_headers=["*"],
            )],
        )

        CfnOutput(self, "ImagesBucketName", value=images_bucket.bucket_name)
        CfnOutput(self, "ImagesBucketUrl", value=f"https://{images_bucket.bucket_name}.s3.amazonaws.com")

        # GSI: query by jersey number
        table.add_global_secondary_index(
            index_name="jersey-index",
            partition_key=dynamodb.Attribute(
                name="jersey_number",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="season",
                type=dynamodb.AttributeType.STRING,
            ),
        )

        # Shared Lambda environment
        lambda_env = {
            "TABLE_NAME": table.table_name,
        }

        # Lambda: list/get players
        get_players_fn = _lambda.Function(
            self, "GetPlayersFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda/players"),
            environment=lambda_env,
            timeout=Duration.seconds(10),
        )

        # Lambda: create player
        create_player_fn = _lambda.Function(
            self, "CreatePlayerFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="create.handler",
            code=_lambda.Code.from_asset("lambda/players"),
            environment=lambda_env,
            timeout=Duration.seconds(10),
        )

        # Lambda: update player stats
        update_stats_fn = _lambda.Function(
            self, "UpdateStatsFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="update_stats.handler",
            code=_lambda.Code.from_asset("lambda/players"),
            environment=lambda_env,
            timeout=Duration.seconds(10),
        )

        # Lambda: delete player
        delete_player_fn = _lambda.Function(
            self, "DeletePlayerFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="delete.handler",
            code=_lambda.Code.from_asset("lambda/players"),
            environment=lambda_env,
            timeout=Duration.seconds(10),
        )

        # Lambda: health check
        health_fn = _lambda.Function(
            self, "HealthFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="health.handler",
            code=_lambda.Code.from_asset("lambda/players"),
            timeout=Duration.seconds(5),
        )

        # Grant DynamoDB permissions
        table.grant_read_data(get_players_fn)
        table.grant_write_data(create_player_fn)
        table.grant_write_data(update_stats_fn)
        table.grant_write_data(delete_player_fn)

        # API Gateway
        api = apigw.RestApi(
            self, "DukeBballApi",
            rest_api_name="Duke Basketball Stats API",
            description="Serverless API for Duke basketball player stats",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "x-api-key"],
            ),
        )

        # API key + usage plan
        api_key = api.add_api_key("DukeBballApiKey", api_key_name="duke-bball-api-key")

        plan = api.add_usage_plan(
            "DukeBballUsagePlan",
            name="duke-bball-usage-plan",
            throttle=apigw.ThrottleSettings(rate_limit=100, burst_limit=200),
        )
        plan.add_api_key(api_key)
        plan.add_api_stage(stage=api.deployment_stage)

        # Helper to add key-required methods
        def add_method(resource, http_method, integration):
            resource.add_method(
                http_method,
                integration,
                api_key_required=True,
            )

        health = api.root.add_resource("health")
        add_method(health, "GET", apigw.LambdaIntegration(health_fn))

        players = api.root.add_resource("players")
        player = players.add_resource("{player_id}")
        stats = player.add_resource("stats")

        add_method(players, "GET", apigw.LambdaIntegration(get_players_fn))
        add_method(player, "GET", apigw.LambdaIntegration(get_players_fn))
        add_method(players, "POST", apigw.LambdaIntegration(create_player_fn))
        add_method(stats, "PUT", apigw.LambdaIntegration(update_stats_fn))
        add_method(player, "DELETE", apigw.LambdaIntegration(delete_player_fn))

        # Output the API key ID so you can retrieve the value from the console
        CfnOutput(self, "ApiKeyId", value=api_key.key_id, description="API Key ID — retrieve value from API Gateway console")
