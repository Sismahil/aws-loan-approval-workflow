import json
import os
import uuid
import boto3

sfn = boto3.client("stepfunctions")

REQUIRED = [
    "applicantName",
    "email",
    "annualIncome",
    "existingDebt",
    "loanAmount"
]


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return respond(400, {"error": "Invalid JSON"})

    if not isinstance(body, dict):
        return respond(400, {"error": "JSON body must be an object"})

    missing = [field for field in REQUIRED if field not in body]
    if missing:
        return respond(400, {"error": f"Missing fields: {missing}"})

    for field in ("annualIncome", "existingDebt", "loanAmount"):
        value = body[field]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        ):
            return respond(
                400,
                {"error": f"{field} must be a non-negative number"}
            )

    if body["annualIncome"] == 0 or body["loanAmount"] == 0:
        return respond(
            400,
            {"error": "Income and loan amount must be above zero"}
        )

    if not isinstance(body["applicantName"], str) or not body["applicantName"].strip():
        return respond(400, {"error": "Invalid applicant name"})

    if not isinstance(body["email"], str) or "@" not in body["email"]:
        return respond(400, {"error": "Invalid email"})

    application_id = str(uuid.uuid4())
    body["applicationId"] = application_id

    try:
        sfn.start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            name=application_id,
            input=json.dumps(body)
        )
    except Exception:
        print("Failed to start workflow execution")
        return respond(500, {"error": "Unable to submit application"})

    return respond(
        202,
        {
            "applicationId": application_id,
            "status": "SUBMITTED"
        }
    )


def respond(code, payload):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(payload)
    }

