"""Generate test claims for development."""

import json
import random
import os

DOCTORS = [
    {"name": "Dr. Sharma", "reg": "KA/45678/2015"},
    {"name": "Dr. Patel", "reg": "MH/23456/2018"},
    {"name": "Dr. Gupta", "reg": "DL/34567/2016"},
    {"name": "Dr. Mehta", "reg": "GJ/56789/2014"},
    {"name": "Dr. Rao", "reg": "AP/67890/2017"},
]

DIAGNOSES = [
    "Viral fever", "Upper respiratory tract infection", "Gastroenteritis",
    "Migraine", "Allergic rhinitis", "Lower back pain", "Chronic joint pain",
]

MEDICINES = [
    "Paracetamol 650mg", "Amoxicillin 500mg", "Azithromycin 500mg",
    "Omeprazole 20mg", "Cetirizine 10mg", "Ibuprofen 400mg",
]


def generate_mock_claims(count=20):
    claims = []
    for i in range(count):
        doctor = random.choice(DOCTORS)
        diagnosis = random.choice(DIAGNOSES)
        meds = random.sample(MEDICINES, k=random.randint(1, 3))
        consultation = random.choice([500, 800, 1000, 1500, 2000])
        med_cost = random.randint(200, 3000)

        claims.append({
            "member_id": f"EMP{100+i:03d}",
            "member_name": f"Test Patient {i+1}",
            "treatment_date": f"2024-{random.randint(9,11):02d}-{random.randint(1,28):02d}",
            "claim_amount": consultation + med_cost,
            "documents": {
                "prescription": {
                    "doctor_name": doctor["name"],
                    "doctor_reg": doctor["reg"],
                    "diagnosis": diagnosis,
                    "medicines_prescribed": meds,
                },
                "bill": {
                    "consultation_fee": consultation,
                    "medicines": med_cost,
                },
            },
        })

    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "claims", "mock_claims.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(claims, f, indent=2)
    print(f"Generated {count} mock claims → {output_path}")
    return claims


if __name__ == "__main__":
    generate_mock_claims()
