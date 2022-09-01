from aws_cdk import (
    Duration,
    NestedStack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_sqs as sqs,
)
from constructs import Construct


class VrfFulfillStack(NestedStack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: dict,
        request_queue: sqs.Queue,
        dynamodb_table: dynamodb.Table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.trigger_sfn_lambda = _lambda.Function(
            self,
            "TriggerSfnLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                path="source/trigger_sfn_lambda",
                exclude=[".venv/*"],  # exclude virtualenv
            ),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(1),  # should be effectively instantenous
        )
        self.vrf_fulfill_lambda = _lambda.Function(
            self,
            "VrfFulfill",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                path="source/vrf_fulfill_lambda",
                exclude=[".venv/*"],  # exclude virtualenv
            ),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(1),  # should be effectively instantenous
        )
        powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "aws_lambda_powertools",
            layer_version_arn=(
                f"arn:aws:lambda:{environment['AWS_REGION']}:"
                "017000801446:layer:AWSLambdaPowertoolsPython:29"  # might consider getting latest layer
            ),
        )

        # Step Function can wait up to 1 year
        # Would need some way of determining block for block number very far away
        # Could use DynamoDB for this
        sleep_until_target_block = sfn.Wait(
            self,
            "SleepUntilTargetBlock",
            time=sfn.WaitTime.timestamp_path("$.target_block_time"),
        )
        fulfill_vrf_request = sfn_tasks.LambdaInvoke(
            self,
            "FulfillVrfRequest",
            lambda_function=self.vrf_fulfill_lambda,
            payload_response_only=True,  # don't want Lambda invocation metadata
        )
        sfn_definition = sleep_until_target_block.next(fulfill_vrf_request)
        self.state_machine = sfn.StateMachine(
            self, "WaitAndFulfillVrfRequest", definition=sfn_definition
        )

        # dependencies
        self.trigger_sfn_lambda.add_layers(powertools_layer)
        self.trigger_sfn_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(request_queue, batch_size=1)
        )
        self.trigger_sfn_lambda.add_environment(
            key="AWSREGION",  # apparently "AWS_REGION" is not allowed as a Lambda env variable
            value=environment["AWS_REGION"],
        )
        self.trigger_sfn_lambda.add_environment(
            key="SFN_ARN", value=self.state_machine.state_machine_arn,
        )
        self.trigger_sfn_lambda.add_environment(
            key="TABLE_NAME", value=dynamodb_table.table_name,
        )
        self.state_machine.grant_start_execution(self.trigger_sfn_lambda)
        dynamodb_table.grant_write_data(self.trigger_sfn_lambda)

        self.vrf_fulfill_lambda.add_layers(powertools_layer)
        self.vrf_fulfill_lambda.add_environment(
            key="AWSREGION",  # apparently "AWS_REGION" is not allowed as a Lambda env variable
            value=environment["AWS_REGION"],
        )
        self.vrf_fulfill_lambda.add_environment(
            key="TABLE_NAME", value=dynamodb_table.table_name,
        )
        dynamodb_table.grant_write_data(self.vrf_fulfill_lambda)


# Lambda -> Step Function (wait -> Lambda write to DynamoDB; has to have decent failure; short runtime)
# make SQS a FIFO queue? Is double fulfillment bad?
# make DLQ?
# create 'expiration' attribute for TTL?
# figure out nested stack
