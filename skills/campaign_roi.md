# Skill: Campaign ROI Analysis

## Description
Evaluates campaign performance by comparing spend against pipeline generated and revenue closed. Uses first-touch and multi-touch attribution to assign credit.

## When to Use
- "Which campaigns are performing best?"
- "What's the ROI on our paid search spend?"
- "Where should we allocate budget next quarter?"
- Any question about campaign effectiveness or spend efficiency

## Analysis Steps
1. Join campaigns to leads via bridge_campaign_leads
2. Trace leads through to opportunities and closed-won deals
3. Calculate pipeline generated and revenue attributed per campaign
4. Compute ROI: (attributed revenue - spend) / spend
5. Compute CAC: spend / customers acquired
6. Rank campaigns by ROI and pipeline contribution
7. Compare first-touch vs multi-touch attribution if relevant

## Output Format
- Campaign performance table (campaign, channel, spend, pipeline, revenue, ROI)
- Top and bottom performers highlighted
- Budget reallocation recommendation
