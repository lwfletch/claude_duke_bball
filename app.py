#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.duke_bball_stack import DukeBballStack

app = cdk.App()
DukeBballStack(app, "DukeBballStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1",
    )
)
app.synth()
