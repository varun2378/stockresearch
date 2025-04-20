import pandas as pd
import requests
import time
import streamlit as st

st.set_page_config(page_title="Financial Overview", layout="wide")

API_KEY = "874WVCYGCPDM9YVS"
symbols = ["MSFT","IBM"]


@st.cache_data(ttl=86400)  # cache for 1 day
def fetch_data(function, symbol):
    url = "https://www.alphavantage.co/query"
    params = {"function": function, "symbol": symbol, "apikey": API_KEY}
    response = requests.get(url, params=params)
    return response.json()


@st.cache_data(ttl=86400)
def get_last_7_prices(symbol):
    data = fetch_data("TIME_SERIES_DAILY_ADJUSTED", symbol)
    ts = data.get("Time Series (Daily)", {})
    prices = []
    for date in sorted(ts.keys(), reverse=True)[:7]:
        price = ts[date].get("5. adjusted close", None)
        if price:
            prices.append(float(price))
    return prices


def extract_quarterly(data, keys, prefix):
    result = {}
    if "quarterlyReports" in data:
        for i, report in enumerate(data["quarterlyReports"][:4]):  # Latest 4 quarters
            for key in keys:
                col = f"{prefix}_{key}_Q{i+1}"
                result[col] = report.get(key, None)
    return result


@st.cache_data(ttl=86400)
def get_full_data(symbols):
    all_data = []

    for symbol in symbols:
        st.write(f"🔍 Processing `{symbol}`")
        overview = fetch_data("OVERVIEW", symbol)
        income_q = fetch_data("INCOME_STATEMENT", symbol)
        balance_q = fetch_data("BALANCE_SHEET", symbol)
        prices = get_last_7_prices(symbol)

        time.sleep(12)  # Respect API rate limit (5/min)

        row = {
            "Company Name": overview.get("Name", symbol),
            "Symbol": symbol,
            "Sector": overview.get("Sector"),
            "Industry": overview.get("Industry"),
            "Market Cap (USD Bn)": round(float(overview.get("MarketCapitalization", 0)) / 1e9, 2),
            "PE Ratio": overview.get("PERatio"),
            "EPS": overview.get("EPS"),
            "PEG": overview.get("PEGRatio"),
            "ProfitMargin": overview.get("ProfitMargin"),
            "OperatingMarginTTM": overview.get("OperatingMarginTTM"),
            "BookValue": overview.get("BookValue"),
            "PriceToBookRatio": overview.get("PriceToBookRatio")
           
            
            
            
            
        }

        # Add last 7 prices
        for i, p in enumerate(prices):
            row[f"Price_Day_{i+1}"] = p

        # Add quarterly income
        income_keys = ["totalRevenue", "grossProfit", "netIncome"]
        row.update(extract_quarterly(income_q, income_keys, "Income"))

        # Add quarterly balance sheet items
        balance_keys = ["totalAssets", "totalLiabilities", "totalShareholderEquity", "cashAndCashEquivalentsAtCarryingValue"]
        row.update(extract_quarterly(balance_q, balance_keys, "Balance"))

        all_data.append(row)

    return pd.DataFrame(all_data)


# Fetch data and cache it
df = get_full_data(symbols)

# Save to Excel
excel_file = "US StocksQuarterly_Financials.xlsx"
#df.to_excel(excel_file, index=False)

# Streamlit UI
st.title("📊 Financial Dashboard- US Stocks")

st.write("### Full Company Financials:")
st.dataframe(df)

# Filter
search = st.text_input("Search Company Name or Symbol")
if search:
    filtered_df = df[df["Company Name"].str.contains(search, case=False) | df["Symbol"].str.contains(search, case=False)]
    st.write("### 🔎 Filtered Results:")
    st.dataframe(filtered_df)

# Download Button
#st.download_button("Download Excel", data=open(excel_file, "rb").read(), file_name=excel_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
