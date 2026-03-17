"""
Generate a realistic synthetic B2B SaaS GTM dataset and load it into DuckDB.

Creates: accounts, leads, opportunities, campaigns, campaign-lead touchpoints,
and product usage data modeled after a mid-stage SaaS company.
"""

import duckdb
import numpy as np
import pandas as pd
from pathlib import Path

# Reproducible
np.random.seed(42)

# --- Config ---
N_ACCOUNTS = 2000
N_LEADS = 8000
N_CAMPAIGNS = 45
DATE_START = "2025-01-01"
DATE_END = "2026-02-28"

INDUSTRIES = [
    "Technology", "Financial Services", "Healthcare", "Manufacturing",
    "Retail", "Education", "Media", "Professional Services",
    "Government", "Energy"
]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
REGION_WEIGHTS = [0.50, 0.25, 0.15, 0.10]

CHANNELS = ["paid_search", "organic", "events", "outbound", "partner", "plg"]
CHANNEL_WEIGHTS = [0.20, 0.15, 0.10, 0.20, 0.10, 0.25]

TITLES = [
    "VP of Engineering", "Director of Product", "CTO", "Head of Operations",
    "VP of Marketing", "Director of IT", "Chief of Staff", "VP of Sales",
    "Head of Data", "Product Manager", "Engineering Manager", "COO"
]

CAMPAIGN_NAMES = {
    "paid_search": ["Google Brand", "Google Non-Brand", "Bing Ads", "LinkedIn Ads - Awareness",
                     "LinkedIn Ads - Retargeting", "Google Display", "Reddit Ads"],
    "organic": ["Blog - Product Updates", "Blog - Thought Leadership", "SEO Landing Pages",
                "YouTube Channel", "Podcast Sponsorship", "Social Organic"],
    "events": ["SaaStr Annual 2025", "Dreamforce 2025", "Web Summit", "Customer Summit Q3",
               "Regional Roadshow - NYC", "Regional Roadshow - London", "Virtual Workshop Series"],
    "outbound": ["Enterprise ABM Tier 1", "Enterprise ABM Tier 2", "Mid-Market SDR Blitz",
                  "Win-Back Campaign", "Expansion Outreach", "Executive Dinner Series"],
    "partner": ["AWS Marketplace", "Salesforce AppExchange", "Partner Co-Sell", "SI Referral Program",
                "Technology Alliance"],
    "plg": ["Free Trial", "Freemium Signup", "Product-Led Onboarding", "In-App Upgrade Prompt",
            "Usage-Based Expansion"]
}


def generate_accounts():
    """Generate dim_accounts."""
    employee_counts = np.concatenate([
        np.random.randint(20, 200, size=int(N_ACCOUNTS * 0.45)),      # SMB
        np.random.randint(200, 2000, size=int(N_ACCOUNTS * 0.35)),    # Mid-Market
        np.random.randint(2000, 50000, size=int(N_ACCOUNTS * 0.20)),  # Enterprise
    ])
    np.random.shuffle(employee_counts)
    employee_counts = employee_counts[:N_ACCOUNTS]

    segments = np.where(employee_counts < 200, "SMB",
               np.where(employee_counts < 2000, "Mid-Market", "Enterprise"))

    # Enterprise more likely to be customers with higher ARR
    is_customer = np.zeros(N_ACCOUNTS, dtype=bool)
    arr = np.zeros(N_ACCOUNTS)

    for i in range(N_ACCOUNTS):
        if segments[i] == "Enterprise":
            is_customer[i] = np.random.random() < 0.30
            if is_customer[i]:
                arr[i] = np.random.lognormal(mean=11.5, sigma=0.5)  # ~$100K-$500K
        elif segments[i] == "Mid-Market":
            is_customer[i] = np.random.random() < 0.20
            if is_customer[i]:
                arr[i] = np.random.lognormal(mean=10.2, sigma=0.6)  # ~$20K-$100K
        else:
            is_customer[i] = np.random.random() < 0.10
            if is_customer[i]:
                arr[i] = np.random.lognormal(mean=9.0, sigma=0.5)  # ~$5K-$25K

    arr = np.round(arr, -2)  # Round to nearest hundred

    accounts = pd.DataFrame({
        "account_id": [f"ACC-{i:05d}" for i in range(N_ACCOUNTS)],
        "company_name": [f"Company {i}" for i in range(N_ACCOUNTS)],
        "industry": np.random.choice(INDUSTRIES, N_ACCOUNTS),
        "employee_count": employee_counts,
        "segment": segments,
        "region": np.random.choice(REGIONS, N_ACCOUNTS, p=REGION_WEIGHTS),
        "created_at": pd.to_datetime(
            np.random.choice(pd.date_range(DATE_START, DATE_END), N_ACCOUNTS)
        ),
        "is_customer": is_customer,
        "arr": arr,
    })
    return accounts


def generate_leads(accounts):
    """Generate dim_leads with realistic funnel progression."""
    dates = pd.date_range(DATE_START, DATE_END)
    leads = []

    for i in range(N_LEADS):
        acct = accounts.sample(1).iloc[0]
        created_at = np.random.choice(dates)
        channel = np.random.choice(CHANNELS, p=CHANNEL_WEIGHTS)

        # Lead score: enterprise and mid-market leads score higher
        base_score = {"SMB": 40, "Mid-Market": 55, "Enterprise": 65}[acct["segment"]]
        lead_score = int(np.clip(np.random.normal(base_score, 20), 5, 100))

        # Funnel progression based on score
        is_mql = lead_score >= 80
        # Higher-scoring MQLs more likely to progress
        is_sql = is_mql and np.random.random() < (0.25 + (lead_score - 80) * 0.015)
        is_opp = is_sql and np.random.random() < 0.55
        is_won = is_opp and np.random.random() < (
            {"SMB": 0.20, "Mid-Market": 0.28, "Enterprise": 0.22}[acct["segment"]]
        )
        is_lost = is_opp and not is_won and np.random.random() < 0.65

        if is_won:
            status = "closed_won"
        elif is_lost:
            status = "closed_lost"
        elif is_opp:
            status = "opportunity"
        elif is_sql:
            status = "sql"
        elif is_mql:
            status = "mql"
        elif np.random.random() < 0.05:
            status = "disqualified"
        else:
            status = "new"

        created_dt = pd.Timestamp(created_at)
        mql_at = (created_dt + pd.Timedelta(days=np.random.randint(1, 30))) if is_mql else None
        sql_at = (mql_at + pd.Timedelta(days=np.random.randint(3, 45))) if is_sql else None

        leads.append({
            "lead_id": f"LEAD-{i:06d}",
            "account_id": acct["account_id"],
            "email": f"contact{i}@company.com",
            "title": np.random.choice(TITLES),
            "lead_source": channel,
            "lead_score": lead_score,
            "status": status,
            "created_at": created_dt,
            "mql_at": mql_at,
            "sql_at": sql_at,
        })

    return pd.DataFrame(leads)


def generate_campaigns():
    """Generate fct_campaigns."""
    campaigns = []
    campaign_id = 0

    for channel, names in CAMPAIGN_NAMES.items():
        for name in names:
            start = pd.Timestamp(DATE_START) + pd.Timedelta(days=np.random.randint(0, 60))
            duration = np.random.randint(30, 365)
            end = start + pd.Timedelta(days=duration)
            if end > pd.Timestamp(DATE_END):
                end = None

            budget = {
                "paid_search": np.random.uniform(30000, 150000),
                "organic": np.random.uniform(5000, 30000),
                "events": np.random.uniform(20000, 200000),
                "outbound": np.random.uniform(15000, 80000),
                "partner": np.random.uniform(10000, 60000),
                "plg": np.random.uniform(5000, 40000),
            }[channel]

            spend_ratio = np.random.uniform(0.6, 1.1)
            spend = min(budget * spend_ratio, budget * 1.15)

            campaigns.append({
                "campaign_id": f"CAMP-{campaign_id:04d}",
                "campaign_name": name,
                "channel": channel,
                "start_date": start,
                "end_date": end,
                "budget": round(budget, 2),
                "spend": round(spend, 2),
            })
            campaign_id += 1

    return pd.DataFrame(campaigns)


def generate_campaign_leads(campaigns, leads):
    """Generate bridge_campaign_leads — multi-touch attribution."""
    bridge = []
    dates = pd.date_range(DATE_START, DATE_END)

    for _, lead in leads.iterrows():
        # Each lead has 1-5 campaign touches
        n_touches = np.random.choice([1, 2, 3, 4, 5], p=[0.35, 0.30, 0.20, 0.10, 0.05])

        # Filter campaigns matching lead's channel for first touch
        channel_campaigns = campaigns[campaigns["channel"] == lead["lead_source"]]
        if len(channel_campaigns) == 0:
            channel_campaigns = campaigns

        first_campaign = channel_campaigns.sample(1).iloc[0]
        touch_date = lead["created_at"]

        bridge.append({
            "campaign_id": first_campaign["campaign_id"],
            "lead_id": lead["lead_id"],
            "touch_date": touch_date,
            "is_first_touch": True,
            "touch_order": 1,
        })

        # Subsequent touches from any campaign
        for t in range(1, n_touches):
            next_campaign = campaigns.sample(1).iloc[0]
            touch_date = touch_date + pd.Timedelta(days=np.random.randint(1, 30))
            if touch_date > pd.Timestamp(DATE_END):
                break

            bridge.append({
                "campaign_id": next_campaign["campaign_id"],
                "lead_id": lead["lead_id"],
                "touch_date": touch_date,
                "is_first_touch": False,
                "touch_order": t + 1,
            })

    return pd.DataFrame(bridge)


def generate_opportunities(leads, accounts):
    """Generate fct_opportunities from leads that reached opportunity stage."""
    opp_leads = leads[leads["status"].isin(["opportunity", "closed_won", "closed_lost"])].copy()
    opps = []

    for _, lead in opp_leads.iterrows():
        acct = accounts[accounts["account_id"] == lead["account_id"]].iloc[0]

        # Deal size varies by segment
        amount = {
            "SMB": np.random.lognormal(mean=9.2, sigma=0.5),
            "Mid-Market": np.random.lognormal(mean=10.5, sigma=0.5),
            "Enterprise": np.random.lognormal(mean=11.8, sigma=0.5),
        }[acct["segment"]]
        amount = round(amount, -2)

        created_at = lead["sql_at"] + pd.Timedelta(days=np.random.randint(1, 14)) if lead["sql_at"] else lead["created_at"]

        is_won = lead["status"] == "closed_won"
        is_closed = lead["status"] in ("closed_won", "closed_lost")

        if is_closed:
            days_to_close = {"SMB": 25, "Mid-Market": 55, "Enterprise": 90}[acct["segment"]]
            closed_at = created_at + pd.Timedelta(days=int(np.random.normal(days_to_close, 15)))
            stage = "Closed Won" if is_won else "Closed Lost"
            close_date = closed_at
        else:
            closed_at = None
            stage = np.random.choice(["Stage 2", "Stage 3", "Stage 4", "Stage 5"],
                                     p=[0.30, 0.35, 0.25, 0.10])
            close_date = created_at + pd.Timedelta(days=np.random.randint(30, 120))

        opps.append({
            "opportunity_id": f"OPP-{len(opps):06d}",
            "account_id": lead["account_id"],
            "lead_id": lead["lead_id"],
            "owner_id": f"REP-{np.random.randint(1, 20):03d}",
            "stage": stage,
            "amount": amount,
            "created_at": created_at,
            "close_date": close_date,
            "closed_at": closed_at,
            "is_won": is_won,
        })

    return pd.DataFrame(opps)


def generate_product_usage(accounts):
    """Generate fct_product_usage for customer accounts."""
    customers = accounts[accounts["is_customer"]].copy()
    dates = pd.date_range(DATE_START, DATE_END)
    usage = []

    for _, acct in customers.iterrows():
        # Not every customer has usage every day
        active_days = np.random.choice(dates, size=int(len(dates) * np.random.uniform(0.4, 0.9)),
                                        replace=False)

        base_dau = int(acct["employee_count"] * np.random.uniform(0.05, 0.30))
        base_dau = max(base_dau, 1)

        for day in sorted(active_days):
            dau = max(1, int(np.random.normal(base_dau, base_dau * 0.2)))
            usage.append({
                "account_id": acct["account_id"],
                "usage_date": day,
                "dau": dau,
                "features_used": np.random.randint(2, 25),
                "api_calls": int(np.random.lognormal(mean=5, sigma=1.5)),
                "storage_mb": round(np.random.lognormal(mean=6, sigma=1), 2),
            })

    return pd.DataFrame(usage)


def main():
    print("Generating synthetic B2B SaaS GTM dataset...")

    print("  → Accounts...")
    accounts = generate_accounts()

    print("  → Leads...")
    leads = generate_leads(accounts)

    print("  → Campaigns...")
    campaigns = generate_campaigns()

    print("  → Campaign-Lead touchpoints...")
    bridge = generate_campaign_leads(campaigns, leads)

    print("  → Opportunities...")
    opportunities = generate_opportunities(leads, accounts)

    print("  → Product usage...")
    product_usage = generate_product_usage(accounts)

    # Load into DuckDB
    db_path = Path(__file__).parent.parent / "data" / "gtm.duckdb"
    db_path.parent.mkdir(exist_ok=True)

    print(f"\nLoading into DuckDB at {db_path}...")
    con = duckdb.connect(str(db_path))

    con.execute("DROP TABLE IF EXISTS bridge_campaign_leads")
    con.execute("DROP TABLE IF EXISTS fct_product_usage")
    con.execute("DROP TABLE IF EXISTS fct_opportunities")
    con.execute("DROP TABLE IF EXISTS fct_campaigns")
    con.execute("DROP TABLE IF EXISTS dim_leads")
    con.execute("DROP TABLE IF EXISTS dim_accounts")

    con.execute("CREATE TABLE dim_accounts AS SELECT * FROM accounts")
    con.execute("CREATE TABLE dim_leads AS SELECT * FROM leads")
    con.execute("CREATE TABLE fct_campaigns AS SELECT * FROM campaigns")
    con.execute("CREATE TABLE bridge_campaign_leads AS SELECT * FROM bridge")
    con.execute("CREATE TABLE fct_opportunities AS SELECT * FROM opportunities")
    con.execute("CREATE TABLE fct_product_usage AS SELECT * FROM product_usage")

    # Print summary
    for table in ["dim_accounts", "dim_leads", "fct_campaigns",
                  "bridge_campaign_leads", "fct_opportunities", "fct_product_usage"]:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  ✓ {table}: {count:,} rows")

    con.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
