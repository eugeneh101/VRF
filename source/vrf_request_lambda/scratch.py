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


print(lambda_handler(event={}, context=lambda_context()))
