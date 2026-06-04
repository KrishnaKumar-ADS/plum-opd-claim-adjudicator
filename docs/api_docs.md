# API Documentation

## Base URL
`http://localhost:8000`

## Endpoints

### Claims
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/claims` | Submit claim with file upload (multipart form) |
| `POST` | `/api/claims/json` | Submit claim via JSON body |
| `GET` | `/api/claims` | List all claims (pagination: `?skip=0&limit=50`) |
| `GET` | `/api/claims/{claim_id}` | Get claim details + decision |

### Decisions
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/decisions` | List decisions (`?decision_type=APPROVED`) |
| `GET` | `/api/decisions/{claim_id}` | Get decision for a claim |

### Appeals
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/appeals` | Create appeal `{claim_id, reason, supporting_info}` |
| `GET` | `/api/appeals` | List all appeals |
| `GET` | `/api/appeals/{appeal_id}` | Get appeal details |
| `PUT` | `/api/appeals/{appeal_id}/review` | Review appeal `{reviewer_notes, new_decision}` |

### Admin
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/stats` | Dashboard statistics |
| `GET` | `/api/admin/review-queue` | Manual review queue |
| `PUT` | `/api/admin/review/{claim_id}` | Submit manual review |

### Evaluation
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/evaluation/run` | Run test case evaluation |

### Health
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API info |
| `GET` | `/health` | Health check |

## Example: Submit Claim via JSON

```bash
curl -X POST http://localhost:8000/api/claims/json \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "EMP001",
    "member_name": "Rajesh Kumar",
    "treatment_date": "2024-11-01",
    "claim_amount": 1500,
    "documents": {
      "prescription": {
        "doctor_name": "Dr. Sharma",
        "doctor_reg": "KA/45678/2015",
        "diagnosis": "Viral fever",
        "medicines_prescribed": ["Paracetamol 650mg"]
      },
      "bill": {
        "consultation_fee": 1000,
        "diagnostic_tests": 500
      }
    }
  }'
```

## Interactive Docs
Visit `http://localhost:8000/docs` for Swagger UI.
