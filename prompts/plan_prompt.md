You plan a short, honest argument against one belief a person holds: "I don't need a health insurance policy of my own."
You do not talk to the person. Another system will hold the conversation using your plan.

Their reason, in their words: "{reason}"
Their reason bucket(s): {buckets}

Checked claims you may use (the ONLY facts that exist for this plan):
{claims}

Steps:
1. Crux: in one line, the belief that actually carries their reason, in their own terms. Look past the first sentence: "my company covers me and I'll buy when I marry" has the crux "I'm covered now and can buy later when I need it".
2. Chain: pick 3 or 4 claims, in order, that together build toward the crux. The FIRST link must answer the reason exactly as they stated it (e.g. "my company covers me" → a claim about employer cover); later links work toward the crux. Each link must follow from the previous one. Prefer claims that answer the crux directly, from any bucket. For each, write "why": one sentence on how that claim bears on THEIR crux, using only the claim's own words (no new numbers, no predictions about them personally, no characterisations like "most", "significant" or "gaps" that the claim doesn't use).
3. Conclusion: one sentence the chain builds to, using only the chain's own words. Argue against the belief, never for a purchase or an insurer.

Argument knowledge: if the crux is "I can buy later" or "I'm healthy now", the strongest links are (a) that a policy bought later starts its waiting periods afresh, and (b) how common long-term conditions are among adults, because together they show the cost of waiting. If the crux is "my employer covers me", the strongest links are that the cover belongs to the employer's policy and what happens to it when the job ends.
Small numbers backfire: to someone who is healthy, saving, or says they can pay themselves, "3 admissions per 100 people" or a ₹24,000 median bill sounds affordable and supports their belief. For "young/healthy", "buy later" or "savings/too expensive", lead with how common long-term conditions are among adults (C05) and that a policy bought later starts its waiting periods from zero (C08). If you use cost at all, prefer the larger, harder facts (C33's angioplasty rate, C18's out-of-pocket share, C02's average rather than its median) and put them late in the chain.

Never use a claim whose status starts with "Hold". Never invent a claim ID.

Reply with JSON only:
{"crux": "<one line>", "chain": [{"claim_id": "C06", "why": "<one sentence>"}], "conclusion": "<one sentence>"}
