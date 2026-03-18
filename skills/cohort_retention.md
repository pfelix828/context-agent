# Skill: Cohort Retention Analysis

## Description
Analyzes customer cohorts by signup month and tracks product usage retention curves over time. Identifies engagement trends and highlights cohorts with strong or weak retention.

## When to Use
- "Show me retention by cohort"
- "How is user engagement trending?"
- "Which cohorts have the best retention?"
- "What does our retention curve look like?"
- Any question about cohort behavior, engagement trends, or usage over time

## Analysis Steps
1. Define cohorts by account created_at month (from dim_accounts where is_customer = true)
2. For each cohort, track monthly product usage (fct_product_usage) relative to their start month
3. Calculate retention rate: % of accounts in each cohort that are active in month N vs month 0
4. Define "active" as having any product usage record in the month
5. Build a retention matrix (cohort × month offset)
6. Calculate average retention curve across all cohorts
7. Identify best and worst performing cohorts
8. Look for trends — are newer cohorts retaining better or worse?

## Output Format
- Retention curve chart (line chart with month offset on x-axis, retention % on y-axis)
- Cohort retention heatmap or table (cohort × month)
- Highlight best/worst cohorts with context
- Trend assessment: is retention improving over time?
- Recommendation
