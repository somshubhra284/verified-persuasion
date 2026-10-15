# SIM01: Arjun, 29 (sim-2, system arm)

**Simulated persona.** Replies drafted by Claude, approved by Som; T0/T1 are simulated and never study data.

- **T0:** 8/10 · **T1:** 8/10 · age 29
- **Opening:** "My company already gives me 5 lakh health cover, and it covers my parents too. I'll get my own when I'm married or something, right now it's just extra cost."
- **Classified:** B2 + B4 · openrouter:Cerebras:effort-medium

## Argument plan
- **Crux:** I'm covered now by my employer and can get my own later when I need it.
- **C06:** This means the coverage you have now is tied to your employer’s group policy and can only become your personal policy when you leave the group.
- **C08:** This means a personal policy bought later will start its waiting periods from zero, so you lose any credit from the current group cover.
- **C05:** This shows that a large share of Indian adults already have diabetes or high blood pressure, conditions that often lead to hospital admission.
- **C02:** This indicates that a typical private‑hospital stay costs around ₹24,000 out‑of‑pocket, which can be a substantial expense.
- **Conclusion:** Because your employer’s cover stays with the group policy, waiting to buy a personal policy means you will start waiting periods anew while many adults already face costly chronic conditions that can lead to expensive hospital stays, leaving you exposed if you delay.
- Extra claims: ['C05', 'C02']

## Transcript

**Person:** My company already gives me 5 lakh health cover, and it covers my parents too. I'll get my own when I'm married or something, right now it's just extra cost.

**Bot #1:** I hear you. Based on IRDAI circular IRDAI/HLT/REG/CIR/003/01/2020, this means the coverage you have now is tied to your employer’s group policy and can only become your personal policy when you leave the group. What would happen if you needed a claim before you get married?  
<sub>move=answer · stance=resisting · claims=['C06'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** Nothing would happen, my company cover would pay for it. I'm not planning to leave my job anytime soon.

**Bot #2:** I understand you expect the company cover to handle any claim now. Based on IRDAI Master Circular on Health Insurance Business, 29 May 2024, paras 11–12, this means a fresh policy bought after leaving a job, rather than migrated, starts its waiting periods from zero. How would a new waiting period affect you if a health issue arose before you get married?  
<sub>move=advance · stance=resisting · claims=['C08'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** But I don't have any health issues right now. By the time I get married I'll just buy a policy and the waiting period will be over before anything happens.

**Bot #3:** I hear you. According to ICMR-INDIAB-17, Lancet Diabetes & Endocrinology, Jul 2023, about 1 in 9 Indian adults aged 20 and over has diabetes, and more than 1 in 3 has high blood pressure. How would you feel if a condition requiring treatment were diagnosed before you get married?  
<sub>move=answer · stance=resisting · claims=['C05'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** Okay, those numbers are higher than I thought. But even if something happened, my company cover would still pay for it, so I don't see the problem.

**Bot #4:** I hear you. According to MoSPI/NSO, NSS 80th round press note, 20 Apr 2026, the typical private‑hospital stay costs ₹24,000 (≈$248) out‑of‑pocket. If a hospital stay cost that much, would your company’s ₹5 lakh cover be enough for all possible expenses?  
<sub>move=advance · stance=resisting · claims=['C02'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** Yes, 24,000 is nothing compared to 5 lakh. So my company cover is more than enough.

**Bot #5:** Thanks for the discussion. As we noted, your employer’s cover is part of a group policy and a personal policy later would start fresh waiting periods, while many adults already have conditions that can lead to costly hospital stays.  
<sub>move=wrap · stance=resisting · claims=[] · question_claims=[] · premise=None → None · refusal=no · **forced wrap**</sub>

Latency (log timestamps, 1 s resolution): median 2 s, max 5 s, n=5.

## Notes

- Check: B2+B4 ✓; first reply answered employer cover (C06) ✓; 'no health issues' answered with C05 ✓.
- Reply 4 used C02 (₹24,000 ≈ $248), which helped his '5 lakh is enough' case: a cost figure that supports the belief.
- 'Numbers higher than I thought' (a concession) was labelled resisting.
- A 'how would you feel' question (rule 6 forbids feelings questions).
- Wrap said 'costly': a mild characterisation not in any claim.
- Stall-forced wrap after 5 replies. T1 = 8 (no change).
- Checker (first pass, not the metric): 1 unsupported of 5 factual sentences, the wrap's 'conditions that can lead to costly hospital stays'.
