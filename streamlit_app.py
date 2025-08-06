import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# -----------------------------
# Solana Helius API 키 입력
# -----------------------------
API_KEY = "c28b8417-e34d-480e-b57b-7098c92f3bd7"
BASE_URL = f"https://mainnet.helius.xyz/v0/addresses"

st.set_page_config(page_title="Solana Wallet Tracker", layout="wide")

def get_solana_transactions(address):
    url = f"{BASE_URL}/{address}/transactions?api-key={API_KEY}&limit=100"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return resp.json()

def extract_sol_transfers(transactions, address):
    transfers = []
    for tx in transactions:
        timestamp = tx.get('timestamp')
        for transfer in tx.get('nativeTransfers', []):
            if transfer['fromUserAccount'] == address or transfer['toUserAccount'] == address:
                transfers.append({
                    'txHash': tx['signature'],
                    'datetime': datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                    'from': transfer['fromUserAccount'],
                    'to': transfer['toUserAccount'],
                    'amount_SOL': transfer['amount'] / 1e9
                })
    return transfers

def calculate_profit(transfers, address):
    sent = sum(tx['amount_SOL'] for tx in transfers if tx['from'] == address)
    received = sum(tx['amount_SOL'] for tx in transfers if tx['to'] == address)
    return received - sent, received, sent

# -----------------------------
# UI
# -----------------------------
st.title("🔍 Solana Wallet Tracker")
st.markdown("Track SOL transfers and calculate net profit for any Solana wallet.")

wallet_address = st.text_input("Enter Solana Wallet Address:")

if wallet_address:
    with st.spinner("Fetching transaction data from Helius..."):
        tx_data = get_solana_transactions(wallet_address)

    if not tx_data:
        st.error("Could not fetch data. Check wallet address or API key.")
    else:
        transfers = extract_sol_transfers(tx_data, wallet_address)
        if not transfers:
            st.warning("No SOL transfers found.")
        else:
            df = pd.DataFrame(transfers)
            df = df.sort_values(by='datetime', ascending=False)

            st.subheader("📜 Transfer History")
            st.dataframe(df, use_container_width=True)

            profit, received, sent = calculate_profit(transfers, wallet_address)
            col1, col2, col3 = st.columns(3)
            col1.metric("🔼 Received (SOL)", f"{received:.4f}")
            col2.metric("🔽 Sent (SOL)", f"{sent:.4f}")
            col3.metric("💰 Net Profit", f"{profit:.4f} SOL")

            st.success(f"✅ Net SOL Gain/Loss: **{profit:.4f} SOL**")
