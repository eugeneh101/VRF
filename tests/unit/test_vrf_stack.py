import aws_cdk as core
import aws_cdk.assertions as assertions

from vrf.vrf_stack import VrfStack

# example tests. To run these tests, uncomment this file along with the example
# resource in vrf/vrf_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = VrfStack(app, "vrf")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
