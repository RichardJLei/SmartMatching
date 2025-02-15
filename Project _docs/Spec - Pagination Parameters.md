# API Pagination & Filtering Specification

## 1. Pagination Parameters
| Parameter | Alias      | Type    | Required | Default | Description                          | Validation Rules         |
|-----------|------------|---------|----------|---------|--------------------------------------|--------------------------|
| `start`   | `_start`   | integer | No       | 0       | Offset/starting record index        | ≥ 0                      |
| `end`     | `_end`     | integer | No       | 10      | Ending record index (exclusive)      | > start, ≤ start + 100   |
| `sort`    | `_sort`    | string  | No       | -       | Field to sort by                     | Valid model field name   |
| `order`   | `_order`   | string  | No       | `asc`   | Sort direction                       | `asc` or `desc`          |

**Example Pagination Request:**
GET /blog-post-sql?start=0&_end=10&_sort=created_at&_order=desc


## 2. Filter Parameters
| Parameter Format         | Type   | Required | Description                              | Supported Operators                          |
|--------------------------|--------|----------|------------------------------------------|---------------------------------------------|
| `filter[field]`          | string | Yes*     | Field name to filter on                 | Valid model field name                      |
| `filter[operator]`       | string | Yes*     | Comparison operator                      | See operator table below                    |
| `filter[value]`          | string | Yes*     | Value to compare against                 | Type depends on field                       |

*Required when using filtering

**Supported Operators:**
| Category     | Operators                                  | Valid For Field Types       |
|--------------|--------------------------------------------|-----------------------------|
| Comparisons  | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`      | Numeric, Dates              |
| Text Search  | `contains`, `ncontains`, `startswith`,    | String                      |
|              | `endswith`, `nstartswith`, `nendswith`     |                             |

**Example Filter Request:**
GET /blog-post-sql?
filter[field]=title&
filter[operator]=contains&
filter[value]=API


## 3. Combined Usage
**Request Structure:**
GET /resource?
start=0&
end=10&
sort=field&
order=asc&
filter[field]=status&
filter[operator]=eq&
filter[value]=published


**Response Headers:**
http
X-Total-Count: 157
Content-Range: blog_posts 0-9/157


## 4. Response Format
json
[
{
"id": 1,
"title": "Example Post",
"content": "Lorem ipsum...",
"created_at": "2024-01-01T00:00:00"
},
...
]


## 5. Error Handling
| Status Code | Error Type                | Resolution Steps                          |
|-------------|---------------------------|-------------------------------------------|
| 400         | Invalid Operator          | Check supported operators list            |
| 422         | Invalid Parameter Value   | Verify parameter types and ranges         |
| 500         | Server Error              | Retry with exponential backoff            |

## 6. Best Practices
1. Always handle the `X-Total-Count` header for accurate pagination controls
2. URL-encode special characters in filter values
3. Implement client-side caching for paginated results
4. Validate sortable fields against API documentation
5. Use case-insensitive filters for text fields (`contains` vs `CONTAINS`)

## 7. Rate Limits
| Tier       | Requests/Minute | Parameters               |
|------------|-----------------|--------------------------|
| Standard   | 60              | All endpoints            |
| Filtering  | 30              | Requests with filters    |
| Bulk       | 10              | _end - _start > 50       |