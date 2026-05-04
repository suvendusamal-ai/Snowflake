def detect_fraud(session):

    query = """
        SELECT TXN_ID, ACCOUNT_ID, AMOUNT, FRAUD_SCORE(AMOUNT) AS RISK
        FROM TRANSACTIONS
        WHERE AMOUNT > 200000
    """

    rows = session.sql(query).collect()

    if not rows:
        return {
            "sql": query,
            "data": ["No suspicious transactions found"]
        }

    results = []

    for r in rows:
        results.append(
            f"Txn {r['TXN_ID']} | Account {r['ACCOUNT_ID']} | Amount {r['AMOUNT']} | Risk {r['RISK']}"
        )

    return {
        "sql": query,
        "data": results
    }