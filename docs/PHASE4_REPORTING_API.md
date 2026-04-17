# Phase 4: Reporting API Documentation

## Overview

The Reporting API provides endpoints for generating and exporting analytics reports in multiple formats (JSON, CSV). Reports can be generated for different time periods: daily, weekly, or monthly.

---

## Report Types

### Daily Report
Includes all metrics for a single day:
- Query analytics (complexity distribution, success rates)
- User metrics (query counts, spending)
- Tool effectiveness
- Cost breakdown
- Performance latency data

**Time Range:** Current day (or specified date)

### Weekly Report
Rolling 7-day analysis with trends and top performers:
- All daily metrics aggregated
- Trend analysis
- Top 10 users by spending
- Top 10 tools by effectiveness
- Weekly cost trends

**Time Range:** Last 7 days (from specified end date)

### Monthly Report
Comprehensive 30-day analysis with advanced metrics:
- All weekly metrics aggregated
- Active user count
- Historical trends
- Top users and tools
- Cost forecasts

**Time Range:** Last 30 days (from specified end date)

---

## API Endpoints

### Generate Daily Report

```
GET /api/v1/reports/daily?date=YYYY-MM-DD&format=csv|json
```

**Parameters:**
- `date` (optional): Report date in YYYY-MM-DD format. Defaults to today.
- `format` (optional): Export format (csv or json). Defaults to json.

**Response:**
```json
{
  "report": "report content as string",
  "filename": "report_daily_20260415.csv",
  "format": "csv"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/reports/daily?date=2026-04-15&format=csv"
```

---

### Generate Weekly Report

```
GET /api/v1/reports/weekly?end_date=YYYY-MM-DD&format=csv|json
```

**Parameters:**
- `end_date` (optional): End date for the 7-day period in YYYY-MM-DD format. Defaults to today.
- `format` (optional): Export format (csv or json). Defaults to json.

**Response:**
```json
{
  "report": "report content as string",
  "filename": "report_weekly_20260415.csv",
  "format": "csv"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/reports/weekly?end_date=2026-04-15&format=json"
```

---

### Generate Monthly Report

```
GET /api/v1/reports/monthly?end_date=YYYY-MM-DD&format=csv|json
```

**Parameters:**
- `end_date` (optional): End date for the 30-day period in YYYY-MM-DD format. Defaults to today.
- `format` (optional): Export format (csv or json). Defaults to json.

**Response:**
```json
{
  "report": "report content as string",
  "filename": "report_monthly_20260415.csv",
  "format": "csv"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/reports/monthly?end_date=2026-04-15&format=csv"
```

---

## Export Formats

### JSON Export

Clean, structured JSON format suitable for programmatic processing.

**Structure:**
```json
{
  "report_type": "daily",
  "date": "2026-04-15",
  "generated_at": "2026-04-15T10:30:00",
  "summary": {
    "total_queries": 1000,
    "success_rate": 0.95,
    "total_cost": 150.50,
    "avg_latency_ms": 245
  },
  "metrics": {
    "query_analytics": {...},
    "user_analytics": {...},
    "tool_analytics": {...},
    "cost_analytics": {...}
  }
}
```

### CSV Export

Spreadsheet-friendly format with sections for different metrics.

**Sections:**
1. **Header** - Report type, date/period, generation timestamp
2. **Summary** - Key metrics overview
3. **Query Analytics** - Complexity distribution and patterns
4. **User Analytics** - Per-user metrics and spending
5. **Top Users** - Top 10 users by cost
6. **Top Tools** - Top 10 tools by effectiveness

---

## Usage Examples

### Download Daily Report as CSV

```bash
curl "http://localhost:8000/api/v1/reports/daily?format=csv" \
  -o report_daily.csv
```

### Get Weekly Report as JSON

```bash
curl "http://localhost:8000/api/v1/reports/weekly?format=json" | jq '.'
```

### Generate Monthly Report for Specific Date

```bash
curl "http://localhost:8000/api/v1/reports/monthly?end_date=2026-03-31&format=csv" \
  -o report_march.csv
```

---

## Frontend Integration

The dashboard includes a Report Generator component accessible via the "Reports" tab.

**Features:**
- Select report type (daily, weekly, monthly)
- Choose export format (CSV, JSON)
- Automatic download with proper filename
- Success/error notifications

**Component Location:** `frontend/src/components/ReportGenerator.tsx`

---

## Data Aggregation

Reports aggregate data from six analytics services:

1. **QueryAnalytics** - Query complexity, success rates, latency
2. **UserAnalytics** - Per-user metrics and spending trends
3. **ToolAnalytics** - Tool effectiveness and usage statistics
4. **CostAnalytics** - Daily/weekly/monthly cost breakdowns
5. **PerformanceAnalytics** - Latency percentiles and throughput
6. **StreamingAnalytics** - Session completion and event patterns

---

## Performance

Typical response times:
- Daily report generation: <500ms
- Weekly report generation: <1s
- Monthly report generation: <2s

CSV export adds minimal overhead (typically 100-300ms for formatting).

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Report generated successfully
- `400 Bad Request` - Invalid parameters (bad date format)
- `500 Internal Server Error` - Backend generation error

Error responses include a descriptive message.

---

## Report Retention

Reports are generated on-demand from current analytics data. There is no storage or archival mechanism - to preserve reports, download them as files.

---

## Scheduling & Automation

To automate report generation:

1. **Daily cron job:**
   ```bash
   0 9 * * * curl "http://localhost:8000/api/v1/reports/daily?format=csv" -o reports/daily_$(date +\%Y\%m\%d).csv
   ```

2. **Weekly job:**
   ```bash
   0 9 * * 1 curl "http://localhost:8000/api/v1/reports/weekly?format=csv" -o reports/weekly_$(date +\%Y\%m\%d).csv
   ```

---

## Limitations

- Reports contain data from the past 7/30 days only (based on analytics service retention)
- Real-time reports show data as of generation time (not live-updating)
- Date parameters must be in YYYY-MM-DD format
- CSV export flattens nested structures (suitable for Excel/Sheets)
