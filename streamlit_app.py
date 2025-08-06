import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --------------------------------------
# STEP 1. 설정
# --------------------------------------
API_KEY = "c28b8417-e34d-480e-b57b-7098c92f3bd7"  # ← 꼭 수정할 것!
BASE_URL = "https://mainnet.helius.xyz/v0/addresses"

st.set_page_config(page_title="Solana Wallet Tracker", layout="wide")
st.title("🔍 Solana Wallet Tracker")
st.markdown("Track SOL transfers and net profit for any Solana wallet using Helius API.")

# --------------------------------------
# STEP 2. 지갑 주소 입력
# --------------------------------------
wallet_address = st.text_input("Enter Solana Wallet Address:")

# --------------------------------------
# STEP 3. API로 트랜잭션 요청
# --------------------------------------
def get_transactions(address):
    url = f"{BASE_URL}/{address}/transactions?api-key={API_KEY}&limit=100"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to fetch transactions. \n\n**Error:** {e}")
        return None

# --------------------------------------
# STEP 4. 결과 처리 및 출력
# --------------------------------------
if wallet_address:
    with st.spinner("🔄 Loading transactions from Solana..."):
        data = get_transactions(wallet_address)

    if data:
        transfers = []
        for tx in data:
            ts = tx.get("timestamp")
            for transfer in tx.get("nativeTransfers", []):
                transfers.append({
                    "Time": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                    "From": transfer["fromUserAccount"],
                    "To": transfer["toUserAccount"],
                    "Amount (SOL)": transfer["amount"] / 1e9,
                    "Tx Hash": tx["signature"]
                })

        if not transfers:
            st.warning("⚠️ No SOL transfers found for this address.")
        else:
            df = pd.DataFrame(transfers)
            st.subheader("📜 Transaction History")
            st.dataframe(df.sort_values("Time", ascending=False), use_container_width=True)

            # 수익 계산
            sent = df[df["From"] == wallet_address]["Amount (SOL)"].sum()
            received = df[df["To"] == wallet_address]["Amount (SOL)"].sum()
            profit = received - sent

            col1, col2, col3 = st.columns(3)
            col1.metric("💸 Sent (SOL)", f"{sent:.4f}")
            col2.metric("💰 Received (SOL)", f"{received:.4f}")
            col3.metric("📈 Net Profit", f"{profit:.4f}")

            st.success(f"✅ Net Profit: **{profit:.4f} SOL**")
    else:
        st.error("❌ Failed to retrieve any data. Check the wallet address and API key.")
