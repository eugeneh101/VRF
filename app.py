import aws_cdk as cdk

from cdk_infrastructure import VrfRequestAndFulfillStack

app = cdk.App()
environment = app.node.try_get_context("environment")
env = cdk.Environment(region=environment["AWS_REGION"])
VrfRequestAndFulfillStack(
    app,
    "VRAFS",
    environment=environment,
    env=env,
    description="VrfRequestAndFulfillStack",
)
app.synth()
