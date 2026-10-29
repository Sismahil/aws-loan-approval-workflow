# Lambda source code

This folder contains the six Lambda source files supplied for the educational project:

- `SubmitApplication.py`
- `GetApplication.py`
- `CreditCheck.py`
- `FraudCheck.py`
- `RequestReview.py`
- `ReviewCallback.py`

Before publishing, compare each file with the code currently deployed in the corresponding AWS Lambda function. These files passed Python syntax checks, but that does not prove they match the deployed versions or that they have been integration-tested from this package.

Do not commit AWS credentials, Step Functions task tokens, review tokens, real applicant data, or secret environment-variable values. Document environment-variable names only.
