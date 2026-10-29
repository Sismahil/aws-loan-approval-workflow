BLOCKED_DOMAINS = {"tempmail.test"}


def lambda_handler(event, context):
    domain = event["email"].split("@")[-1].lower()

    if domain in BLOCKED_DOMAINS:
        return {
            "fraudRisk": "HIGH",
            "reason": "BLOCKED_EMAIL_DOMAIN"
        }

    if event["loanAmount"] > event["annualIncome"] * 2:
        return {
            "fraudRisk": "HIGH",
            "reason": "AMOUNT_TOO_HIGH_FOR_INCOME"
        }

    return {
        "fraudRisk": "LOW",
        "reason": "NONE"
    }


