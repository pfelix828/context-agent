# Skill: Revenue Analysis

## Description
Analyzes revenue composition, bookings trends, unit economics (CAC, LTV/CAC), and ARR breakdown by segment. Designed for executive-level financial reviews.

## When to Use
- "What's our ARR?"
- "How are bookings trending?"
- "What's our CAC by segment?"
- "Show me unit economics"
- "Revenue breakdown by segment"
- Any question about ARR, bookings, LTV, or CAC

## Analysis Steps
1. Calculate total ARR from active customers (dim_accounts where is_customer = true)
2. Break down ARR by segment (SMB, Mid-Market, Enterprise)
3. Calculate bookings from closed-won opportunities in the requested period
4. Compare bookings to prior period
5. Calculate CAC: total campaign spend / new customers acquired
6. Estimate LTV using ARR and segment-level retention assumptions
7. Compute LTV/CAC ratio by segment
8. Identify the highest-growth and most efficient segments

## Output Format
- Headline ARR figure with growth context
- ARR breakdown table by segment (ARR, % of total, customer count, avg deal size)
- Bookings trend (current vs prior period)
- Unit economics summary (CAC, estimated LTV, LTV/CAC by segment)
- Key takeaway and recommendation
