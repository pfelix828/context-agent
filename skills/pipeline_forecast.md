# Skill: Pipeline Forecast

## Description
Assesses current pipeline coverage against quarterly targets and forecasts likely bookings based on historical win rates and stage distribution.

## When to Use
- "Are we going to hit our number?"
- "What does pipeline coverage look like?"
- "How much pipeline do we need to generate?"
- Any question about forecast or pipeline health

## Analysis Steps
1. Sum open pipeline by stage
2. Apply historical stage-specific win rates to estimate weighted pipeline
3. Compare weighted pipeline to quarterly target
4. Calculate pipeline coverage ratio (weighted pipeline / target)
5. Estimate gap: target - weighted pipeline
6. Calculate required lead generation to fill the gap (using historical conversion rates)

## Output Format
- Pipeline summary table by stage (count, value, historical win rate, weighted value)
- Coverage ratio vs target
- Gap analysis with required lead volume to close the gap
- Risk assessment (on track / at risk / behind)
