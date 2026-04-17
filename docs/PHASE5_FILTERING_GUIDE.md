# Phase 5: Advanced Filtering & Drill-Down - User Guide

## Overview

Phase 5 transforms the analytics dashboard from view-only to interactive analytics exploration with advanced filtering, sorting, pagination, and real-time drill-down capabilities.

---

## Getting Started

### Accessing the Dashboard

Navigate to the Analytics Dashboard at `/dashboard`. You'll see:

1. **Filter Panel** - Collapsible filter builder at the top
2. **Filter Badges** - Display of currently active filters
3. **Analytics Tabs** - 8 tabs for different analytics views
4. **Dashboard Content** - Data visualizations responding to filters

### Basic Workflow

1. **Click "Filters"** to expand the filter panel
2. **Select your filters** using the various filter controls
3. **Click "Apply Filters"** to execute the query
4. **View results** in the dashboard below
5. **Click column headers** to sort (in tables)
6. **Use pagination** to navigate large result sets

---

## Filter Dimensions

### Time Filtering

#### Preset Time Ranges
- **1H**: Last 1 hour of data
- **24H**: Last 24 hours (default)
- **7D**: Last 7 days (rolling)
- **30D**: Last 30 days (rolling)

#### Custom Date Range
- Click "Custom Date Range" to select specific dates
- Choose start and end dates using the date pickers
- Format: YYYY-MM-DD (e.g., 2026-04-15)
- Custom ranges automatically override time presets

### Dimension Filters

#### Users
- Multi-select filter for specific users
- Filter by user ID or user name
- Leave empty to show all users
- Useful for: User-specific analysis, individual account monitoring

#### Tools
- Multi-select filter for AI tools/models used
- Filter by tool name or identifier
- Leave empty to show all tools
- Useful for: Tool performance comparison, tool-specific metrics

#### Complexity
- Select query complexity levels:
  - SIMPLE - Basic queries
  - MODERATE - Standard queries
  - COMPLEX - Complex multi-step queries
  - VERY_COMPLEX - Advanced reasoning queries
- Multiple complexities can be selected
- Leave empty to show all complexity levels

### Status Filtering

#### Success Status
- **All** - Both successful and failed queries (default)
- **Successful** - Only successful queries
- **Failed** - Only failed queries
- Useful for: Error analysis, reliability tracking

### Range Filters

#### Cost Range
- Filter queries by cost (in dollars)
- Adjust minimum and maximum using:
  - Slider controls (drag to set range)
  - Number inputs (type exact values)
  - Reset button to clear the filter
- Useful for: Cost optimization, high-cost query identification

#### Latency Range
- Filter queries by response time (in milliseconds)
- Adjust minimum and maximum latency
- Useful for: Performance analysis, slow query identification

### Sorting

#### Sort By
- **Cost** - Sort by query/user cost
- **Latency** - Sort by response time
- **Count** - Sort by frequency/usage count
- **Effectiveness** - Sort by tool effectiveness

#### Sort Order
- **Descending** (↓) - Highest to lowest (default)
- **Ascending** (↑) - Lowest to highest

---

## Using Filter Controls

### MultiSelect Dropdown

Click any multi-select field to open the dropdown:

1. **Select All** - Checks all options
2. **Deselect All** - Unchecks all options (when all selected)
3. **Individual Checkboxes** - Click to toggle each item
4. **Clear Button** - Click the ✕ to clear the entire filter

### Range Sliders

Adjust min and max using:

1. **Visual Sliders** - Drag to set values
2. **Number Inputs** - Type exact values
3. **Reset Button** - Restore default range

Example: Cost Range with values $50-$500
- Min field: type or drag to set minimum
- Max field: type or drag to set maximum
- Visual feedback shows current range

### Date Range Picker

Select custom date range:

1. **Start Date** - Click field to open calendar
2. **End Date** - Click field to open calendar
3. **Formatted Output** - Shows selected date range
4. **Clear** - Reset to time preset

---

## Filter Behavior

### Active Filters
When filters are active (non-default):
- Dashboard shows filter badges below the filter panel
- Badge count updates in real-time
- Each badge displays the filter details
- Click ✕ in any badge to clear all filters

### Filter Application
- Filters apply immediately when changed
- Some controls have "Apply Filters" button to batch updates
- API calls are debounced to prevent excessive requests
- Loading indicators show data is refreshing

### Filter Combinations
- Multiple filters work together (AND logic)
- Example: Users=[user1, user2] + Complexity=[SIMPLE]
  - Shows only SIMPLE queries from user1 or user2
- All filters must match for a result to be included

### URL Persistence
- Current filter state is saved to URL query parameters
- Share filter URLs with colleagues
- Bookmark filtered views for quick access
- Example: `/dashboard?users=user1,user2&timePreset=7d`

---

## Dashboard Features

### Tabs

Each tab shows different analytics:

1. **Overview** - Key metrics and top visualizations
2. **Queries** - Query complexity, patterns, and trends
3. **Users** - User spending and usage metrics
4. **Tools** - Tool effectiveness and usage statistics
5. **Costs** - Daily cost trends and breakdowns
6. **Performance** - Latency percentiles and throughput
7. **Streaming** - Real-time session analytics
8. **Reports** - Generate and download reports

### Tables

Sortable, paginated data tables:

- **Click Column Headers** - Sort ascending/descending
- **Visual Indicator** - Arrow (▼) shows sort direction
- **Pagination Controls** - Previous/Next/Page indicator
- **Result Count** - Shows total and current page

### Charts

Interactive visualizations:

- **Pie Charts** - Distribution analysis (e.g., complexity)
- **Bar Charts** - Comparisons (e.g., tool effectiveness)
- **Area Charts** - Trends over time (e.g., daily costs)
- **Hover Tooltips** - Detailed values on mouse over
- **Responsive Design** - Adapts to screen size

---

## Common Use Cases

### 1. Identify High-Cost Queries

**Steps:**
1. Open Filter Panel
2. Set Cost Range: Min=$100, Max=$10000
3. Sort by: Cost (Descending)
4. View top expensive queries

**What You'll See:**
- Most expensive queries listed first
- Query details including user and complexity
- Opportunities for cost optimization

### 2. Analyze User Spending

**Steps:**
1. Click "Users" tab
2. Sort by: Cost (Descending)
3. Optional: Apply date range for specific period
4. Paginate through users

**What You'll See:**
- Users ranked by spending
- Individual user costs
- Spending trends over time

### 3. Find Slow Queries

**Steps:**
1. Set Latency Range: Min=2000ms (2 seconds)
2. Sort by: Latency (Descending)
3. View problematic queries

**What You'll See:**
- Slow queries at the top
- Response time details
- User and tool information

### 4. Complex Query Performance

**Steps:**
1. Set Complexity: Select only "COMPLEX", "VERY_COMPLEX"
2. Set Time Range: Last 7 days
3. View "Performance" tab
4. Analyze latency and success rate

**What You'll See:**
- How complex queries perform
- Success/failure rates
- Performance patterns

### 5. Tool Comparison

**Steps:**
1. Click "Tools" tab
2. Compare tool effectiveness
3. Filter by date range or user
4. Sort by effectiveness

**What You'll See:**
- Tool rankings by effectiveness
- Usage frequency
- Success rates
- Average response time

---

## Filter Best Practices

### Do's ✓

- ✓ Use presets first (1h, 24h, 7d, 30d)
- ✓ Combine multiple filters for specific analysis
- ✓ Bookmark filtered URLs for recurring analysis
- ✓ Check filter badges to confirm active filters
- ✓ Use pagination for large result sets
- ✓ Sort by most relevant column

### Don'ts ✗

- ✗ Don't leave all complexity levels unselected (use presets)
- ✗ Don't combine conflicting filters (e.g., Success + Failed)
- ✗ Don't forget to clear old filters before new analysis
- ✗ Don't apply extreme ranges without checking results
- ✗ Don't miss the "Apply Filters" button in filter panel

---

## Tips & Tricks

### Quick Filters
- Double-click category headers to auto-filter
- Use keyboard shortcuts for faster navigation
- Bookmark common filter combinations

### Performance
- Filters apply immediately (no "Apply" button needed for most)
- Use pagination for better performance with large datasets
- Time presets load faster than custom date ranges

### Sharing
- Copy dashboard URL to share filtered views
- Filters persist in URLs for collaboration
- Export results via Reports tab

### Data Refresh
- Dashboard data updates in real-time as it changes
- Filter badge shows "Loading" during updates
- API calls are optimized to prevent slowness

---

## Troubleshooting

### No Results Found
- **Cause**: Filters too restrictive
- **Solution**: Clear some filters, use "Reset All"
- **Check**: Verify time range includes data

### Slow Dashboard Performance
- **Cause**: Too many results or complex filters
- **Solution**: Add more specific filters, use pagination
- **Check**: Try shorter time range (24h instead of 30d)

### URL Not Working
- **Cause**: Bookmark from different session
- **Solution**: Reapply filters manually
- **Note**: Some data may have changed since bookmark

### Filter Badge Not Showing
- **Cause**: Filter values are defaults
- **Solution**: Change filter to non-default value
- **Note**: Badges only show active (non-default) filters

---

## API Reference for Developers

### Filtered Query Endpoint

```
GET /api/v1/analytics/queries/filtered?
  hours=24
  &complexities=SIMPLE,MODERATE
  &success_status=success
  &cost_min=10
  &cost_max=100
  &latency_min=50
  &latency_max=5000
  &sort_by=cost
  &sort_order=desc
  &limit=50
  &offset=0
```

Response:
```json
{
  "queries": [
    {
      "query": "q1",
      "complexity": "SIMPLE",
      "success": true,
      "cost": 1.5,
      "duration_ms": 100,
      "timestamp": "2026-04-15T10:30:00"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0,
  "filters": { ... }
}
```

### Filtered User Costs Endpoint

```
GET /api/v1/analytics/costs/by-user/filtered?
  days=30
  &cost_min=50
  &cost_max=500
  &sort_by=cost
  &sort_order=desc
  &limit=50
  &offset=0
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Open filter panel |
| `Escape` | Close filter panel |
| `Ctrl+R` | Reset all filters |
| `Tab` | Navigate filter controls |
| `Enter` | Apply filters |

---

## Version History

**Phase 5 - Week 1-3**
- Initial release with full filtering, sorting, pagination
- FilterContext and hooks for state management
- URL persistence for bookmarkable views
- Performance optimization with debouncing

---

## Support

For issues or feature requests:
1. Check this guide's troubleshooting section
2. Review dashboard error messages
3. Check browser console for API errors
4. Contact the analytics team

---

**Last Updated**: April 16, 2026
**Maintainer**: AI Control Plane Team
