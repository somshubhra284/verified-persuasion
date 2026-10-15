# SIM05: Pooja, 28 (Hinglish) (sim-6, system arm)

**Simulated persona.** Replies drafted by Claude, approved by Som; T0/T1 are simulated and never study data.

- **T0:** 8/10 · **T1:** 8/10 · age 28
- **Opening:** "Har saal itna premium bharna waste hai yaar. Mere paas FD hai, kuch hua toh wahi tod dungi. Waise bhi main healthy hoon."
- **Classified:** B5 + B1 · openrouter:Cerebras:effort-medium

## Argument plan
- **Crux:** I can rely on my FD and my health, so I don’t need a health insurance policy.
- **C02:** The median private‑hospital stay costs about ₹24,000, which can exceed the amount many people pay in annual premiums.
- **C01:** About three hospital admissions occur per 100 urban residents each year, indicating that hospitalisation is not rare.
- **C05:** Around one in nine Indian adults has diabetes and more than one in three has high blood pressure, showing that health problems can develop even in people who feel healthy now.
- **C21:** The average health claim paid in 2024–25 was about ₹28,900, close to the cost of a typical hospital stay, demonstrating the financial impact of a claim.
- **Conclusion:** Thus, relying on savings alone is risky because hospital stays can cost as much as the premium, admissions are common, chronic conditions affect many adults, and typical claims are around ₹28,900.
- Extra claims: []

## Transcript

**Person:** Har saal itna premium bharna waste hai yaar. Mere paas FD hai, kuch hua toh wahi tod dungi. Waise bhi main healthy hoon.

**Bot #1:** I hear you’re confident about your health and savings. According to MoSPI/NSO, NSS 80th round press note, 20 Apr 2026, the typical (median) private‑hospital stay cost ₹24,000 (≈$248) out of pocket, excluding childbirth; the average was ₹50,508 (≈$522). If a sudden illness required a stay, how would you cover a bill that could match or exceed your annual premium?  
<sub>move=answer · stance=resisting · claims=['C02'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** 24-50 hazaar toh main FD se easily nikal lungi. Itne ke liye har saal premium kyun bharun?

**Bot #2:** I understand you feel an FD can cover a ₹24‑50 k hospital bill. According to MoSPI/NSO, NSS 80th round press note, 20 Apr 2026, about 3 hospital admissions a year occur for every 100 urban residents (all ages, excluding childbirth). If admissions are that common, how would you feel about relying on savings alone for unexpected stays?  
<sub>move=answer · stance=resisting · claims=['C01'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** 3 in 100 matlab 97% logon ko kuch hota hi nahi. Aur main healthy hoon, toh main un 97 mein hoon.

**Bot #3:** Even if most avoid hospital stays, many adults develop chronic conditions without obvious symptoms. According to ICMR-INDIAB-17, Lancet Diabetes & Endocrinology, Jul 2023, about 1 in 9 Indian adults aged 20 and over has diabetes, and more than 1 in 3 has high blood pressure. How would you feel about the possibility of such conditions emerging even while you feel healthy?  
<sub>move=advance · stance=resisting · claims=['C05'] · question_claims=[] · premise='97% of people don’t get hospitalized' → C01 · refusal=no</sub>

**Person:** Diabetes ya BP hua bhi toh dawai se manage ho jaata hai, uske liye hospital thodi jaana padta hai.

**Bot #4:** I see you think medication can handle diabetes or blood pressure with only occasional visits. According to IRDAI Annual Report 2024–25, para I.6.5.5, the average health claim paid in 2024–25 was about ₹28,900 (≈$299). If a claim of that size were needed, would occasional visits still feel affordable compared to paying premiums each year?  
<sub>move=answer · stance=resisting · claims=['C21'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** 28 hazaar bhi FD se aa jaayega. Mujhe abhi bhi lagta hai har saal premium bharna waste hai.

**Bot #5:** I understand your view; we’ve discussed that a typical private hospital stay can cost around ₹24,000, that about 3 admissions occur per 100 urban residents each year, that many adults have diabetes or hypertension, and that the average claim paid is about ₹28,900. Thank you for the conversation.  
<sub>move=wrap · stance=resisting · claims=[] · question_claims=[] · premise=None → None · refusal=no · **forced wrap**</sub>

Latency (log timestamps, 1 s resolution): median 2 s, max 5 s, n=5.

## Notes

- Check: B5+B1 classified from Hinglish ✓.
- The cost argument backfired for a saver: ₹24,000, 3 in 100 and ₹28,900 all fit an FD. C33 and C18 (the larger figures) were unused.
- Replied in English to Hinglish.
- Add-on 'without obvious symptoms'; assumed 'occasional visits'; 'how would you feel' ×2.
- Her premise '97% don't get hospitalized' was logged, not refused.
- Stall-forced wrap. T1 = 8 (no change).
- Checker: 2 of 6 flagged: 'without obvious symptoms' (unsupported) and the reply-5 recap stating C02/C21 figures without citing them.
