import os
import boto3
import secrets
from urllib.parse import urlencode

dynamodb = boto3.client("dynamodb")
sns = boto3.client("sns")


def lambda_handler(event, context):
    app_id = event["applicationId"]
    level = event["reviewLevel"]

    if level not in ("UNDERWRITER", "SENIOR"):
        raise ValueError("Invalid review level")

    status = (
        "PENDING_REVIEW"
        if level == "UNDERWRITER"
        else "ESCALATED"
    )

    # Generate a unique, unpredictable review token.
    review_token = secrets.token_urlsafe(32)

    # Store the task token, review token, and status.
    dynamodb.update_item(
        TableName=os.environ["TABLE_NAME"],
        Key={"applicationId": {"S": app_id}},
        UpdateExpression=(
            "SET taskToken = :task, "
            "reviewToken = :review, "
            "#s = :status"
        ),
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":task": {"S": event["taskToken"]},
            ":review": {"S": review_token},
            ":status": {"S": status},
        },
    )

    base = os.environ["API_BASE_URL"].rstrip("/")

    common = {
        "applicationId": app_id,
        "level": level,
        "reviewToken": review_token,
    }

    approve = (
        f"{base}/review?"
        + urlencode({**common, "action": "approve"})
    )
    reject = (
        f"{base}/review?"
        + urlencode({**common, "action": "reject"})
    )

    sns.publish(
        TopicArn=os.environ["TOPIC_ARN"],
        Subject=f"[{level}] Loan review needed: {app_id}",
        Message=(
            f"Applicant: {event['applicantName']}\n"
            f"Loan amount: {event['loanAmount']}\n"
            f"Credit score: {event['creditScore']}\n"
            f"Review level: {level}\n\n"
            f"Approve: {approve}\n"
            f"Reject: {reject}\n\n"
            "Treat these review links as confidential. "
            "Each link is intended for one use."
        ),
    )

    return {"requested": True}

