# KQ Bookings Quality Report - REST API Documentation

## Base URL
```
http://localhost:8000/api/v1/
```

## Authentication
- Session Authentication (for web interface)
- Token Authentication (for API clients)

## Endpoints

### 1. Bookings CRUD Operations

#### List Bookings
```http
GET /api/v1/bookings/
```
**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 50)
- `booking_channel` - Filter by channel (web, mobile, office, agency, ndc)
- `office_id` - Filter by office ID
- `agency_iata` - Filter by agency IATA code
- `staff_id` - Filter by staff ID
- `start_date` - Filter from date (YYYY-MM-DD)
- `end_date` - Filter to date (YYYY-MM-DD)
- `search` - Search in PNR, phone, email, FF number
- `ordering` - Sort by field (created_at, pnr, -created_at)

#### Get Single Booking
```http
GET /api/v1/bookings/{id}/
```

#### Create Booking
```http
POST /api/v1/bookings/
Content-Type: application/json

{
    "pnr": "ABC123",
    "phone": "123456789",
    "email": "user@example.com",
    "ff_number": "FF123456",
    "meal_selection": "Vegetarian",
    "seat": "12A",
    "booking_channel": "web",
    "office_id": "NBO001",
    "agency_iata": "12345678",
    "staff_id": "STAFF001"
}
```

#### Update Booking
```http
PUT /api/v1/bookings/{id}/
PATCH /api/v1/bookings/{id}/
```

#### Delete Booking
```http
DELETE /api/v1/bookings/{id}/
```

### 2. Analytics Endpoints

#### Quality Statistics
```http
GET /api/v1/bookings/quality_stats/
```
**Response:**
```json
{
    "total_pnrs": 1500,
    "with_contacts": 1200,
    "without_contacts": 300,
    "avg_quality": 75.5,
    "contact_percentage": 80.0
}
```

#### Channel Performance
```http
GET /api/v1/bookings/channel_stats/
```
**Response:**
```json
[
    {
        "booking_channel": "web",
        "total": 800,
        "avg_quality": 78.5,
        "percentage": 53.3
    },
    {
        "booking_channel": "mobile",
        "total": 400,
        "avg_quality": 72.1,
        "percentage": 26.7
    }
]
```

#### Office Performance
```http
GET /api/v1/bookings/office_stats/
```

#### Quality Trends
```http
GET /api/v1/bookings/quality_trends/?days=30
```
**Response:**
```json
[
    {
        "date": "2024-01-01",
        "quality": 75.5,
        "count": 45
    },
    {
        "date": "2024-01-02",
        "quality": 78.2,
        "count": 52
    }
]
```

### 3. Filtered Data Endpoints

#### Bookings Without Contacts
```http
GET /api/v1/bookings/no_contacts/
```

#### Low Quality Bookings (<60%)
```http
GET /api/v1/bookings/low_quality/
```

#### High Quality Bookings (≥80%)
```http
GET /api/v1/bookings/high_quality/
```

### 4. Bulk Operations

#### Bulk Upload from Excel
```http
POST /api/v1/bookings/bulk_upload/
Content-Type: multipart/form-data

file: [Excel file]
```
**Response:**
```json
{
    "message": "Upload successful",
    "created": 150,
    "updated": 50,
    "total": 200
}
```

## Example Usage

### Python (requests)
```python
import requests

# Get quality statistics
response = requests.get('http://localhost:8000/api/v1/bookings/quality_stats/')
stats = response.json()
print(f"Average Quality: {stats['avg_quality']}%")

# Create a booking
booking_data = {
    "pnr": "KQ123456",
    "phone": "+254700123456",
    "email": "passenger@example.com",
    "booking_channel": "web"
}
response = requests.post('http://localhost:8000/api/v1/bookings/', json=booking_data)
```

### JavaScript (fetch)
```javascript
// Get channel statistics
fetch('http://localhost:8000/api/v1/bookings/channel_stats/')
    .then(response => response.json())
    .then(data => console.log(data));

// Filter bookings by date range
const params = new URLSearchParams({
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    booking_channel: 'web'
});
fetch(`http://localhost:8000/api/v1/bookings/?${params}`)
    .then(response => response.json())
    .then(data => console.log(data));
```

### cURL
```bash
# Get quality trends for last 7 days
curl "http://localhost:8000/api/v1/bookings/quality_trends/?days=7"

# Create a new booking
curl -X POST "http://localhost:8000/api/v1/bookings/" \
     -H "Content-Type: application/json" \
     -d '{"pnr": "TEST123", "phone": "123456", "booking_channel": "web"}'
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