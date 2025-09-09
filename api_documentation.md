# KQ Bookings Quality Report - API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Available Endpoints

### 1. Channel Groupings
```http
GET /api/channel-groupings/
```
**Description:** Get channel groupings for filtering (Direct vs Indirect channels)

**Response:**
```json
{
    "groupings": [
        {
            "id": "direct",
            "label": "Direct Channels",
            "channels": [
                {"id": "website", "label": "Website"},
                {"id": "mobile", "label": "Mobile"},
                {"id": "ato", "label": "ATO"},
                {"id": "cto", "label": "CTO"},
                {"id": "cec", "label": "Contact Center (CEC)"},
                {"id": "kq_gsa", "label": "KQ GSA"}
            ]
        },
        {
            "id": "indirect",
            "label": "Indirect Channels",
            "channels": [
                {"id": "travel_agents", "label": "Travel Agents"},
                {"id": "ndc", "label": "NDC"},
                {"id": "msafiri_connect", "label": "Msafiri Connect"}
            ]
        }
    ]
}
```

### 2. Offices by Channels
```http
GET /api/offices-by-channels/?channels=website&channels=mobile
```
**Description:** Get available offices for selected channels

**Query Parameters:**
- `channels` - Array of channel IDs

**Response:**
```json
{
    "offices": [
        {"office_id": "WEB001", "name": "Website Office"},
        {"office_id": "MOB001", "name": "Mobile App Office"}
    ]
}
```

### 3. Channel & Office Statistics
```http
GET /api/channel-office-stats/?channels=website&offices=WEB001
```
**Description:** Get booking statistics for selected channels and offices

**Query Parameters:**
- `channels` - Array of channel IDs (optional)
- `offices` - Array of office IDs (optional)

**Response:**
```json
{
    "total_bookings": 1500,
    "avg_quality": 75.5,
    "with_contacts": 1200
}
```

### 4. Quality Trends (from views.py)
```http
GET /api/trends/?days=30
```
**Description:** Get quality trends over time

**Query Parameters:**
- `days` - Number of days (default: 30)
- All filter parameters from main view (channels, offices, dates)

**Response:**
```json
{
    "trends": [
        {
            "date": "2024-01-01",
            "quality": 75.5,
            "count": 45
        }
    ]
}
```

## Example Usage

### Python (requests)
```python
import requests

# Get channel groupings
response = requests.get('http://localhost:8000/api/channel-groupings/')
groupings = response.json()
print(f"Available channels: {groupings['groupings']}")

# Get offices for specific channels
params = {'channels': ['website', 'mobile']}
response = requests.get('http://localhost:8000/api/offices-by-channels/', params=params)
offices = response.json()
print(f"Available offices: {offices['offices']}")

# Get statistics
params = {'channels': ['website'], 'offices': ['WEB001']}
response = requests.get('http://localhost:8000/api/channel-office-stats/', params=params)
stats = response.json()
print(f"Average Quality: {stats['avg_quality']}%")
```

### JavaScript (fetch)
```javascript
// Get channel groupings
fetch('http://localhost:8000/api/channel-groupings/')
    .then(response => response.json())
    .then(data => console.log(data.groupings));

// Get offices for selected channels
const params = new URLSearchParams();
params.append('channels', 'website');
params.append('channels', 'mobile');
fetch(`http://localhost:8000/api/offices-by-channels/?${params}`)
    .then(response => response.json())
    .then(data => console.log(data.offices));

// Get quality trends
fetch('http://localhost:8000/api/trends/?days=7')
    .then(response => response.json())
    .then(data => console.log(data.trends));
```

### cURL
```bash
# Get channel groupings
curl "http://localhost:8000/api/channel-groupings/"

# Get offices for website channel
curl "http://localhost:8000/api/offices-by-channels/?channels=website"

# Get statistics with filters
curl "http://localhost:8000/api/channel-office-stats/?channels=website&offices=WEB001"
```

## Error Responses
```json
{
    "error": "Error message",
    "details": "Detailed error information"
}
```

## Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Server Error