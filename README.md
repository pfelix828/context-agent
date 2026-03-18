# Context Agent

An AI-powered data scientist that adapts to the stakeholder asking the question. Instead of generic "chat with your data" responses, Context Agent reads stakeholder profiles, domain knowledge, and analysis skills to deliver tailored, actionable insights.

## Features

- **Stakeholder-aware responses** — Select a team (Executive, Marketing, Sales, Product) and the agent adapts its tone, metrics, and recommendations
- **Interactive Plotly charts** — Trends, comparisons, and distributions rendered as interactive visualizations
- **Streaming responses** — Token-by-token streaming with live tool execution indicators
- **Configurable context layer** — Swap markdown files to adapt for any stakeholder or domain
- **Analysis skills** — Pre-built frameworks for funnel analysis, campaign ROI, revenue analysis, cohort retention, and more
- **Secure execution** — Read-only database, sandboxed Python with restricted imports

## The Idea

Data teams answer the same questions differently depending on who's asking. A VP of Marketing wants pipeline impact and budget recommendations. An executive wants ARR and bookings vs plan. A product manager wants engagement trends and retention curves. Context Agent makes this adaptation automatic by loading a configurable context layer before every interaction.

## How It Works

```
context/
├── agent.md             # Tone, depth, output format instructions
├── domain.md            # Business context — metric definitions, KPIs, segments
├── data_dictionary.md   # Schema documentation
└── stakeholders/
    ├── executive.md     # ARR, bookings, unit economics
    ├── marketing.md     # Pipeline, campaigns, MQLs, attribution
    ├── sales.md         # Pipeline health, win rates, forecast
    └── product.md       # DAU, feature adoption, retention

skills/
├── funnel_analysis.md   # Lead-to-revenue conversion analysis
├── campaign_roi.md      # Campaign performance and attribution
├── segmentation.md      # Segment-level metric breakdowns
├── pipeline_forecast.md # Pipeline coverage and bookings forecast
├── revenue_analysis.md  # ARR, bookings, CAC, LTV/CAC
└── cohort_retention.md  # Signup cohort retention curves
```

The agent reads all context files, receives the user's question, queries the database using Claude's tool use, and delivers a response shaped by the stakeholder's profile and the agent instructions.

## Technical Decisions

- **DuckDB** over SQLite/Postgres — columnar analytics engine that runs in-process, no server needed. Perfect for analytical queries on a ~5MB dataset.
- **Tool use over RAG** — Claude decides when to query (run_sql) and when to compute (run_python), rather than retrieving pre-computed answers. This handles novel questions that don't match existing analysis patterns.
- **Markdown context files** over YAML/JSON config — Easy to read, edit, and version. Non-technical stakeholders can review and suggest changes to their own profiles.
- **Plotly over Matplotlib** — Interactive charts that work natively in Streamlit. Users can hover, zoom, and explore data points.
- **Streaming** — Token-by-token streaming with tool status indicators eliminates the "staring at a spinner" problem.

## Stack

- **Python 3.12** — core language
- **Claude API** (tool use + streaming) — reasoning and natural language generation
- **DuckDB** — local analytical database
- **Streamlit** — interactive UI with streaming support
- **Plotly** — interactive charting
- **Pandas** — data manipulation

## Setup

```bash
# Clone and install
git clone https://github.com/pfelix828/context-agent.git
cd context-agent
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Add your Anthropic API key
echo 'ANTHROPIC_API_KEY=your-key' > .env

# Generate the sample dataset
python src/generate_data.py

# Run the app
streamlit run app/streamlit_app.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Sample Dataset

The included data generator creates a realistic B2B SaaS GTM dataset with:
- **2,000 accounts** across SMB, Mid-Market, and Enterprise segments
- **8,000 leads** with full funnel progression (Lead → MQL → SQL → Opportunity → Closed)
- **45 campaigns** across 6 channels with budget and spend tracking
- **17,000 multi-touch attribution records**
- **100K+ daily product usage records**

## Architecture

```
User Question
     │
     ▼
┌─────────────────┐
│  Context Loader  │ ← reads stakeholder profile, domain.md, agent.md, skills/
└────────┬────────┘
         │ (system prompt)
         ▼
┌─────────────────┐
│   Claude API    │ ← tool use: run_sql, run_python (streaming)
│  (Sonnet 4)     │
└────────┬────────┘
         │ (tool calls)
         ▼
┌─────────────────┐
│    Executor     │ ← DuckDB queries, sandboxed Python + Plotly
└────────┬────────┘
         │ (results + figures)
         ▼
┌─────────────────┐
│ Tailored Answer │ ← shaped by stakeholder profile + agent instructions
│  + Charts       │
└─────────────────┘
```

## Customization

Swap the context files to adapt the agent for any stakeholder or domain:

1. Add a new stakeholder in `context/stakeholders/`
2. Update `context/domain.md` with your business metrics
3. Add or modify skills in `skills/` for domain-specific analysis patterns
4. Point `data_dictionary.md` at your actual schema

## License

MIT
