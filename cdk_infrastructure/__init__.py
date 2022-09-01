import aws_cdk as cdk
from constructs import Construct

from .vrf_fulfill_stack import VrfFulfillStack
from .vrf_request_stack import VrfRequestStack


class VrfRequestAndFulfillStack(cdk.Stack):
    def __init__(
        self, scope: Construct, construct_id: str, environment: dict, **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)
        kwargs.pop("env")  # NestedStack does not have `env` argument
        self.vrf_request_stack = VrfRequestStack(
            self, "VrfRequestStack", environment=environment, **kwargs
        )
        self.vrf_fulfill_stack = VrfFulfillStack(
            self,
            "VrfFulfillStack",
            environment=environment,
            request_queue=self.vrf_request_stack.request_queue,
            dynamodb_table=self.vrf_request_stack.dynamodb_table,
            **kwargs
        )

