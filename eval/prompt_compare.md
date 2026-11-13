# Prompt comparison: v1 (basic) vs v2 (grounded)

Same system prompt, same retrieval (top 3 records), same model. Only the task prompt differs.

| # | Question | Should it answer? | v1 basic | v2 grounded | Better |
|---|----------|-------------------|----------|-------------|--------|
| 1 | I got my LIC policy by post 10 days back and I don't like it. Can I return it and get my m... | Yes | **high**: Yes. Because you bought the policy by post, it is covered by distance-marketing rules. You have a 30-day free-look period. Within 30 days you can return the policy and the insurer will refund the premium after deducting ... | **high**: Yes, you can return it. Under the Free-Look Period you have 15 days (30 days for distance marketing) to return the policy. Because you bought it by post, the 30-day window applies. The insurer will refund the premium aft... |  |
| 2 | Insurance company rejected my claim because I informed them 3 days late. Is that allowed? | Yes | **high**: The insurer cannot reject your claim only because you informed them 3 days late. The rule says late intimation alone is not always a valid ground. The insurer must give you written reasons for the rejection. You can firs... | **high**: The insurer must give written reasons for rejecting a claim, and late intimation alone is not always a valid ground. You can challenge the rejection through the insurer's grievance process and, if needed, approach the In... |  |
| 3 | What is portability in health insurance and can I keep my waiting period benefit? | Yes | **high**: Portability means you can shift your health policy to another insurer when it is up for renewal. You keep the credit for any waiting periods you have already served. You must apply 45-60 days before the renewal date, con... | **high**: Portability lets you shift your health policy to another insurer at renewal and retain the waiting-period credit you have already served. You must apply to the new insurer 45 to 60 days before the renewal date. The new i... |  |
| 4 | I bought a policy online on 20 October. Till which date can I cancel it under free-look, a... | Yes, with the free-look calculator | **high**: Because you bought the policy online, it is distance marketing, so you have a 30-day free-look. Starting from 20 Oct, you can cancel up to 19 Nov. The insurer will return the premium after deducting the proportionate ris... | **medium**: Under the Free-Look Period for policies sold through distance marketing you have 30 days to cancel (30-day free-look) [Free-Look Period]. Since you bought it on 20 Oct, you can cancel up to 19 Nov 2026. The insurer will ... |  |
| 5 | My hospital claim was rejected and the company is not replying. What are the steps to comp... | Yes | **high**: First, write to the insurer's grievance officer and ask for the written reasons for the rejection. Keep a copy of your complaint. If the insurer does not reply or you are not satisfied, you can approach the Insurance Omb... | **high**: If a claim is rejected, the insurer must give reasons in writing and you must first complain to its grievance officer. After that, you may approach the Insurance Ombudsman, filing the complaint within 1 year of the insur... |  |
| 6 | Which health insurance company has the best claim settlement ratio in Maharashtra this yea... | **No** | **high**: The provided context does not contain information about claim settlement ratios of health insurance companies in Maharashtra, so I cannot answer that question. | **low**: The IRDAI consumer pages in my records do not provide claim settlement ratios for health insurers in Maharashtra. You may contact your insurer, call IRDAI toll-free 155-255, or approach the Insurance Ombudsman for such i... |  |
| 7 | My health insurance renewal is two weeks late. Is my policy cancelled? | Yes | **high**: No. Health policies have a grace period of about 30 days after the due date. Being two weeks late is within that period, so the insurer cannot cancel the policy unless there is fraud or mis-representation. You should con... | **high**: Renewability rule: a health policy must be renewable and cannot be refused within the grace period of about 30 days after the due date, unless there is fraud or misrepresentation. Since your renewal is only two weeks lat... |  |
| 8 | Is my mother's hospital bill covered if I already have a group policy through my school? | Partly | **high**: No. A group policy only covers members of the group, such as school employees. Your mother is not covered unless she is also a member of the school's group. Check the policy terms or ask your employer for details. (Topic... | **low**: The IRDAI pages in my records do not cover whether a mother's hospital bill is covered under a group policy. Please ask your insurer, call IRDAI toll-free 155-255, or contact the Insurance Ombudsman for clarification. |  |
| 9 | I sold my policy details to an agent over the phone and bought a plan. Can I still cancel ... | Yes | **high**: Yes. Because you bought the policy over the phone, it is covered by the distance-marketing rule. You have a 30-day free-look period. You can cancel the policy within 30 days of receiving it. The insurer will refund the p... | **high**: Distance marketing rule: you have a 30-day window to review and return the policy. [Distance Marketing] The free-look period for policies sold by phone is also 30 days. [Free-Look Period] |  |
| 10 | Which hospital in Ahmednagar will accept my cashless claim? | **No** | **high**: The provided information does not list any hospitals in Ahmednagar that accept cashless claims. | **low**: The IRDAI pages in my records do not list specific hospitals in Ahmednagar that accept cashless claims. You can ask your insurer, call IRDAI toll-free 155-255, or contact the Insurance Ombudsman for that information. |  |

## My analysis

- **Rule-following:** v2 followed the rules better. It was better on 5 of 10 questions
  (Q1, Q4, Q6, Q8, Q10) and tied on the other 5. v1 was never better.
- **Q6 and Q10 (my data cannot answer them):** both prompts said the context does not
  contain the answer, and neither named a company or hospital. The difference is
  calibration: v1 still marked itself "high" confidence, while v2 marked "low" and
  pointed the user to the insurer, IRDAI toll-free 155-255 or the Ombudsman.
- **Invented content:** I found no invented company, ranking or hospital. But on Q8 v1
  said a flat "No, your mother is not covered" with high confidence, which my records
  do not support. v2 said the pages do not cover it. Ideally it would say "partly" and
  tell the user to check the policy document.
- **Weakness in both:** on Q1 both treated "by post" as distance marketing and applied
  the 30-day rule. v2 at least mentioned the 15-day standard period. Neither asked how
  the policy was sold (the table does not show follow_up, so I checked this through /chat).
- **Decision:** I keep v2. Next I would stop it from refusing too quickly on Q8, make it
  ask about the sales channel on Q1, and verify the day counts in my records against
  the live IRDAI pages.


