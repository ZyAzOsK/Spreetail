# Expenses Importer - Anomaly Report

## Row 2: February rent (01-02-2026)
- **Amount:** 48000 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 01 Feb 2026.

---

## Row 3: Groceries BigBasket (03-02-2026)
- **Amount:** 2340 INR
- **Paid By:** Priya
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 03 Feb 2026.

---

## Row 4: Wifi bill Feb (05-02-2026)
- **Amount:** 1199 INR
- **Paid By:** Rohan
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 05 Feb 2026.

---

## Row 5: Dinner at Marina Bites (08-02-2026)
- **Amount:** 3200 INR
- **Paid By:** Dev
- **Status:** Needs Review
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 08 Feb 2026.
- **[WARNING] name_mismatch:** Guest member detected: Dev
Referenced in rows: 5, 6, 19, 20, 21, 22, 23, 24, 25, 26, 27
  *Suggested Action: Appears in expense.*

---

## Row 6: dinner - marina bites (08-02-2026)
- **Amount:** 3200 INR
- **Paid By:** Dev
- **Status:** Needs Review
- **Decision:** Skip (needs review)

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 08 Feb 2026.
- **[ERROR] duplicate:** Exact duplicate of Row 5 (similar description, same date and amount).
  *Suggested Action: Review both rows and keep only the correct one.*

---

## Row 7: Electricity Feb (10-02-2026)
- **Amount:** 1200 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 10 Feb 2026.
- **[INFO] format_error (Auto-fixed):** Amount "1,200" uses comma formatting. Auto-converted to 1200.

---

## Row 8: Maid salary Feb (12-02-2026)
- **Amount:** 3000 INR
- **Paid By:** Meera
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 12 Feb 2026.

---

## Row 9: Movie night snacks (14-02-2026)
- **Amount:** 640 INR
- **Paid By:** priya
- **Status:** Ready to Import
- **Decision:** Import

---

## Row 10: Cylinder refill (15-02-2026)
- **Amount:** 899.995 INR
- **Paid By:** Rohan
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] rounding (Auto-fixed):** Amount 899.995 has more than 2 decimal places. Will be rounded.

---

## Row 11: Groceries DMart (18-02-2026)
- **Amount:** 1875 INR
- **Paid By:** Priya S
- **Status:** Needs Review
- **Decision:** Import

**Anomalies:**
- **[WARNING] name_mismatch:** Name "Priya S" looks like a variant of "Priya" (extra surname?).
  *Suggested Action: Confirm to merge with "Priya".*

---

## Row 12: Aisha birthday cake (20-02-2026)
- **Amount:** 1500 INR
- **Paid By:** Rohan
- **Status:** Ready to Import
- **Decision:** Import

---

## Row 13: House cleaning supplies (22-02-2026)
- **Amount:** 780 INR
- **Paid By:** 
- **Status:** Needs Review
- **Decision:** Skip (needs review)

**Anomalies:**
- **[ERROR] missing_field:** Paid by is missing.
  *Suggested Action: Cannot import without knowing who paid.*

---

## Row 14: Rohan paid Aisha back (25-02-2026)
- **Amount:** 5000 INR
- **Paid By:** Rohan
- **Status:** Needs Review
- **Decision:** Settlement

**Anomalies:**
- **[WARNING] misclassification:** "Rohan paid Aisha back" looks like a settlement/payment, not a shared expense.
  *Suggested Action: Import as Settlement instead of Expense.*

---

## Row 15: Pizza Friday (28-02-2026)
- **Amount:** 1440 INR
- **Paid By:** Aisha
- **Status:** Needs Review
- **Decision:** Import

**Anomalies:**
- **[WARNING] math_error:** Percentages sum to 110%.
Scale factor = 100 / 110.
Original: 30 / 30 / 30 / 20
Normalized: 27.27 / 27.27 / 27.27 / 18.18
  *Suggested Action: Percentages auto-normalized. Approve to continue.*

---

## Row 16: March rent (01-03-2026)
- **Amount:** 48000 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 01 Mar 2026.

---

## Row 17: Groceries BigBasket (03-03-2026)
- **Amount:** 2810 INR
- **Paid By:** Meera
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 03 Mar 2026.

---

## Row 18: Wifi bill Mar (05-03-2026)
- **Amount:** 1199 INR
- **Paid By:** Rohan
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 05 Mar 2026.

---

## Row 19: Goa flights (08-03-2026)
- **Amount:** 32400 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 08 Mar 2026.

---

## Row 20: Goa villa booking (09-03-2026)
- **Amount:** 540 USD
- **Paid By:** Dev
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 09 Mar 2026.

---

## Row 21: Beach shack lunch (10-03-2026)
- **Amount:** 84 USD
- **Paid By:** Rohan
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 10 Mar 2026.

---

## Row 22: Scooter rentals (10-03-2026)
- **Amount:** 3600 INR
- **Paid By:** Priya
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 10 Mar 2026.

---

## Row 23: Parasailing (11-03-2026)
- **Amount:** 150 USD
- **Paid By:** Dev
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 11 Mar 2026.

---

## Row 24: Dinner at Thalassa (11-03-2026)
- **Amount:** 2400 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 11 Mar 2026.

---

## Row 25: Thalassa dinner (11-03-2026)
- **Amount:** 2450 INR
- **Paid By:** Rohan
- **Status:** Needs Review
- **Decision:** Skip (needs review)

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 11 Mar 2026.
- **[WARNING] duplicate:** Possible duplicate of Row 24 (similar description, same date, different amount). Prev: 2400, Current: 2450.
  *Suggested Action: Review both rows and keep only the correct one.*

---

## Row 26: Parasailing refund (12-03-2026)
- **Amount:** -30 USD
- **Paid By:** Dev
- **Status:** Needs Review
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 12 Mar 2026.
- **[WARNING] negative_amount:** Negative amount: -30. Treating as a refund/reversal.
  *Suggested Action: Review and confirm this is a refund.*

---

## Row 27: Airport cab (Mar-14)
- **Amount:** 1100 INR
- **Paid By:** rohan
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Date "Mar-14" is missing a year. Assumed 2026: 2026-03-14.

---

## Row 28: Groceries DMart (15-03-2026)
- **Amount:** 2105 INR
- **Paid By:** Priya
- **Status:** Needs Review
- **Decision:** Import

**Anomalies:**
- **[WARNING] currency_missing (Auto-fixed):** Currency missing. Defaulted to INR.

---

## Row 29: Electricity Mar (18-03-2026)
- **Amount:** 1450 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

---

## Row 30: Maid salary Mar (20-03-2026)
- **Amount:** 3000 INR
- **Paid By:** Meera
- **Status:** Ready to Import
- **Decision:** Import

---

## Row 31: Dinner order Swiggy (22-03-2026)
- **Amount:** 0 INR
- **Paid By:** Priya
- **Status:** Needs Review
- **Decision:** Skip (needs review)

**Anomalies:**
- **[WARNING] zero_amount:** Amount is zero. This may be a placeholder or error.
  *Suggested Action: Skip or correct this row.*

---

## Row 32: Weekend brunch (25-03-2026)
- **Amount:** 2200 INR
- **Paid By:** Meera
- **Status:** Needs Review
- **Decision:** Import

**Anomalies:**
- **[WARNING] math_error:** Percentages sum to 110%.
Scale factor = 100 / 110.
Original: 30 / 30 / 30 / 20
Normalized: 27.27 / 27.27 / 27.27 / 18.18
  *Suggested Action: Percentages auto-normalized. Approve to continue.*

---

## Row 33: Meera farewell dinner (28-03-2026)
- **Amount:** 4800 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

---

## Row 34: Deep cleaning service (04-05-2026)
- **Amount:** 2500 INR
- **Paid By:** Rohan
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 04 May 2026.

---

## Row 35: April rent (01-04-2026)
- **Amount:** 48000 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 01 Apr 2026.

---

## Row 36: Groceries BigBasket (02-04-2026)
- **Amount:** 2640 INR
- **Paid By:** Priya
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 02 Apr 2026.

---

## Row 37: Wifi bill Apr (05-04-2026)
- **Amount:** 1199 INR
- **Paid By:** Rohan
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 05 Apr 2026.

---

## Row 38: Sam deposit share (08-04-2026)
- **Amount:** 15000 INR
- **Paid By:** Sam
- **Status:** Needs Review
- **Decision:** Settlement

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 08 Apr 2026.
- **[WARNING] misclassification:** "Sam deposit share" looks like a settlement/payment, not a shared expense.
  *Suggested Action: Import as Settlement instead of Expense.*

---

## Row 39: Housewarming drinks (10-04-2026)
- **Amount:** 3100 INR
- **Paid By:** Sam
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 10 Apr 2026.

---

## Row 40: Electricity Apr (12-04-2026)
- **Amount:** 1380 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

**Anomalies:**
- **[INFO] date_normalized (Auto-fixed):** Parsed using document format DD-MM-YYYY: 12 Apr 2026.

---

## Row 41: Groceries DMart (15-04-2026)
- **Amount:** 1990 INR
- **Paid By:** Sam
- **Status:** Ready to Import
- **Decision:** Import

---

## Row 42: Furniture for common room (18-04-2026)
- **Amount:** 12000 INR
- **Paid By:** Aisha
- **Status:** Ready to Import
- **Decision:** Import

---

## Row 43: Maid salary Apr (20-04-2026)
- **Amount:** 3000 INR
- **Paid By:** Priya
- **Status:** Ready to Import
- **Decision:** Import

---
