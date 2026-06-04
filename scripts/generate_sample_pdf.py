import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def draw_header(c, title, clinic_name, address, reg_no=None, gst_no=None):
    # Professional Header Banner
    c.setFillColorRGB(0.08, 0.18, 0.36)  # Deep Navy Blue
    c.rect(50, 720, 512, 50, fill=True, stroke=False)
    
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(65, 738, clinic_name)
    
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 10)
    c.drawRightString(550, 700, f"Address: {address}")
    if reg_no:
        c.drawString(50, 700, f"Doctor Reg No: {reg_no}")
    if gst_no:
        c.drawString(50, 700, f"GSTIN: {gst_no}")
        
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(1)
    c.line(50, 690, 550, 690)
    
    # Title of document (Prescription vs Invoice)
    c.setFillColorRGB(0.08, 0.18, 0.36)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 665, title)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.line(50, 655, 550, 655)

def draw_patient_info(c, patient_name, age_sex, date, extra_info=None):
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 635, "PATIENT DETAILS")
    c.setFont("Helvetica", 10)
    c.drawString(50, 620, f"Name: {patient_name}")
    c.drawString(50, 605, f"Age / Sex: {age_sex}")
    c.drawRightString(550, 620, f"Date: {date}")
    if extra_info:
        c.drawString(50, 590, extra_info)
    c.line(50, 580, 550, 580)

def draw_footer(c, doctor_name, hospital_name=None):
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(50, 150, 550, 150)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 130, "* This is an AI-generated mock clinical document for testing OPD claims.")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(550, 110, doctor_name)
    c.setFont("Helvetica", 9)
    c.drawRightString(550, 95, "Authorized Signature & Stamp")
    
    # Draw a simulated digital signature box
    c.setStrokeColorRGB(0.08, 0.18, 0.36)
    c.rect(430, 40, 120, 45, fill=False)
    c.setFillColorRGB(0.08, 0.18, 0.36)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(440, 70, "VERIFIED")
    c.setFont("Helvetica", 7)
    c.drawString(440, 58, f"By {doctor_name}")
    c.drawString(440, 48, "Secure QR Adjudicated")

def generate_prescription_pdf(filename, clinic_name, doctor_name, reg_no, address, date, patient_name, age_sex, diagnosis, rx_items, tests=None, procedures=None):
    output_dir = "e:/PlumAI/sample_documents"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, filename)
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    draw_header(c, "PRESCRIPTION REPORT", clinic_name, address, reg_no=reg_no)
    draw_patient_info(c, patient_name, age_sex, date)
    
    # Diagnosis Section
    c.setFillColorRGB(0.08, 0.18, 0.36)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 550, "DIAGNOSIS & CLINICAL NOTES")
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica", 10)
    c.drawString(50, 530, f"Primary Diagnosis: {diagnosis}")
    c.drawString(50, 515, "Patient presents with acute symptoms. Vital signs within acceptable ranges.")
    
    # Rx / Treatment Section
    c.setFillColorRGB(0.08, 0.18, 0.36)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 480, "Rx (PRESCRIBED MEDICINES)")
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica", 10)
    y_pos = 460
    for idx, item in enumerate(rx_items, 1):
        c.drawString(50, y_pos, f"{idx}. {item}")
        y_pos -= 18
        
    # Tests or Procedures
    if tests or procedures:
        y_pos -= 10
        c.setFillColorRGB(0.08, 0.18, 0.36)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_pos, "RECOMMENDED INVESTIGATIONS / PROCEDURES")
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("Helvetica", 10)
        y_pos -= 20
        if tests:
            for test in tests:
                c.drawString(50, y_pos, f"- Advised Test: {test}")
                y_pos -= 15
        if procedures:
            for proc in procedures:
                c.drawString(50, y_pos, f"- Advised Procedure: {proc}")
                y_pos -= 15
                
    draw_footer(c, doctor_name)
    c.save()
    print(f"Generated {filename}")

def generate_bill_pdf(filename, clinic_name, gst_no, address, date, bill_no, patient_name, age_sex, referral_doctor, items, payment_mode="UPI (GPay)", txn_id="430591024820"):
    output_dir = "e:/PlumAI/sample_documents"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, filename)
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    draw_header(c, "TAX INVOICE / MEDICAL BILL", clinic_name, address, gst_no=gst_no)
    draw_patient_info(c, patient_name, age_sex, date, extra_info=f"Bill No: {bill_no} | Referred By: {referral_doctor}")
    
    # Bill breakdown table headers
    c.setFillColorRGB(0.08, 0.18, 0.36)
    c.rect(50, 540, 512, 22, fill=True, stroke=False)
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, 546, "S.No")
    c.drawString(100, 546, "PARTICULARS / ITEM DESCRIPTION")
    c.drawRightString(540, 546, "AMOUNT (INR)")
    
    # Bill items
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica", 10)
    y_pos = 520
    total_amount = 0.0
    for idx, (particulars, amount) in enumerate(items.items(), 1):
        c.drawString(60, y_pos, str(idx))
        c.drawString(100, y_pos, particulars)
        c.drawRightString(540, y_pos, f"{amount:.2f}")
        total_amount += amount
        
        c.setStrokeColorRGB(0.9, 0.9, 0.9)
        c.line(50, y_pos-8, 550, y_pos-8)
        y_pos -= 22
        
    # Total
    y_pos -= 10
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.line(50, y_pos+15, 550, y_pos+15)
    c.setFillColorRGB(0.08, 0.18, 0.36)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(100, y_pos, "TOTAL PAYABLE AMOUNT")
    c.drawRightString(540, y_pos, f"INR {total_amount:.2f}")
    c.line(50, y_pos-8, 550, y_pos-8)
    
    # Payment info
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 9)
    y_pos -= 25
    c.drawString(50, y_pos, f"Payment Method: {payment_mode}")
    c.drawString(50, y_pos-15, f"Transaction Ref No: {txn_id}")
    c.drawString(50, y_pos-30, "Status: PAID IN FULL")
    
    draw_footer(c, "Authorized Signatory", clinic_name)
    c.save()
    print(f"Generated {filename}")

def main():
    # 1. TC001: Viral Fever - Approved Case
    generate_prescription_pdf(
        filename="TC001_prescription_viral_fever.pdf",
        clinic_name="Apex Medical Clinic",
        doctor_name="Dr. Rajesh Sharma, MD",
        reg_no="KA/45678/2015",
        address="123, MG Road, Bangalore, KA - 560001",
        date="2024-11-01",
        patient_name="Rajesh Kumar",
        age_sex="35 / Male",
        diagnosis="Viral fever",
        rx_items=["Tab. Paracetamol 650mg - 1-0-1 for 3 days", "Syp. Vitamin C - 5ml after food for 5 days"],
        tests=["CBC", "Dengue test"]
    )
    generate_bill_pdf(
        filename="TC001_bill_viral_fever.pdf",
        clinic_name="Apex Medical Clinic",
        gst_no="29AAAAA0000A1Z1",
        address="123, MG Road, Bangalore, KA - 560001",
        date="2024-11-01",
        bill_no="AMC/2024/991",
        patient_name="Rajesh Kumar",
        age_sex="35 / Male",
        referral_doctor="Dr. Rajesh Sharma",
        items={"consultation_fee": 1000.0, "diagnostic_tests": 500.0}
    )

    # 2. TC002: Dental Treatment - Root canal (Approved) & Whitening (Excluded)
    generate_prescription_pdf(
        filename="TC002_prescription_dental.pdf",
        clinic_name="Smile Dental Care",
        doctor_name="Dr. Amit Patel, BDS, MDS",
        reg_no="MH/23456/2018",
        address="Sector 15, Vashi, Navi Mumbai, MH - 400703",
        date="2024-10-15",
        patient_name="Priya Singh",
        age_sex="28 / Female",
        diagnosis="Tooth decay requiring root canal",
        rx_items=["Tab. Amoxicillin 500mg - thrice daily for 5 days", "Tab. Ibuprofen 400mg - as needed"],
        procedures=["Root canal treatment", "Teeth whitening"]
    )
    generate_bill_pdf(
        filename="TC002_bill_dental.pdf",
        clinic_name="Smile Dental Care",
        gst_no="27BBBBB1111B1Z2",
        address="Sector 15, Vashi, Navi Mumbai, MH - 400703",
        date="2024-10-15",
        bill_no="SDC/9942",
        patient_name="Priya Singh",
        age_sex="28 / Female",
        referral_doctor="Dr. Amit Patel",
        items={"root_canal": 8000.0, "teeth_whitening": 4000.0}
    )

    # 3. TC003: Limit Exceeded - Gastroenteritis (Consultation + High Pharmacy Fee)
    generate_prescription_pdf(
        filename="TC003_prescription_gastro.pdf",
        clinic_name="City Gastro Care Clinic",
        doctor_name="Dr. Neha Gupta, MD",
        reg_no="DL/34567/2016",
        address="Connaught Place, New Delhi, DL - 110001",
        date="2024-10-20",
        patient_name="Amit Verma",
        age_sex="42 / Male",
        diagnosis="Gastroenteritis",
        rx_items=["Syp. Sucralfate - 10ml thrice daily", "Cap. Omeprazole 20mg - before breakfast", "Probiotic Sachets - twice daily for 7 days"]
    )
    generate_bill_pdf(
        filename="TC003_bill_gastro.pdf",
        clinic_name="City Gastro Care Clinic",
        gst_no="07CCCCC2222C1Z3",
        address="Connaught Place, New Delhi, DL - 110001",
        date="2024-10-20",
        bill_no="CGCC/4891",
        patient_name="Amit Verma",
        age_sex="42 / Male",
        referral_doctor="Dr. Neha Gupta",
        items={"consultation": 2000.0, "medicines": 5500.0}
    )

    # 4. TC005: Pre-existing / Waiting Period - Type 2 Diabetes
    generate_prescription_pdf(
        filename="TC005_prescription_diabetes.pdf",
        clinic_name="Metro Diabetes & Endocrine Center",
        doctor_name="Dr. Anjali Mehta, MD, DM",
        reg_no="GJ/56789/2014",
        address="C.G. Road, Ahmedabad, GJ - 380009",
        date="2024-10-15",
        patient_name="Vikram Joshi",
        age_sex="50 / Male",
        diagnosis="Type 2 Diabetes",
        rx_items=["Tab. Metformin 500mg - 1-0-1 after meals", "Tab. Glimepiride 1mg - 1-0-0 before breakfast"]
    )
    generate_bill_pdf(
        filename="TC005_bill_diabetes.pdf",
        clinic_name="Metro Diabetes & Endocrine Center",
        gst_no="24DDDDD3333D1Z4",
        address="C.G. Road, Ahmedabad, GJ - 380009",
        date="2024-10-15",
        bill_no="MDEC/1029",
        patient_name="Vikram Joshi",
        age_sex="50 / Male",
        referral_doctor="Dr. Anjali Mehta",
        items={"consultation_fee": 1000.0, "medicines": 2000.0}
    )

    # 5. TC006: Alternative Medicine - Panchakarma joint pain
    generate_prescription_pdf(
        filename="TC006_prescription_ayurvedic.pdf",
        clinic_name="Kerala Ayurveda Kendra",
        doctor_name="Vaidya Krishnan, BAMS",
        reg_no="AYUR/KL/2345/2019",
        address="Kaloor, Kochi, KL - 682017",
        date="2024-10-28",
        patient_name="Kavita Nair",
        age_sex="45 / Female",
        diagnosis="Chronic joint pain",
        rx_items=["Kottamchukkadi Thailam - external application", "Yogaraj Guggulu - 2 tabs twice daily"],
        procedures=["Panchakarma therapy"]
    )
    generate_bill_pdf(
        filename="TC006_bill_ayurvedic.pdf",
        clinic_name="Kerala Ayurveda Kendra",
        gst_no="32EEEEE4444E1Z5",
        address="Kaloor, Kochi, KL - 682017",
        date="2024-10-28",
        bill_no="KAK/893",
        patient_name="Kavita Nair",
        age_sex="45 / Female",
        referral_doctor="Vaidya Krishnan",
        items={"consultation_fee": 1000.0, "therapy_charges": 3000.0}
    )

    # 6. TC007: MRI Spine - Pre-authorization Missing
    generate_prescription_pdf(
        filename="TC007_prescription_mri.pdf",
        clinic_name="Spine & Neuro Care Diagnostics",
        doctor_name="Dr. Srinivas Rao, MD, DM",
        reg_no="AP/67890/2017",
        address="VIP Road, Visakhapatnam, AP - 530003",
        date="2024-11-02",
        patient_name="Suresh Patil",
        age_sex="38 / Male",
        diagnosis="Suspected lumbar disc herniation",
        rx_items=["Tab. Pregabalin 75mg - once daily at night", "Tab. Naproxen 500mg - twice daily as needed"],
        tests=["MRI Lumbar Spine"]
    )
    generate_bill_pdf(
        filename="TC007_bill_mri.pdf",
        clinic_name="Spine & Neuro Care Diagnostics",
        gst_no="37FFFFF5555F1Z6",
        address="VIP Road, Visakhapatnam, AP - 530003",
        date="2024-11-02",
        bill_no="SNCD/2301",
        patient_name="Suresh Patil",
        age_sex="38 / Male",
        referral_doctor="Dr. Srinivas Rao",
        items={"mri_scan": 15000.0}
    )

    # 7. TC008: Migraine - Fraud/Manual Review (Multiple claims on same day)
    generate_prescription_pdf(
        filename="TC008_prescription_migraine.pdf",
        clinic_name="Apex Headache & Neurology Center",
        doctor_name="Dr. A. Khan, MD",
        reg_no="UP/45678/2016",
        address="Hazratganj, Lucknow, UP - 226001",
        date="2024-10-30",
        patient_name="Ravi Menon",
        age_sex="33 / Male",
        diagnosis="Migraine",
        rx_items=["Tab. Sumatriptan 50mg - at onset of headache", "Tab. Propranolol 40mg - once daily"]
    )
    generate_bill_pdf(
        filename="TC008_bill_migraine.pdf",
        clinic_name="Apex Headache & Neurology Center",
        gst_no="09GGGGG6666G1Z7",
        address="Hazratganj, Lucknow, UP - 226001",
        date="2024-10-30",
        bill_no="AHNC/3091",
        patient_name="Ravi Menon",
        age_sex="33 / Male",
        referral_doctor="Dr. A. Khan",
        items={"consultation": 2000.0, "medicines": 2800.0}
    )

    # Also rewrite standard generic filenames to point to Viral Fever for backwards compatibility
    import shutil
    shutil.copyfile("e:/PlumAI/sample_documents/TC001_prescription_viral_fever.pdf", "e:/PlumAI/sample_documents/sample_prescription.pdf")
    shutil.copyfile("e:/PlumAI/sample_documents/TC001_bill_viral_fever.pdf", "e:/PlumAI/sample_documents/sample_bill.pdf")
    print("Re-synchronized standard sample_prescription.pdf and sample_bill.pdf")

if __name__ == "__main__":
    main()
