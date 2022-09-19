from collections import namedtuple

from handler import lambda_handler


def lambda_context():
    lambda_context = {
        "function_name": ...,
        "memory_limit_in_mb": ...,
        "invoked_function_arn": ...,
        "aws_request_id": ...,
    }
    return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())


print(
    lambda_handler(
        event={
            "wait_time": 142,
            "unique_identifier": "mock-unique-identifier",
            "min_random_value": 1,
            "max_random_value": 42,
        },
        context=lambda_context(),
    )
)
