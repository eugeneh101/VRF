#!/usr/bin/env python3
import aws_cdk as cdk

from cdk_infrastructure.vrf_fulfill_stack import VrfFulfillStack
from cdk_infrastructure.vrf_request_stack import VrfRequestStack

app = cdk.App()
environment = app.node.try_get_context("environment")
env = cdk.Environment(region=environment["AWS_REGION"])
vrf_request_stack = VrfRequestStack(
    app, "VrfRequestStack", environment=environment, env=env,
)
vrf_fulfill_stack = VrfFulfillStack(
    app,
    "VrfFulfillStack",
    environment=environment,
    env=env,
    request_queue=vrf_request_stack.request_queue,
    dynamodb_table=vrf_request_stack.dynamodb_table,
)

app.synth()
