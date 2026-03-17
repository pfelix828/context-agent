# Data Dictionary

## Tables

### dim_accounts
| Column | Type | Description |
|--------|------|-------------|
| account_id | varchar | Unique account identifier |
| company_name | varchar | Company name |
| industry | varchar | Industry vertical |
| employee_count | int | Number of employees |
| segment | varchar | SMB / Mid-Market / Enterprise (derived from employee_count) |
| region | varchar | Geographic region |
| created_at | date | Account creation date |
| is_customer | boolean | Whether account has an active subscription |
| arr | decimal | Current ARR (0 if not a customer) |

### dim_leads
| Column | Type | Description |
|--------|------|-------------|
| lead_id | varchar | Unique lead identifier |
| account_id | varchar | FK to dim_accounts |
| email | varchar | Contact email |
| title | varchar | Job title |
| lead_source | varchar | Original source channel |
| lead_score | int | Behavioral + firmographic score (0-100) |
| status | varchar | new / mql / sql / opportunity / closed_won / closed_lost / disqualified |
| created_at | date | Lead creation date |
| mql_at | date | Date lead became MQL (null if not MQL) |
| sql_at | date | Date lead became SQL (null if not SQL) |

### fct_opportunities
| Column | Type | Description |
|--------|------|-------------|
| opportunity_id | varchar | Unique opportunity identifier |
| account_id | varchar | FK to dim_accounts |
| lead_id | varchar | FK to dim_leads (primary lead) |
| owner_id | varchar | Sales rep ID |
| stage | varchar | Stage 1-5, Closed Won, Closed Lost |
| amount | decimal | Deal size (ARR) |
| created_at | date | Opportunity creation date |
| close_date | date | Expected or actual close date |
| closed_at | date | Actual close date (null if open) |
| is_won | boolean | Whether deal was won |

### fct_campaigns
| Column | Type | Description |
|--------|------|-------------|
| campaign_id | varchar | Unique campaign identifier |
| campaign_name | varchar | Campaign name |
| channel | varchar | paid_search / organic / events / outbound / partner / plg |
| start_date | date | Campaign start date |
| end_date | date | Campaign end date (null if ongoing) |
| budget | decimal | Allocated budget |
| spend | decimal | Actual spend to date |

### bridge_campaign_leads
| Column | Type | Description |
|--------|------|-------------|
| campaign_id | varchar | FK to fct_campaigns |
| lead_id | varchar | FK to dim_leads |
| touch_date | date | Date of the touchpoint |
| is_first_touch | boolean | Whether this was the lead's first campaign interaction |
| touch_order | int | Sequence number of this touch (1 = first) |

### fct_product_usage
| Column | Type | Description |
|--------|------|-------------|
| account_id | varchar | FK to dim_accounts |
| usage_date | date | Date of activity |
| dau | int | Daily active users |
| features_used | int | Distinct features used that day |
| api_calls | int | API calls made |
| storage_mb | decimal | Storage consumed in MB |
