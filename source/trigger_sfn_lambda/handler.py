import json
import os
import sys
from datetime import datetime
from typing import Any, Union

sys.path.insert(
    0, "./__lambda_dependencies__"
)  # folder created by Makefile during `cdk deploy`

import boto3
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from beartype import beartype
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()
logger = Logger(level="INFO")
config = Config(region_name=os.environ["AWSREGION"])
dynamodb_resource = boto3.resource("dynamodb", config=config)
dynamodb_table = dynamodb_resource.Table(name=os.environ["TABLE_NAME"])
sfn_client = boto3.client("stepfunctions", config=config)


@logger.inject_lambda_context(log_event=True)
@beartype
def lambda_handler(
    event: dict,
    context: Union[
        Any,
        LambdaContext,  # AWS's `context` isn't precisely a `LambdaContext` instance
        tuple,  # namedtuple is used in `scratch.py`
    ],
) -> None:
    records = event["Records"]
    assert (
        len(records) == 1
    ), f"Expected a batch size of exactly 1 but got {len(records)}"
    parsed_event = json.loads(records[0]["body"])
    dynamodb_table.put_item(
        Item={
            "unique_identifier": parsed_event["unique_identifier"],
            "action": "fulfill",
            "received_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S%z"),
            "failed_fulfill_attempts": 0,
        }
    )
    payload = {
        "wait_time": parsed_event["target_block_in_the_future"],
        "unique_identifier": parsed_event["unique_identifier"],
        "min_random_value": parsed_event["min_random_value"],
        "max_random_value": parsed_event["max_random_value"],
    }
    sfn_client.start_execution(
        stateMachineArn=os.environ["SFN_ARN"], input=json.dumps(payload)
    )
    return
