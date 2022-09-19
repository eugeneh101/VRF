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
            "TriggerStepFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                path="source/trigger_sfn_lambda",
                exclude=[".venv/*"],  # exclude virtualenv
            ),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(1),  # should be effectively instantaneous
        )
        self.decrement_wait_time_lambda = _lambda.Function(
            self,
            "DecrementWaitTime",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(
                path="source/decrement_wait_time_lambda",
                exclude=[".venv/*"],  # exclude virtualenv
            ),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(1),  # should be effectively instantaneous
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
            timeout=Duration.seconds(1),  # should be effectively instantaneous
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
        decrement_wait_time = sfn_tasks.LambdaInvoke(
            self,
            "DecrementWaitTimeLambda",
            lambda_function=self.decrement_wait_time_lambda,
            payload_response_only=True,  # don't want Lambda invocation metadata
            retry_on_service_exceptions=False,  # don't want the weird default retries
        ).add_retry(max_attempts=3)
        assert isinstance(
            environment["WAIT_TIME_IN_SECONDS"], (int, float)
        ), f'"WAIT_TIME_IN_SECONDS" should be a number. It is {environment["WAIT_TIME_IN_SECONDS"]}'
        sleep_for_X_seconds = sfn.Wait(
            self,
            "SleepForXSeconds",
            time=sfn.WaitTime.duration(
                Duration.seconds(environment["WAIT_TIME_IN_SECONDS"])
            ),
        )
        fulfill_vrf_request = sfn_tasks.LambdaInvoke(
            self,
            "FulfillVrfRequestLambda",
            lambda_function=self.vrf_fulfill_lambda,
            payload_response_only=True,  # don't want Lambda invocation metadata
            retry_on_service_exceptions=False,  # don't want the weird default retries
        ).add_retry(max_attempts=3)
        is_wait_time_still_positive = sfn.Choice(self, "IsWaitTimeStillPositive")
        sleep_loop = is_wait_time_still_positive.when(
            sfn.Condition.number_greater_than_equals("$.wait_time", 0),
            sleep_for_X_seconds.next(decrement_wait_time).next(
                is_wait_time_still_positive
            ),
        )
        sfn_definition = sleep_loop.otherwise(fulfill_vrf_request)
        self.state_machine = sfn.StateMachine(
            self, "WaitAndFulfillVrfRequestLambda", definition=sfn_definition
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

        self.decrement_wait_time_lambda.add_layers(powertools_layer)
        self.decrement_wait_time_lambda.add_environment(
            key="WAIT_TIME_IN_SECONDS", value=str(environment["WAIT_TIME_IN_SECONDS"])
        )

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
