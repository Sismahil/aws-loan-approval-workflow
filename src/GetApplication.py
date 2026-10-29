
import json
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb")


def lambda_handler(event, context):
    app_id = (event.get("pathParameters") or {}).get("applicationId")

    if not app_id:
        return respond(400, {"error": "Missing application ID"})

    try:
        response = dynamodb.get_item(
            TableName=os.environ["TABLE_NAME"],
            Key={"applicationId": {"S": app_id}},
            ConsistentRead=True
        )
        item = response.get("Item")

    except ClientError:
        print("DynamoDB GetItem failed.")
        return respond(500, {"error": "Unable to retrieve application status"})

    if not item:
        return respond(404, {"error": "Application not found"})

    # Return only approved public status fields.
    # Never expose taskToken or reviewToken.
    payload = {
        "applicationId": app_id,
        "status": item.get("status", {}).get("S", "UNKNOWN"),
        "loanAmount": (
            float(item["loanAmount"]["N"])
            if "loanAmount" in item
            else None
        ),
        "decidedAt": item.get("decidedAt", {}).get("S")
    }

    return respond(200, payload)


def respond(code, payload):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff"
        },
        "body": json.dumps(payload)
    }
