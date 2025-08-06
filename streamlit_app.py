import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# -----------------------------
# Solana RPC 설정 및 환율 API
# -----------------------------
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=c28b8417-e34d-480e-b57b-7098c92f3bd7"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=krw"

st.set_page_config(page_title="Solana Wallet Tracker (RPC+KRW)", layout="wide")
st.title("🔍 Solana Wallet Tracker (KRW Edition)")
st.markdown("Track SOL transfers, token purchases, and profits in KRW using Solana RPC and CoinGecko API.")

wallet_address = st.text_input("Enter Solana Wallet Address:")

# -----------------------------
# Helper functions
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

def get_sol_krw():
    try:
        res = requests.get(COINGECKO_API)
        return res.json().get("solana", {}).get("krw", 0)
    except:
        return 0

# -----------------------------
# 데이터 수집 및 분석
# -----------------------------
if wallet_address:
    with st.spinner("🔄 Fetching recent transactions and exchange rate..."):
        sigs = get_signatures(wallet_address)
        transactions = [get_transaction(sig["signature"]) for sig in sigs if "signature" in sig]
        sol_krw = get_sol_krw()

    transfers = []
    token_activities = []

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
                            "Amount (KRW)": amount_change * sol_krw,
                            "Tx Hash": signature
                        })

            # Check token transfers (SPL tokens)
            instructions = tx.get("meta", {}).get("postTokenBalances", [])
            for token in instructions:
                mint = token.get("mint")
                ui_amount = token.get("uiTokenAmount", {}).get("uiAmountString", "0")
                owner = token.get("owner", "")
                if owner == wallet_address:
                    token_activities.append({
                        "Time": dt,
                        "Mint Address": mint,
                        "Token Amount": ui_amount,
                        "Tx Hash": signature
                    })
        except Exception as e:
            continue

    if transfers:
        df = pd.DataFrame(transfers)
        st.subheader("📜 SOL Transfers (with KRW)")
        st.dataframe(df.sort_values("Time", ascending=False), use_container_width=True)

        received = df[df["Amount (SOL)"] > 0]["Amount (SOL)"].sum()
        sent = -df[df["Amount (SOL)"] < 0]["Amount (SOL)"].sum()
        profit = received - sent
        profit_krw = profit * sol_krw

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Received (SOL)", f"{received:.4f}")
        col2.metric("💸 Sent (SOL)", f"{sent:.4f}")
        col3.metric("📈 Net Profit (SOL)", f"{profit:.4f}")
        col4.metric("💵 Net Profit (KRW)", f"₩{profit_krw:,.0f}")
    else:
        st.warning("⚠️ No SOL transfer data found in recent transactions.")

    if token_activities:
        st.subheader("🪙 Token Purchases / Holdings")
        df_tokens = pd.DataFrame(token_activities)
        st.dataframe(df_tokens.sort_values("Time", ascending=False), use_container_width=True)
    else:
        st.info("ℹ️ No SPL token activity found in recent transactions.")
