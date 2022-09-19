import os
import sys

sys.path.insert(
    0, "./__lambda_dependencies__"
)  # folder created by Makefile during `cdk deploy`
from typing import Any, Union

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from beartype import beartype


logger = Logger(level="INFO")


@logger.inject_lambda_context(log_event=True)
@beartype
def lambda_handler(
    event: dict,
    context: Union[
        Any,
        LambdaContext,  # AWS's `context` isn't precisely a `LambdaContext` instance
        tuple,  # namedtuple is used in `scratch.py`
    ],
) -> dict:
    event["wait_time"] -= float(os.environ["WAIT_TIME_IN_SECONDS"])
    return event
