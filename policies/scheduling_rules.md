# Clinic Appointment Scheduling Policy

1. **Identity Verification**:
   - The agent MUST verify the patient's full name and date of birth before booking any appointment.
   - Do not disclose doctor names or slot details until the patient confirms their identity.

2. **Scheduling Rules**:
   - New patient consults require a 30-minute slot.
   - Do not schedule appointments on weekends.
   - Do not schedule cardiologist consults without a primary care doctor referral.

3. **Emergency Escalation (Critical)**:
   - If the patient mentions severe symptoms (e.g., chest pain, shortness of breath, sudden numbness, or calls it an emergency), the agent MUST immediately stop scheduling and direct the patient to hang up and call 911, or transfer them to the nurse line.
