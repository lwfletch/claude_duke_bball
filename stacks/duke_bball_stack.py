from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
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
            ),
        )

        players = api.root.add_resource("players")
        player = players.add_resource("{player_id}")
        stats = player.add_resource("stats")

        # GET /players, GET /players/{player_id}
        players.add_method("GET", apigw.LambdaIntegration(get_players_fn))
        player.add_method("GET", apigw.LambdaIntegration(get_players_fn))

        # POST /players
        players.add_method("POST", apigw.LambdaIntegration(create_player_fn))

        # PUT /players/{player_id}/stats
        stats.add_method("PUT", apigw.LambdaIntegration(update_stats_fn))

        # DELETE /players/{player_id}
        player.add_method("DELETE", apigw.LambdaIntegration(delete_player_fn))
