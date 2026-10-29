def lambda_handler(event, context):
    if event.get("simulateFailure"):
        raise Exception("CreditBureauUnavailable")

    income = max(float(event["annualIncome"]), 1)
    debt = float(event["existingDebt"])
    loan = float(event["loanAmount"])

    ratio = (debt + loan) / income
    score = int(850 - min(ratio, 1.5) * 200)

    return {"creditScore": max(score, 300)}