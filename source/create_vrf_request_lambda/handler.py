import json
import random
import os
import sys
from typing import Union, Any

sys.path.insert(
    0, "./__lambda_dependencies__"
)  # folder created by Makefile during `cdk deploy`

import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import Logger
from beartype import beartype
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()
logger = Logger(level="INFO")
sqs_resource = boto3.resource("sqs", config=Config(region_name=os.environ["AWSREGION"]))
queue = sqs_resource.get_queue_by_name(QueueName=os.environ["QUEUE"])


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
    request_arrival_time = random.randint(0, 120)
    target_block_in_the_future = random.randint(0, 10)
    random_value_bounds = random.sample(range(0, 1000), 2)
    min_random_value, max_random_value = (
        min(random_value_bounds),
        max(random_value_bounds),
    )
    payload = {
        "target_block_in_the_future": target_block_in_the_future,
        "min_random_value": min_random_value,
        "max_random_value": max_random_value,
    }
    queue.send_message(
        MessageBody=json.dumps(payload), DelaySeconds=request_arrival_time
    )
    return
