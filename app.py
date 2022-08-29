#!/usr/bin/env python3
import aws_cdk as cdk

from cdk_infrastructure.vrf_stack import VRFStack


app = cdk.App()
VRFStack(
    app,
    "VRFStack",
    env=cdk.Environment(region=app.node.try_get_context("environment")["REGION"]),
)

app.synth()
