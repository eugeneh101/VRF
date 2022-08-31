import typing

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_lambda as _lambda,
    aws_sqs as sqs,
)
from constructs import Construct


class VRFStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: typing.Optional[dict] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        environment = {} if environment is None else environment

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
                exclude=[
                    ".venv/*",  # exclude virtualenv
                ],
            ),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(1),  # should be effectively instantenous
        )
        self.request_queue = sqs.Queue(
            self,
            "RequestQueue",
            removal_policy=RemovalPolicy.DESTROY,
            retention_period=Duration.days(4),
            visibility_timeout=Duration.seconds(30),
        )

        # dependencies:
        self.eventbridge_minute_scheduled_event.add_target(
            target=events_targets.LambdaFunction(
                handler=self.create_vrf_request_lambda, retry_attempts=0
            )
        )
        powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "aws_lambda_powertools",
            layer_version_arn=(
                f"arn:aws:lambda:{environment['AWS_REGION']}:"
                "017000801446:layer:AWSLambdaPowertoolsPython:29"  # might consider getting latest layer
            ),
        )
        self.create_vrf_request_lambda.add_layers(powertools_layer)
        self.create_vrf_request_lambda.add_environment(
            key="QUEUE", value=self.request_queue.queue_name
        )
        self.create_vrf_request_lambda.add_environment(
            key="AWSREGION",  # apparently "AWS_REGION" is not allowed as a Lambda env variable
            value=environment["AWS_REGION"],
        )
        self.request_queue.grant_send_messages(self.create_vrf_request_lambda)
