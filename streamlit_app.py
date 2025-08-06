import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# -----------------------------
# Solana RPC 설정
# -----------------------------
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=c28b8417-e34d-480e-b57b-7098c92f3bd7"

st.set_page_config(page_title="Solana Wallet Tracker (RPC)", layout="wide")
st.title("🔍 Solana Wallet Tracker (RPC Edition)")
st.markdown("Track SOL transfers and net profit for any Solana wallet using direct RPC calls.")

wallet_address = st.text_input("Enter Solana Wallet Address:")

# -----------------------------
# RPC 호출 함수
# -----------------------------
def get_signatures(address, limit=30):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [address, {"limit": limit}]
    }
    res = requests.post(RPC_URL, json=payload)
    return res.json().get("result", [])

def get_transaction(signature):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, "json"]
    }
    res = requests.post(RPC_URL, json=payload)
    return res.json().get("result", {})

# -----------------------------
# 데이터 수집 및 분석
# -----------------------------
if wallet_address:
    with st.spinner("🔄 Fetching recent transactions..."):
        sigs = get_signatures(wallet_address)
        transactions = [get_transaction(sig["signature"]) for sig in sigs if "signature" in sig]

    transfers = []
    for tx in transactions:
        if not tx or "meta" not in tx or "transaction" not in tx:
            continue
        try:
            block_time = tx.get("blockTime", 0)
            dt = datetime.utcfromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S') if block_time else "N/A"
            signature = tx.get("transaction", {}).get("signatures", ["N/A"])[0]
            post_balances = tx.get("meta", {}).get("postBalances", [])
            pre_balances = tx.get("meta", {}).get("preBalances", [])
            accounts = tx.get("transaction", {}).get("message", {}).get("accountKeys", [])

            for i, acc in enumerate(accounts):
                if acc == wallet_address and i < len(pre_balances):
                    amount_change = (post_balances[i] - pre_balances[i]) / 1e9
                    if amount_change != 0:
                        transfers.append({
                            "Time": dt,
                            "Amount (SOL)": amount_change,
                            "Tx Hash": signature
                        })
        except Exception as e:
            continue

    if transfers:
        df = pd.DataFrame(transfers)
        st.subheader("📜 SOL Transfers")
        st.dataframe(df.sort_values("Time", ascending=False), use_container_width=True)

        received = df[df["Amount (SOL)"] > 0]["Amount (SOL)"].sum()
        sent = -df[df["Amount (SOL)"] < 0]["Amount (SOL)"].sum()
        profit = received - sent

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Received (SOL)", f"{received:.4f}")
        col2.metric("💸 Sent (SOL)", f"{sent:.4f}")
        col3.metric("📈 Net Profit", f"{profit:.4f}")
    else:
        st.warning("⚠️ No SOL transfer data found in recent transactions.")
