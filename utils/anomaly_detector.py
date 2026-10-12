"""
anomaly_detector.py
--------------------
Detects unusual ("anomalous") transactions in a bank statement using
scikit-learn's Isolation Forest - a simple, unsupervised ML algorithm.

WHAT IT DOES (in plain English):
Isolation Forest works by trying to "isolate" each data point using
random splits of the data. Points that are easy to isolate (i.e. very
different from the rest) get flagged as anomalies. Since most
transactions are "normal" and unusual ones are rare, this works well
WITHOUT needing any labeled training data (nobody has to tell the
model "this transaction was fraud" ahead of time).

We use EXACTLY 5 features per transaction, as specified in the project:
  1. transaction_amount          - the amount of this transaction
  2. average_transaction_amount  - average amount across the statement
  3. amount_deviation            - how far this transaction is from that average
  4. transaction_frequency       - how many transactions happened that same day
  5. account_balance             - balance right after this transaction

IMPORTANT: this model does NOT prove fraud. It only flags transactions
that are statistically unusual compared to the account's own history.
Results are always labeled "potentially suspicious" / "unusual",
never "confirmed fraud".
"""

from sklearn.ensemble import IsolationForest


def build_features(transactions_df):
    """
    Build the 5 ML features required for anomaly detection.

    Args:
        transactions_df: pandas DataFrame with at least these columns:
            'date', 'description', 'amount', 'type' (CREDIT/DEBIT), 'balance'

    Returns:
        A new DataFrame with the 5 feature columns added.
    """
    df = transactions_df.copy()

    # Feature 1: transaction_amount (the raw amount, as-is)
    df["transaction_amount"] = df["amount"]

    # Feature 2: average_transaction_amount (same value repeated on
    # every row - the overall average for this statement)
    avg_amount = df["amount"].mean()
    df["average_transaction_amount"] = avg_amount

    # Feature 3: amount_deviation (distance from the average - bigger
    # means the transaction size itself is more unusual)
    df["amount_deviation"] = (df["amount"] - avg_amount).abs()

    # Feature 4: transaction_frequency (number of transactions that
    # happened on the same date - a burst of transactions can also be unusual)
    df["transaction_frequency"] = df.groupby("date")["date"].transform("count")

    # Feature 5: account_balance (balance right after the transaction)
    df["account_balance"] = df["balance"]

    return df


def detect_anomalies(transactions_df, contamination=0.1):
    """
    Run Isolation Forest on the transactions and flag anomalies.

    Args:
        transactions_df: DataFrame with transaction data (needs at
            least 'date', 'amount', 'balance' columns)
        contamination: expected proportion of anomalies in the data.
            0.1 means "assume roughly 10% of transactions could be
            unusual" - this is a tuning knob, not a guarantee.

    Returns:
        A DataFrame with two extra columns:
          - 'is_anomaly': True/False
          - 'anomaly_score': lower score = more unusual

    NOTE: Isolation Forest needs a reasonable number of data points to
    work well. With very few transactions, results aren't meaningful,
    so we skip the model and mark everything "not anomalous" instead
    of crashing or giving a nonsense answer.
    """
    if transactions_df is None or transactions_df.empty or len(transactions_df) < 3:
        df = transactions_df.copy() if transactions_df is not None else transactions_df
        if df is not None:
            df["is_anomaly"] = False
            df["anomaly_score"] = 0.0
        return df

    df = build_features(transactions_df)

    feature_cols = [
        "transaction_amount",
        "average_transaction_amount",
        "amount_deviation",
        "transaction_frequency",
        "account_balance",
    ]

    X = df[feature_cols].fillna(0)

    try:
        model = IsolationForest(
            contamination=contamination,
            random_state=42,   # fixed seed = reproducible results for the demo
            n_estimators=100,
        )
        predictions = model.fit_predict(X)     # -1 = anomaly, 1 = normal
        scores = model.decision_function(X)    # lower = more anomalous

        df["is_anomaly"] = predictions == -1
        df["anomaly_score"] = scores

    except Exception as e:
        print(f"[anomaly_detector] Error running Isolation Forest: {e}")
        df["is_anomaly"] = False
        df["anomaly_score"] = 0.0

    return df
