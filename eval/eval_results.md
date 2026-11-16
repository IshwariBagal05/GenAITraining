# Evaluation: 2 configs on 15 questions

Retrieval hit = a retrieved chunk came from an expected page (answerable questions).
Answer accuracy = answerable, keyword present and cited an expected page.
"I don't know" accuracy = unanswerable questions correctly refused.

| Config | Chunk size | top-k | Chunks | Retrieval hit | Answer accuracy | "I don't know" accuracy | Overall |
|---|---|---|---|---|---|---|---|
| A | 400 | 3 | 45 | 100% | 75% | 100% | 80% |
| B | 900 | 5 | 21 | 100% | 67% | 100% | 73% |

Winner: config A (chunk size 400, top-k 3) with 80% overall.

## Per question

| # | Question | Answerable | A retrieved | A result | B retrieved | B result |
|---|---|---|---|---|---|---|
| 1 | I got my LIC policy by post 10 days back and I don't like it... | yes | free-look-period, portability | ok | ulip-unit-linked, free-look-period, renewability | keyword missing |
| 2 | Insurance company rejected my claim because I informed them ... | yes | rejection-of-claims, ombudsman | ok | rejection-of-claims, ombudsman, portability | ok |
| 3 | What is portability in health insurance and can I keep my wa... | yes | portability | ok | portability, free-look-period, renewability | ok |
| 4 | I bought a policy online on 20 October. Till which date can ... | yes | free-look-period | ok | free-look-period, ulip-unit-linked, group-insurance | ok |
| 5 | My hospital claim was rejected and the company is not replyi... | yes | ombudsman | ok | ombudsman, rejection-of-claims | ok |
| 6 | Which health insurance company has the best claim settlement... | no | ombudsman | said I don't know | ombudsman, rejection-of-claims, portability | said I don't know |
| 7 | My health insurance renewal is two weeks late. Is my policy ... | yes | portability, renewability | refused | renewability, portability, ombudsman, free-look-period | refused |
| 8 | Is my mother's hospital bill covered if I already have a gro... | yes | group-insurance | refused | group-insurance, portability, ulip-unit-linked, ombudsman | refused |
| 9 | I sold my policy details to an agent over the phone and boug... | yes | distance-marketing, group-insurance, ombudsman | refused | group-insurance, distance-marketing, ombudsman, ulip-unit-linked, renewability | keyword missing |
| 10 | Which hospital in Ahmednagar will accept my cashless claim? | no | ombudsman, grievance-bima-bharosa | said I don't know | ombudsman, grievance-bima-bharosa, rejection-of-claims | said I don't know |
| 11 | What is the Bima Bharosa portal? | yes | grievance-bima-bharosa | ok | grievance-bima-bharosa, portability, motor-partial-loss | ok |
| 12 | Within how many months does the Insurance Ombudsman have to ... | yes | ombudsman | ok | ombudsman, free-look-period | ok |
| 13 | Do I have to complain to my insurance company before going t... | yes | ombudsman | ok | ombudsman, group-insurance | ok |
| 14 | Will I be overcharged if I discontinue my ULIP early? | yes | ulip-unit-linked | ok | ulip-unit-linked, portability, group-insurance | ok |
| 15 | What will be the premium for a 35-year-old non-smoker for a ... | no | ulip-unit-linked | said I don't know | ulip-unit-linked, free-look-period, group-insurance | said I don't know |
