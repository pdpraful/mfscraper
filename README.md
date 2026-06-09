# International Mutual Fund Capacity Discovery Agent

This is an autonomous investment-capacity intelligence agent designed to discover Indian mutual funds that invest overseas and currently have available RBI overseas investment capacity. 

The goal of this agent is NOT to report news, but to deterministically identify actual investable opportunities based on fund-level flows, AUM changes, and NFO status.

## Features

- **Automated Tracking:** Automatically tracks all Indian mutual funds with overseas exposure (e.g., US equities, Global equities, Nasdaq, S&P 500) using daily data from AMFI.
- **Capacity Scoring Engine:** Analyzes AUM trends, net flows, and fund age to calculate a deterministic Capacity Score (0-100) indicating the likelihood of available investment capacity.
- **Background Scheduler:** Runs completely autonomously via `APScheduler`. Scrapes data daily at 06:00 IST and performs a deep universe audit every Sunday.
- **Rich Reporting & Fallbacks:** Capable of sending daily HTML reports with ranked high-conviction investment opportunities directly to your inbox. If email is disabled, the agent gracefully falls back to printing a clean, formatted text summary to your terminal and saves the interactive HTML dashboard directly to your Desktop.
- **Extensible AMC Framework:** Includes an advanced, rate-limited Playwright framework to scrape AMC websites. Extracts notices directly from AMC websites and autonomously downloads and parses 50+ page AMC Factsheet PDFs using `pdfplumber` to extract highly accurate, fund-level AUM figures.

## Architecture Flow

```text
       [ AMFI Website ]                     [ AMC Websites ]
      (Daily NAV, AUM, NFOs)             (Notices, Addendums, SIDs)
               │                                      │
               ▼                                      ▼
       +---------------+                     +------------------+
       | amfi_scraper  |                     |  amc/ scrapers   |
       |  (Requests)   |                     |  (Playwright)    |
       +---------------+                     +------------------+
               │                                      │
               └─────────────────┐  ┌─────────────────┘
                                 ▼  ▼
                       +--------------------+
                       |                    |
                       |  SQLite Database   | <--- Historical AUM Trends
                       | (funds, notices)   |      (30-day tracking)
                       |                    |
                       +--------------------+
                                 │
                                 ▼
                       +--------------------+
                       |                    |
                       |  Capacity Engine   |
                       |  (Scoring 0-100)   |
                       |                    |
                       +--------------------+
                                 │
                                 ▼
                       +--------------------+
                       |                    |
                       |  Email Reporter    |
                       |  (SMTP via .env)   |
                       |                    |
                       +--------------------+
                                 │
                                 ▼
                          [ Your Inbox ]
                 (Daily HTML Ranked Recommendations)
```

## Project Structure

```
MFScraper/
├── main.py                     # Entry point for the application and scheduler
├── core/
│   ├── config.py               # Settings (SMTP, DB path, Target URLs)
│   └── scheduler.py            # APScheduler definitions for daily/weekly runs
├── database/
│   ├── db.py                   # SQLite connection and session management
│   └── models.py               # SQLAlchemy ORM models (Fund, AUMHistory, Notice, CapacityScoreHistory)
├── engine/
│   └── capacity_engine.py      # Core logic for evaluating the 0-100 capacity scores
├── notifier/
│   └── email_reporter.py       # Logic for formatting and sending SMTP emails
├── scrapers/
│   ├── amfi_scraper.py         # Daily NAV/AUM scraper (Tier 2 data)
│   └── amc/
│       ├── base.py             # Base Playwright scraping framework for AMCs
│       └── motilal.py          # Template scraper for Motilal Oswal
└── requirements.txt            # Project dependencies
```

## Setup & Installation

**One-Step Interactive Remote Install:**
You can install and configure the agent completely autonomously directly from GitHub without manually cloning the repository. Just paste this command into your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/pdpraful/mfscraper/main/remote_install.sh | bash
```

This script will securely download the project to `~/.mfscraper-app`, configure the Python virtual environment, install dependencies, set up your terminal commands, and **interactively prompt you to configure your email settings (optional)**.

**If you skip the email setup prompt during installation**, the agent will automatically fall back to printing the ranked fund summary directly to your terminal and saving the rich HTML dashboard file directly to your Desktop!

**(Optional) How to Generate a Google App Password for Email:**
If you want to configure email reporting during the installation prompt, you must use a **Google App Password** (you cannot use your normal Gmail password).
1. Go to your Google Account management page: [https://myaccount.google.com/](https://myaccount.google.com/)
2. On the left navigation panel, click **Security**.
3. Under the "How you sign in to Google" section, ensure **2-Step Verification** is turned ON.
4. Click on **2-Step Verification**. Scroll to the bottom and click on **App passwords**.
5. You will be prompted to enter an "App name". Type `MF Scraper Agent` and click **Create**.
6. A yellow box will appear with a 16-character password. Copy this password and provide it when the terminal asks for it during installation.

## Usage

To start the background agent, simply run:

```bash
# To run the manual sweep immediately:
mfscraper --runonce

# To start the background scheduler daemon:
mfscraper --daemon
```

Upon execution, the agent will immediately:
1. Initialize the SQLite database.
2. Run a full initial sweep (downloading AMFI data, adding all matching international funds, and evaluating capacity).
3. Start the background scheduler, running silently until 06:00 IST the next day.

## Logic Overview (The Capacity Score)

The engine assigns each fund a score from 0-100 based on:
- **Signal A:** Reopening or Suspension Notices (Requires specific AMC scrapers).
- **Signal C:** AUM Declines (e.g., A large outflow implies newly created headroom, extracted from daily/monthly factsheets).
- **Signal E:** NFO Status (Newly launched funds typically have unused allocation).

A score of `90-100` signifies a high likelihood that the fund is currently accepting fresh lump-sum investments.

## Disclaimer

**Educational Purposes Only.** This project is strictly for educational, learning, and research purposes. It does not constitute financial advice, investment recommendations, or an offer to sell or a solicitation to buy any securities. The automated scores and outputs generated by this tool are based on heuristic logic and may be inaccurate or out-of-date. Always consult a certified financial advisor before making any investment decisions. The creators and contributors of this repository are not responsible for any financial losses or damages incurred.

## License

This project is licensed under the [MIT License](LICENSE). You are completely free to use, modify, and distribute this software as per the terms of the license.
