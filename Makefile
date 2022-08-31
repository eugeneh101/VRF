create_lambda_layer_dependencies:
	rm -rf source/vrf_request_lambda/__lambda_dependencies__
	python -m pip install -r source/vrf_request_lambda/requirements.txt -t source/vrf_request_lambda/__lambda_dependencies__  # machine that `cdk deploy` must have same Python version as deployed Lambdas, ie Python 3.9
	rm -rf source/vrf_request_lambda/__lambda_dependencies__/*.dist-info
