from aws_cdk import (
    Duration,
    Stack,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_lambda as _lambda,
    # aws_sqs as sqs,
)
from constructs import Construct


class VRFStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.eventbridge_minute_scheduled_event = events.Rule(
            self,
            "RunEveryMinute",
            event_bus=None,  # "default" bus
            schedule=events.Schedule.rate(Duration.minutes(1)),
        )

        self.create_vrf_request_lambda = _lambda.Function(
            self,
            "CreateVrfRequestLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                path="source/create_vrf_request_lambda",
                exclude=[".venv/*"],  # exclude virtualenv
            ),
            handler="handler.lambda_handler",
        )
        # dependencies:
        self.eventbridge_minute_scheduled_event.add_target(
            target=events_targets.LambdaFunction(
                handler=self.create_vrf_request_lambda, retry_attempts=0
            )
        )
