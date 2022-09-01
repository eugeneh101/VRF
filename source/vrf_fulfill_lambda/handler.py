import os
import random
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
    if random.choices([True, False], weights=[0.9, 0.1])[0]:  # hard coded probability
        dynamodb_table.update_item(
            Key={"unique_identifier": event["unique_identifier"], "action": "fulfill"},
            UpdateExpression="SET vrf_value = :vrf_value, fulfill_time_actual = :fta",
            ExpressionAttributeValues={
                ":vrf_value": random.randint(
                    event["min_random_value"], event["max_random_value"]
                ),
                ":fta": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S%z"),
            },
        )
    else:
        dynamodb_table.update_item(
            Key={"unique_identifier": event["unique_identifier"], "action": "fulfill"},
            UpdateExpression="ADD failed_fulfill_attempts :inc",
            ExpressionAttributeValues={":inc": 1},
        )
        raise RuntimeError("Simulating intermittent failure")
