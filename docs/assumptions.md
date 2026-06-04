# Assumptions

1. **Database**: Using SQLite for MVP. Easily swappable to PostgreSQL via DATABASE_URL.
2. **OCR**: Gemini 2.5 Flash via OpenRouter for vision OCR. PDF text extraction as primary method.
3. **AI Providers**: Using free-tier models (Groq Llama 3.3 70B, OpenRouter Gemini Flash, Mistral Small). Production should use paid tiers.
4. **Authentication**: No auth for MVP. Production needs JWT/OAuth.
5. **Member Database**: Simplified — accepts EMP-prefixed IDs. Production needs full member registry.
6. **Policy Terms**: Single policy (PLUM_OPD_2024). Production supports multiple policies.
7. **YTD Claims**: Not tracked across sessions. Production needs persistent tracking.
8. **Fraud Detection**: Rule-based. Production needs ML-based anomaly detection.
9. **File Storage**: Local filesystem. Production needs S3/GCS.
10. **Concurrency**: Single-threaded adjudication. Production needs async workers.
11. **Amounts**: All amounts in Indian Rupees (₹).
12. **Dates**: Treatment dates validated against policy start date of 2024-01-01.
13. **Doctor Registration**: Format validated but not verified against external registry.
14. **Waiting Period**: Calculated from member_join_date if provided, else assumed satisfied.
