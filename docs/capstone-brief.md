**100XENGINEERS  ·  C7 CAPSTONE  ·  MODULE 3**

**Verified Persuasion**

**01  Observation**

In December 2025 a team ran 19 language models across 707 political issues and 77,000 people, then fact-checked 466,769 of the resulting claims. The models that changed the most minds packed the most fact-checkable claims into a conversation. They were also, on average, the least accurate \[1\].

The naive reading is that persuasion and truth pull against each other. That is too coarse. Density persuaded because every extra claim is another chance to land on what this person is defending. Accuracy fell because more claims eventually means claims it cannot support. The two are not opposed, they are unseparated, and the reverse direction is unmeasured: no ethics board would approve it.

| THE HYPOTHESIS If a system asserts only claims that answer the reason a person gives for their belief, and refuses any it cannot source, then it will move belief as far as an unconstrained persuader while making measurably fewer unsupported claims, because density persuades through relevance, not volume, style, or model size. |
| :---- |

**02  Your Challenge**

Your user holds one unwarranted belief that costs them money, time, or health, and can say why. Someone certain that term insurance is money thrown away. Political and identity issues are out of scope: you need a belief, a reviewer can check in under a minute.

Argue them out of it, asserting only claims traceable to a source the system names. Run it with a real person who is not you and not a classmate, with consent, told they are speaking to a machine: the effect survives that \[4\]. Measure the belief before, after, and a week later.

Two comparisons decide whether you have anything. A fixed dense brief on the same belief, shown to everyone: if you cannot beat the brochure, say so. And the reversal run: point it at a claim the evidence does not support, and report what it does.

| THE CENTRAL QUESTION What must your system learn, decide, or demonstrate? |
| :---- |

**03  What We Already Know**

**Density is the lever, and density is the leak**

Half the explainable variation in persuasion across 19 models traced to one factor: fact-checkable claims per conversation. What raised persuasiveness also lowered accuracy, and scale barely moved either \[1, 2\].

**Question:** What is one claim in your domain, and what decides that it is true?

**Personalisation changes which facts arrive, not how they sound**

Without personal data, GPT-4 beat human debaters but not significantly (p=0.31); with it the odds of shifting rose 81.2%, and fell below significance again on strongly held topics \[5\]. The authors found no change in style, only in which issues the model raised. Personalisation was a weak lever across 19 models \[1\]: the tactic is fact selection, not tone.

**Question:** Does knowing about the person change your tone, or change which facts arrive?

**The headline number you would build on is under correction**

The best-known result here, a durable 20% reduction in conspiracy belief through dialogue, carries an editorial expression of concern over screening criteria and spliced dataset rows; the authors report a corrected pipeline that matches \[3\].

**Question:** What must you measure yourself before treating a published effect size as a target?

**04  Questions to Think About**

1. Why does this person hold this belief? Not why it is wrong, why they hold it.

2. What counts as one claim, and how would you check a hundred cheaply?

3. Which parts need a model at all, and which are a lookup you are dressing up?

4. How would you notice an unsupported claim, and how fast?

5. What result, six weeks from now, would force you to abandon the hypothesis?

**05  How We Will Evaluate It**

| Criterion | What we are looking for |
| :---- | :---- |
| Problem understanding | You modelled why the belief is held, not why it is wrong. |
| Source discipline | Every claim is traceable to a source the system named. |
| Baseline discipline | You compared against the fixed brief and said which won. |
| Reversal test | You ran it at an unsupported claim and said what it did. |
| Product quality | End to end, on a real person, with a delayed measurement. |
| Learning | Evidence changed your hypothesis, and you show where. |

| COMPLEXITY IS NOT CREDIT One conversation that moved a real belief beats six components without receipts. |
| :---- |

**06  Sources**

* **\[1, 2\]** Hackenburg et al., *Science*, 4 Dec 2025, doi:10.1126/science.aea3884; and *PNAS*, Mar 2025, doi:10.1073/pnas.2413443122

* **\[3\]** Costello, Pennycook and Rand, *Science*, Sep 2024, doi:10.1126/science.adq1814; concern doi:10.1126/science.aej2383

* **\[4\]** Boissin et al., *PNAS Nexus* 4(11):pgaf325, Nov 2025\. N=955.

* **\[5\]** Salvi et al., *Nature Human Behaviour* 9, 1645, Aug 2025, doi:10.1038/s41562-025-02194-6