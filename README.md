# Context Agent

An AI-powered data analyst that adapts to the stakeholder asking the question. Instead of generic "chat with your data" responses, Context Agent reads stakeholder profiles, domain knowledge, and analysis skills to deliver tailored, actionable insights.

## The Idea

Data teams answer the same questions differently depending on who's asking. A VP of Marketing wants pipeline impact and budget recommendations. A data engineer wants query performance and schema details. Context Agent makes this adaptation automatic by loading a configurable context layer before every interaction.

## How It Works

```
context/
├── stakeholder.md       # Who is asking — role, priorities, how they use data
├── domain.md            # Business context — metric definitions, KPIs, segments
├── data_dictionary.md   # Schema documentation and gotchas
└── agent.md             # Tone, depth, output format instructions

skills/
├── funnel_analysis.md   # Lead-to-revenue conversion analysis
├── campaign_roi.md      # Campaign performance and attribution
├── segmentation.md      # Segment-level metric breakdowns
└── pipeline_forecast.md # Pipeline coverage and bookings forecast
```

The agent reads all context files, receives the user's question, queries the database using Claude's tool use, and delivers a response shaped by the stakeholder's profile and the agent instructions.

## Stack

- **Python 3.12** — core language
- **Claude API** (tool use) — reasoning and natural language generation
- **DuckDB** — local analytical database
- **Streamlit** — interactive UI
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

## Sample Dataset

The included data generator creates a realistic B2B SaaS GTM dataset with:
- **2,000 accounts** across SMB, Mid-Market, and Enterprise segments
- **8,000 leads** with full funnel progression (Lead → MQL → SQL → Opportunity → Closed)
- **36 campaigns** across 6 channels with budget and spend tracking
- **17,000 multi-touch attribution records**
- **100K+ daily product usage records**

## Customization

Swap the context files to adapt the agent for any stakeholder or domain:

1. Edit `context/stakeholder.md` to define a new persona
2. Update `context/domain.md` with your business metrics
3. Add or modify skills in `skills/` for domain-specific analysis patterns
4. Point `data_dictionary.md` at your actual schema

## Architecture

```
User Question
     │
     ▼
┌─────────────────┐
│  Context Loader  │ ← reads stakeholder.md, domain.md, agent.md, skills/
└────────┬────────┘
         │ (system prompt)
         ▼
┌─────────────────┐
│   Claude API    │ ← tool use: run_sql, run_python
│  (Sonnet 4)     │
└────────┬────────┘
         │ (tool calls)
         ▼
┌─────────────────┐
│    Executor     │ ← DuckDB queries, Python execution
└────────┬────────┘
         │ (results)
         ▼
┌─────────────────┐
│ Tailored Answer │ ← shaped by stakeholder profile + agent instructions
└─────────────────┘
```

## License

MIT
