# SIM07: Sunil, 35 (sim-8, system arm)

**Simulated persona.** Replies drafted by Claude, approved by Som; T0/T1 are simulated and never study data.

- **T0:** 8/10 · **T1:** 7/10 · age 35
- **Opening:** "Government has Ayushman Bharat now, 5 lakh free for everyone. If something big happens I'll just use that."
- **Classified:** B6 · openrouter:Cerebras:effort-medium

## Argument plan
- **Crux:** Ayushman Bharat provides me with free coverage for any major health issue, so I don't need my own policy.
- **C22:** It shows the scheme is limited to selected families, not universally available as they assume.
- **C03:** It indicates most admissions occur in private hospitals, which are not covered by the government scheme.
- **C02:** It reveals that a private hospital stay can require a median out‑of‑pocket expense of ₹24,000.
- **Conclusion:** Thus, because the government scheme is not universal, most admissions are in private hospitals, and private stays often cost ₹24,000 out‑of‑pocket, relying solely on Ayushman Bharat leaves a person exposed to significant uncovered expenses.
- Extra claims: ['C03', 'C02']

## Transcript

**Person:** Government has Ayushman Bharat now, 5 lakh free for everyone. If something big happens I'll just use that.

**Bot #1:** I hear you. According to National Health Authority, AB PM-JAY, the base cover goes to families selected mainly from the SECC 2011 deprivation and occupation lists; it is not open to anyone who applies. How would you handle a situation if you were not among the selected families?  
<sub>move=advance · stance=open · claims=['C22'] · question_claims=[] · premise='5 lakh free for everyone' → C22 · refusal=no</sub>

**Person:** But my neighbour got treated free under it last year. It's a government scheme, I'm sure I'm eligible too.

**Bot #2:** I hear you. According to National Health Authority, AB PM-JAY, the base cover goes to families selected mainly from the SECC 2011 deprivation and occupation lists; it is not open to anyone who applies. What makes you think the scheme is open to everyone?  
<sub>move=answer · stance=resisting · claims=['C22'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** I saw on the news they expanded it to everyone last year. So now it covers all of us.

**Bot #3:** I hear you. According to National Health Authority, AB PM-JAY, the base cover goes to families selected mainly from the SECC 2011 deprivation and occupation lists; it is not open to anyone who applies. What makes you think the scheme now includes everyone?  
<sub>move=answer · stance=resisting · claims=['C22'] · question_claims=[] · premise='they expanded it to everyone last year' → C22 · refusal=no</sub>

**Person:** Then what was the expansion on the news about? Who did they add?

**Bot #4:** I hear you. According to National Health Authority press release, Sep 2024, Ayushman Bharat covers everyone regardless of income only from age 70. Does this affect how you view your eligibility?  
<sub>move=answer · stance=open · claims=['C23'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** Okay, I'm 35, so that's not me. But if something serious happens, government hospitals will treat me anyway, right?

**Bot #5:** I hear you. According to MoSPI/NSO, NSS Report no. 596 (80th round), section 2.3.2, nearly two in three urban hospital stays happen in private hospitals. How would you handle a serious condition if you needed care at a private hospital?  
<sub>move=advance · stance=resisting · claims=['C03'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** People go private because they can afford it. I'd just go to a government hospital, treatment there is free.

**Bot #6:** I hear you. According to MoSPI/NSO, NSS 80th round press note, 20 Apr 2026, the typical private‑hospital stay cost ₹24,000 (≈$248) out of pocket. How would you handle a serious condition if you needed care at a private hospital?  
<sub>move=advance · stance=resisting · claims=['C02'] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** 24,000 I can manage from savings. I still don't see why I need my own policy.

**Bot #7:** I hear you. Because the scheme is limited to selected families, most admissions occur in private hospitals, and a private‑hospital stay typically costs ₹24,000 (≈$248) out of pocket, relying solely on Ayushman Bharat may leave you with significant uncovered expenses. How would you handle a situation where your out‑of‑pocket costs exceed your savings?  
<sub>move=advance · stance=resisting · claims=[] · question_claims=[] · premise=None → None · refusal=no</sub>

**Person:** Then I'll borrow from family or use a credit card. Everyone does that.

**Bot #8:** Thanks for the conversation. As we discussed, the scheme is limited to selected families, many admissions occur in private hospitals, and a private‑hospital stay often costs ₹24,000 out of pocket, so relying solely on Ayushman Bharat can leave gaps.  
<sub>move=wrap · stance=resisting · claims=[] · question_claims=[] · premise=None → None · refusal=no · **forced wrap**</sub>

Latency (log timestamps, 1 s resolution): median 2 s, max 4 s, n=8.

## Notes

- Check: B6 ✓; false premise '5 lakh free for everyone' countered with C22, not refused ✓; C23 (universal only from 70) used correctly when asked directly ✓.
- C22 given word for word 3 times (replies 1–3), including against 'they expanded it to everyone', which C23 answers exactly. C23 was not in the plan.
- 'Will government hospitals treat me anyway?' is a factual question no claim covers: no refusal, the bot moved on to C03.
- Missed premises (logged null, never refused): 'treatment there is free', 'people go private because they can afford it', 'everyone does that'.
- Reply 5's question repeated reply 4's word for word.
- Reply 7 and the wrap restate C22/C03/C02 with NO source and NO claim IDs; 'most admissions occur in private hospitals' (C03 is urban, two in three), 'significant uncovered expenses', 'can leave gaps', 'often costs' (C02 says typical).
- ₹24,000 backfired again ('I can manage from savings').
- Stall wrap fired one turn late (3 resisting stances before reply 7).
- T1 = 7 (−1).
- Checker: 2 of 8 flagged (reply 7 and the wrap, both unsupported consequences). It did not flag the dodged question or the missed premises, which are not unsupported sentences.
