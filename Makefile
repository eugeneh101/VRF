create_lambda_layer_dependencies:
	# eventually delete this entire file by moving dependency management to Docker via `BundlingOptions`
	rm -rf source/vrf_request_lambda/__lambda_dependencies__
	pip3 install -r source/vrf_request_lambda/requirements.txt -t source/vrf_request_lambda/__lambda_dependencies__  # machine that `cdk deploy` must have same Python version as deployed Lambdas, ie Python 3.9
	rm -rf source/vrf_request_lambda/__lambda_dependencies__/*.dist-info

	rm -rf source/trigger_sfn_lambda/__lambda_dependencies__
	pip3 install -r source/trigger_sfn_lambda/requirements.txt -t source/trigger_sfn_lambda/__lambda_dependencies__  # machine that `cdk deploy` must have same Python version as deployed Lambdas, ie Python 3.9
	rm -rf source/trigger_sfn_lambda/__lambda_dependencies__/*.dist-info

	rm -rf source/decrement_wait_time_lambda/__lambda_dependencies__
	pip3 install -r source/decrement_wait_time_lambda/requirements.txt -t source/decrement_wait_time_lambda/__lambda_dependencies__  # machine that `cdk deploy` must have same Python version as deployed Lambdas, ie Python 3.9
	rm -rf source/decrement_wait_time_lambda/__lambda_dependencies__/*.dist-info

	rm -rf source/vrf_fulfill_lambda/__lambda_dependencies__
	pip3 install -r source/vrf_fulfill_lambda/requirements.txt -t source/vrf_fulfill_lambda/__lambda_dependencies__  # machine that `cdk deploy` must have same Python version as deployed Lambdas, ie Python 3.9
	rm -rf source/vrf_fulfill_lambda/__lambda_dependencies__/*.dist-info
