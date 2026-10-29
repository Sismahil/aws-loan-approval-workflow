import json
import os
import hmac
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb")
sfn = boto3.client("stepfunctions")


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}

    app_id = params.get("applicationId")
    action = params.get("action")
    level = params.get("level", "UNDERWRITER")
    supplied_token = params.get("reviewToken")

    if (
        not app_id
        or action not in ("approve", "reject")
        or level not in ("UNDERWRITER", "SENIOR")
        or not supplied_token
    ):
        return page(400, "Invalid or incomplete review link.")

    try:
        response = dynamodb.get_item(
            TableName=os.environ["TABLE_NAME"],
            Key={"applicationId": {"S": app_id}},
            ConsistentRead=True
        )
    except ClientError:
        return page(500, "Unable to retrieve the review request.")

    item = response.get("Item")

    if not item:
        return page(404, "Application not found.")

    saved_token = item.get("reviewToken", {}).get("S")
    task_token = item.get("taskToken", {}).get("S")
    current_status = item.get("status", {}).get("S")

    expected_status = (
        "PENDING_REVIEW"
        if level == "UNDERWRITER"
        else "ESCALATED"
    )

    if (
        not saved_token
        or not hmac.compare_digest(saved_token, supplied_token)
        or not task_token
        or current_status != expected_status
    ):
        return page(409, "Invalid, expired, or already used review link.")

    # Atomically consume the review token to prevent reuse.
    now = datetime.now(timezone.utc).isoformat()

    try:
        dynamodb.update_item(
            TableName=os.environ["TABLE_NAME"],
            Key={"applicationId": {"S": app_id}},
            UpdateExpression=(
                "SET reviewTokenUsedAt = :now "
                "REMOVE reviewToken"
            ),
            ConditionExpression=(
                "reviewToken = :provided "
                "AND #status = :expected"
            ),
            ExpressionAttributeNames={
                "#status": "status"
            },
            ExpressionAttributeValues={
                ":now": {"S": now},
                ":provided": {"S": supplied_token},
                ":expected": {"S": expected_status}
            }
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        return page(409, "This review link has already been used.")
    except ClientError:
        return page(500, "Unable to secure the review request.")

    try:
        if action == "approve":
            sfn.send_task_success(
                taskToken=task_token,
                output=json.dumps({
                    "decidedBy": level,
                    "reviewAction": "approve"
                })
            )
        else:
            sfn.send_task_failure(
                taskToken=task_token,
                error="ReviewRejected",
                cause=f"Rejected by {level}"
            )

    except (
        sfn.exceptions.TaskTimedOut,
        sfn.exceptions.TaskDoesNotExist
    ):
        return page(410, "This review request has expired.")

    except ClientError:
        return page(500, "Unable to submit the review decision.")

    return page(200, f"Decision recorded: {action}.")


def page(code, message):
    safe_message = (
        message.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff"
        },
        "body": (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>Loan Review</title></head><body><h2>"
            + safe_message
            + "</h2></body></html>"
        )
    }
