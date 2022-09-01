from aws_cdk import (
    Duration,
    NestedStack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_lambda as _lambda,
    aws_sqs as sqs,
)
from constructs import Construct


class VrfRequestStack(NestedStack):
    def __init__(
        self, scope: Construct, construct_id: str, environment: dict, **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.eventbridge_minute_scheduled_event = events.Rule(
            self,
            "RunEveryMinute",
            event_bus=None,  # "default" bus, though eventually put in its own Eventbridge bus
            schedule=events.Schedule.rate(Duration.minutes(1)),
        )

        self.vrf_request_lambda = _lambda.Function(
            self,
            "VrfRequest",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                path="source/vrf_request_lambda",
                exclude=[".venv/*"],  # exclude virtualenv
            ),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(1),  # should be effectively instantenous
        )

        self.request_queue = sqs.Queue(
            self,
            "RequestQueue",
            removal_policy=RemovalPolicy.DESTROY,
            retention_period=Duration.days(4),
            visibility_timeout=Duration.seconds(1),  # retry failed message quickly
        )

        self.dynamodb_table = dynamodb.Table(
            self,
            "RequestAndResponseTable",
            partition_key=dynamodb.Attribute(
                name="unique_identifier", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="action", type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="expiration",  # when to automatically delete record
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # can handle burst entries
            # CDK wil not automatically deleted DynamoDB during `cdk destroy`
            # (as DynamoDB is a stateful resource) unless explicitly specified by the following line
            removal_policy=RemovalPolicy.DESTROY,
        )

        # dependencies
        self.eventbridge_minute_scheduled_event.add_target(
            target=events_targets.LambdaFunction(
                handler=self.vrf_request_lambda, retry_attempts=3
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
        self.vrf_request_lambda.add_layers(powertools_layer)
        self.vrf_request_lambda.add_environment(
            key="QUEUE_NAME", value=self.request_queue.queue_name
        )
        self.vrf_request_lambda.add_environment(
            key="AWSREGION",  # apparently "AWS_REGION" is not allowed as a Lambda env variable
            value=environment["AWS_REGION"],
        )
        self.vrf_request_lambda.add_environment(
            key="TABLE_NAME", value=self.dynamodb_table.table_name
        )
        self.request_queue.grant_send_messages(self.vrf_request_lambda)
        self.dynamodb_table.grant_write_data(self.vrf_request_lambda)
