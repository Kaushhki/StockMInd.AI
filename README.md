# StockMind AI

An automated inventory forecasting and management agent that predicts stockouts, calculates optimal reorder quantities, and provides AI-powered insights through a conversational interface.

## Overview

StockMind AI analyzes inventory data to identify products at risk of stocking out, recommends when and how much to reorder using an EOQ (Economic Order Quantity) model, and highlights profit opportunities. It is available both as a terminal-based automation agent and as a full web dashboard with a real-time AI chat assistant.

Users can upload their own inventory CSV, or use the bundled 200-product sample dataset. All data, chat history, and historical trends are persisted in a local SQLite database.

## Features

- Stockout forecasting based on current stock levels and daily sales velocity
- EOQ-based optimal reorder quantity calculations, factoring in ordering and holding costs
- Automatic classification of products into Critical, Reorder, Overstock, and Healthy status
- Profit and revenue-at-risk analysis by product and category
- AI-generated plain-English briefings and a conversational chat assistant grounded in live inventory data
- Upload your own inventory CSV, with clear validation errors for malformed files
- Persistent chat history and historical trend tracking via SQLite
- CLI dashboard with formatted tables and panels
- Scheduled daily automation with CSV report export
- Web dashboard with live KPIs, category filters, trends, and chat

## Architecture

The project separates data loading, forecasting logic, alerting, AI integration, persistence, and presentation into independent modules.

```
data/sample_inventory.csv   Bundled sample dataset (200 products).

forecasting.py               Loads inventory data (bundled, a file path,
                              or an uploaded file) and computes stockout
                              dates, EOQ, cost, and profit metrics.
                              Validates schema and raises clear errors.

alerts.py                    Classifies products into alert categories
                              and builds summary statistics. No display
                              or storage logic.

ai_insights.py                Handles all Groq API calls: one-shot
                              briefings and multi-turn chat, grounded in
                              current inventory data.

db.py                        SQLite persistence for chat history and
                              historical inventory snapshots.

agent.py                     CLI dashboard (Rich), CSV export, and the
                              daily scheduler.

app.py                       Streamlit web dashboard with live tabs,
                              file upload, trends, and chat.
```

Each module can be used and tested independently of the others.

## Setup

Clone the repository and install dependencies:

```
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

A `.env.example` file is provided as a template. Never commit your actual `.env` file.

## Usage

### Web dashboard

```
streamlit run app.py
```

Opens a browser-based dashboard with live KPIs, critical alerts, profit analysis, full inventory browsing, historical trends, and an AI chat assistant. Upload your own inventory CSV from the sidebar, or use the bundled sample data.

Your uploaded CSV must include these columns: `product_id`, `product_name`, `category`, `current_stock`, `unit`, `reorder_point`, `reorder_quantity`, `unit_cost`, `lead_time_days`, `daily_sales_avg`.

### CLI agent

Run a single forecast cycle on the bundled sample data:

```
python agent.py --once
```

Run against your own CSV:

```
python agent.py --once --csv path/to/your_inventory.csv
```

Run continuously on a daily schedule:

```
python agent.py --daily-at 08:00
```

Each run prints a formatted report to the terminal, exports a timestamped CSV to the `reports/` folder, and saves a snapshot to the database for trend tracking.

## How the forecasting works

Days until stockout is calculated as current stock divided by average daily sales. A product is marked Critical if it will run out before a new order could arrive, given its lead time, and Reorder if it is approaching that threshold.

Optimal order quantity uses the EOQ formula:

```
EOQ = sqrt( (2 x Annual Demand x Ordering Cost) / Holding Cost per Unit )
```

The final recommended order quantity is the larger of the calculated EOQ and the supplier's minimum reorder quantity.

## AI integration

AI features use Groq's API with the `openai/gpt-oss-120b` model. All AI calls are grounded in the current inventory summary rather than raw data, keeping responses fast and accurate. If no API key is configured, the rest of the application continues to function normally, with AI features displaying a clear fallback message instead of failing.

## Persistence

A local SQLite database (`stockmind.db`, created automatically on first run) stores:

- Chat history, per browser session, so conversations survive a page refresh
- Inventory snapshots, saved on every run of either the CLI agent or the web app, powering the Trends tab

This file is excluded from version control via `.gitignore`, since it's local runtime state rather than source code.

## Deployment

The web app can be deployed for free on Streamlit Community Cloud:

1. Push this repository to GitHub, making sure `.env` and `stockmind.db` are not included (check with `git status` before committing).
2. Go to share.streamlit.io and connect your GitHub repository.
3. Set the main file path to `app.py`.
4. In the app's Settings, add your Groq API key under Secrets, in this format:
   ```
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
5. Deploy. The app will read the key from Streamlit's secrets manager automatically; no code changes are needed since `ai_insights.py` checks both `.env` (for local development) and `st.secrets` (for cloud deployment).

## Tech stack

Python, Pandas, Streamlit, Rich, Groq API, SQLite, schedule

## Notes

The bundled dataset is sample data for demonstration purposes. Connecting the forecasting layer to a live inventory database or POS system would require no changes to the presentation layer, since `app.py` and `agent.py` only depend on the data shape returned by `forecasting.load_data()`.
