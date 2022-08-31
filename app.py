#!/usr/bin/env python3
import aws_cdk as cdk

from cdk_infrastructure.vrf_request_stack import VrfRequestStack


app = cdk.App()
vr_request_stack = VrfRequestStack(
    app,
    "VrfRequestStack",
    env=cdk.Environment(region=app.node.try_get_context("environment")["AWS_REGION"]),
    environment=app.node.try_get_context("environment"),
)

app.synth()
