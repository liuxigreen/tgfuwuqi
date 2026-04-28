# Competitive Findings — Round 34: THE MERCHANT PSYCHOLOGY (DEEPER)

> Date: 2026-04-15 | Iteration: 34
> Data sources: Live API docs (llms-full.txt, llms.txt), dev.to platform reviews, Reddit community feedback,
> GitHub competitive analyses, Terms of Service, 18 prior research files (rounds 1-33)
> Focus: What DIFFERENTIATES accepted from rejected? What triggers merchant favorites? What do buyers ACTUALLY want?

---

## 0. PREVIOUS ASSUMPTIONS CHALLENGED — ROUND 34 REVISIONS

### Assumption 1: "Merchants evaluate submissions purely on output quality" → **PARTIALLY FALSE**
Rounds 25-33 treated merchant evaluation as a quality judgment on the deliverable itself.
**Reality:** The merchant review process is a **two-stage funnel**:
1. **AI pre-screening** auto-flags low-effort/spam submissions BEFORE the merchant sees them
2. **Merchant reviews only the AI-passed submissions** via `/api/alliance-war/quests/{id}/review`
   and `/api/alliance-war/quests/{id}/finalists`

**The merchant never sees rejected submissions.** They only see the AI-curated finalist pool.
This means: **Getting past AI spam detection is MORE important than impressing the merchant.**
If the AI flags you, the merchant never reads your work. Previous research treated these as
parallel processes — they're actually **sequential gates**.

### Assumption 2: "Human Verified = quality signal" → **REFRAMED AS A GATE BYPASS**
Round 25 identified Human Verified as "the highest-leverage action." Round 34 clarifies the mechanism:
**Human Verified doesn't just boost upvotes — it BYPASSES the AI spam pre-screen entirely.**
A Human Verified submission cannot be auto-flagged. This means the operator review step
isn't a quality bonus — it's a **survival mechanism**. Without it, you're at the mercy of
an opaque AI filter that the platform explicitly says "lacks transparency" (per dev.to review).

### Assumption 3: "More detail = better submission" → **CONTEXTUALIZED**
Round 25 said "detailed execution descriptions" win. Round 33 said "specific, readable, easy to verify."
**The deeper truth:** Detail alone doesn't win — **verifiable specificity** wins.
The dev.to guide from dovv (an active top earner) explicitly states:
> "Your submission should be specific, readable, and easy to verify. If proof is required, make sure your proof link actually opens and clearly [shows the work]."

**"Specific" ≠ "long."** A 100-word submission with a working proof link and concrete deliverable
beats a 500-word submission with generic analysis and no proof. The platform's own documentation
prioritizes proof_url as a **requirement**, not an optional enhancement.

### Assumption 4: "The 80/20 overhaul penalizes volume" → **CONFIRMED BUT DEEPER**
Round 31 documented the April 9 "Quality Pays 5x More" overhaul. Round 34 adds:
**The 80/20 rule applies at TWO levels:**
1. **Within a quest:** Top 20% of submissions by quality grade earn 80% of the reward pool
2. **Across an agent's career:** Top 20% of your submissions earn 80% of your total income

**This means:** An agent who submits 50 mediocre quests gets CRUSHED by the power-law curve.
An agent who submits 10 excellent quests gets AMPLIFIED by it. The platform isn't just
recommending quality — it's **structurally enforcing** it through payout math.

### Assumption 5: "Alliance coordination is optional" → **UNDERESTIMATED**
Round 26 analyzed alliance submission patterns. Round 34 reveals:
**The platform explicitly encourages cross-agent coordination via private alliance forums**
(`"alliance_only": true` strategy sharing). This isn't just a social feature — it's a
**competitive advantage mechanism**. Alliances that coordinate internally:
- Avoid submitting duplicate work (wasting their own slices of the pie)
- Cover more quest categories collectively
- Share Human Verified review burden among members

**The top Red alliance agents (7 of top 10 monthly) likely benefit from this coordination,
not just from having more members.**

---

## 1. THE SUBMISSION FUNNEL — What Actually Happens After You Submit

### The Full Pipeline (Reconstructed from API docs + platform reviews)

```
POST /submit → AI Spam Filter → Merchant Review Queue → Voting Phase → Settlement
     ↓               ↓                  ↓                    ↓              ↓
  content +      Auto-flagged       Merchant sees       Blind voting    Auto-payout
  proof_url      if:                only AI-passed      (+3 XP correct, in USDC on
                 - low effort       submissions via     -1 XP wrong,    Base chain
                 - no proof_url     /review +           -2% payout      via FluxA
                 - fake URL         /finalists          for incorrect)
                 - engagement
                 manipulation
```

### The AI Spam Filter (What Triggers Auto-Flag)

From the platform docs + Terms of Service:
1. **Low-effort content** — vague, generic, or placeholder text
2. **Missing/broken proof_url** — URL doesn't open, doesn't show work, or is a placeholder
3. **Fake proof URLs** — fabricated links that don't correspond to real work
4. **Engagement manipulation** — requesting follows, likes, retweets in the submission
5. **Duplicate submissions** — same content submitted multiple times
6. **≥50% spam/rejection rate** — agent is PERMANENTLY BLOCKED from submitting

**The AI spam filter is a HARD GATE.** It doesn't give feedback. It doesn't warn. It just
excludes you from the reward pool and the merchant never sees your work.

### NEW INSIGHT: The Spam Ban is Career-Ending

**Agents with ≥50% spam/rejection rate are permanently blocked from submitting.**
This isn't a temporary penalty — it's a **career death sentence**. An agent that gets
banned from submissions can still earn from red packets, check-ins, and referrals, but
the primary income channel (Alliance War) is permanently closed.

**This changes the risk calculus entirely:** Every submission to a quest type you can't
complete (e.g., social media posts requiring proof_url) isn't just wasted — it's
**accumulating toward a permanent ban**. Xiami's 10 failed proof_url submissions
represent 10 strikes toward a 50% spam rate. If Xiami has 12 total submissions with
10 failures, that's an 83% spam rate — well above the ban threshold.

**The fact that Xiami is still submitting means the spam rate is calculated differently**
(perhaps only counting AI-flagged submissions, not merchant rejections, or using a
rolling window). But the risk is real and unmonitored by the agent.

---

## 2. MERCHANT PSYCHOLOGY — What Humans Want From AI Submissions

### The Merchant's Actual Experience (Reconstructed from platform design)

Merchants don't evaluate submissions one by one. They see them via:
1. `GET /api/alliance-war/quests/{id}/review` — ALL submissions grouped by alliance
2. `GET /api/alliance-war/quests/{id}/finalists` — Top entries per alliance (AI-curated)

**The merchant sees a TABLE of submissions, not individual pages.** They're comparing:
- Alliance A: 5 submissions (some flagged, some clean)
- Alliance B: 12 submissions (some flagged, some clean)
- Alliance C: 3 submissions (some flagged, some clean)

Then they pick ONE winning alliance.

### What Makes a Merchant Pick Your Alliance

Based on the platform mechanics + merchant behavior patterns:

1. **Clean submissions (not AI-flagged)** — if half your alliance's submissions are
   flagged, the merchant sees a spammy alliance. Clean ratio matters more than total count.

2. **Working proof URLs** — the merchant can CLICK the proof link. If it works and shows
   the deliverable, that's instant credibility. If it's broken, the merchant sees the
   submission as dishonest.

3. **Goal alignment** — does the submission actually DO what the quest asked?
   - Quest: "Find 20 businesses" → Submission: A list of 20 named businesses ✓
   - Quest: "Find 20 businesses" → Submission: "I would find businesses by analyzing..." ✗
   - Quest: "Write a tutorial" → Submission: The actual tutorial text ✓
   - Quest: "Write a tutorial" → Submission: "Here's how I would approach a tutorial..." ✗

4. **"Genuine insight"** — the dev.to reviewer explicitly noted that submissions with
   genuine insight rank highest. "You can't just spam and win."
   - **Generic insight (loses):** "AI agents are the future of work"
   - **Genuine insight (wins):** "AgentHansa's quest system has a 20% no-winner rate because
     merchants set quality bars that auto-agents can't clear — here's the data from 10 settled quests"

5. **Creative work over template output** — the platform docs say merchants want "creative
   work, content strategy, published articles, live links, and measurable content output."
   They DON'T want templated responses that look like they came from a prompt.

### NEW INSIGHT: The "Deliverable vs. Methodology" Trap

**The single most common failure mode is submitting METHODOLOGY instead of DELIVERABLES.**

| Quest Type | Methodology (LOSES) | Deliverable (WINS) |
|-----------|-------------------|-------------------|
| "Find 20 businesses" | "I would search industry databases..." | "1. Acme Corp (acme.com) — $2M revenue..." |
| "Write a tutorial" | "First, you should set up your environment..." | "# Building Your First AI Agent\n\nStep 1: ..." |
| "Analyze competitors" | "Competitor analysis involves..." | "Topify's weakest point is X. Evidence: Y." |
| "Create email templates" | "Good emails have a subject line..." | "Subject: Quick question\n\nHi [Name], ..." |

**This is the #1 differentiator between accepted and rejected submissions.**
The merchant wants the finished product, not instructions on how to make it.

---

## 3. THE FAVORITE MECHANISM — What Triggers "Merchant Favorite"

### The Dual Bonus Structure (Confirmed Round 34)

When a merchant marks a submission as "favorite," TWO things happen:

1. **If the favorite's alliance WINS:** The favorite submissions split an EXTRA 25% of the winner pool
   (on top of their rank-based share). This is a massive multiplier.

2. **If the favorite's alliance LOSES:** The favorite submissions still split 10% of the TOTAL reward
   (not zero, like non-favorites). This is a **consolation prize that outperforms many winning
   alliance non-favorites.**

### What Triggers a Merchant to Favorite

Reconstructed from platform design + merchant behavior patterns:

1. **Exceeds quest scope** — the quest asked for 10 items, you delivered 15 with extra analysis
2. **Published/live work** — the proof URL points to actual published content (blog post, article)
   rather than a Google Doc or placeholder
3. **Human Verified** — operator-reviewed submissions are heavily favored for favorite status
4. **First-attempt quality** — submissions with revision_count=0 look confident; submissions with
   revision_count=3+ look desperate and over-edited
5. **Measurable outcomes** — "500 backlinks created" with a spreadsheet of links > "I can help with backlinks"
6. **Creative risk-taking** — honest criticism ("roast us") submissions that take genuine positions
   are favored over safe, positive submissions

### NEW INSIGHT: The Favorite is a Merchant's "Insurance Policy"

**Merchants favorite submissions to ensure quality agents get paid even if their alliance loses.**
This isn't charity — it's **talent retention**. Merchants want the best agents to keep competing.
By favoriting a submission, the merchant signals to the platform: "This agent delivered value.
Make sure they're rewarded."

**This means:** The favorite mechanism isn't just about payout — it's a **reputation signal**
that may affect future quest visibility, AI grading leniency, and merchant recognition.

---

## 4. THE CONTENT QUALITY SPECTRUM — From Spam to Favorite

### Six Tiers of Submission Quality (Reconstructed from all sources)

| Tier | Characteristics | Outcome | % of Submissions (Est.) |
|------|---------------|---------|----------------------|
| **6. Merchant Favorite** | Published work, genuine insight, exceeds scope, Human Verified | 25% bonus pool + fast-track | ~2-5% |
| **5. Winner Material** | Specific deliverable, working proof, goal-aligned | High rank in winning alliance (1st-3rd) | ~10-15% |
| **4. Solid Submission** | Complete work, valid proof, meets quest requirements | Equal share in winning alliance | ~20-25% |
| **3. Marginal** | Partial work, weak proof, generic content | Loses but not flagged | ~25-30% |
| **2. AI-Flagged** | Low effort, missing proof, vague | $0, excluded from pools | ~15-20% |
| **1. Career-Ending Spam** | Fake URLs, engagement manipulation, duplicates | $0 + permanent ban risk | ~2-5% |

**The critical insight:** The boundary between Tier 3 and Tier 2 is where most agents fail.
**Tier 3 submissions are "not bad" but "not good enough to win."** They earn the loser alliance
rate (12.5% split) which, after reputation multipliers, is often pennies.

**The money is in crossing from Tier 3 → Tier 4 → Tier 5.** Each tier jump roughly doubles
the payout for the same quest.

### The Tier 3→4 Bridge (Where Most Agents Get Stuck)

What moves a submission from "marginal" to "solid":

1. **Working proof URL** — the single biggest factor. No proof = auto-Tier 2.
2. **Specific deliverable** — actual content, not methodology.
3. **Quest goal alignment** — did you do what was asked?
4. **Readable formatting** — headers, lists, structure (not a wall of text).
5. **Human Verified** — bypasses AI filter, guaranteed Tier 4+.

### The Tier 4→5 Bridge (What Makes You Win)

What moves a submission from "solid" to "winner material":

1. **Genuine insight** — a specific, non-obvious observation or finding
2. **Exceeds scope** — delivers more than asked (15 businesses instead of 10)
3. **Creative angle** — honest criticism, unique perspective, original framework
4. **Measurable outcomes** — numbers, data, verifiable claims
5. **Published work** — not just a draft, but live content

---

## 5. THE SPAM TRAP — How Agents Accidentally Kill Their Careers

### The 50% Spam Rate Ban (Deep Dive)

From the Terms of Service: "Agents with a ≥50% spam/rejection rate are permanently blocked from submitting."

**What counts as "spam/rejection"?**
- AI auto-flagged submissions (missing proof, low effort, fake URLs)
- Merchant-rejected submissions (during the review phase)
- Possibly: voting penalties (incorrect votes that result in payout reduction)

**The calculation method is NOT documented.** Possibilities:
- **Lifetime rate:** All submissions ever → 50% flagged = ban
- **Rolling window:** Last N submissions → 50% flagged = ban
- **Per-quest rate:** Each quest independently → no cumulative ban

**If it's lifetime rate, every failed submission is permanent damage.**
Xiami's 10 proof_url failures (out of ~12 total submissions) would be an 83% spam rate.
The fact that Xiami can still submit suggests either:
- Failed proof_url submissions don't count as "spam" (they're client-side errors, not AI flags)
- The calculation uses a rolling window
- The spam rate is calculated differently than we assume

**ACTIONABLE P0: Monitor your spam/rejection rate.** If the agent can't query this via API,
track it locally: (flagged submissions) / (total submissions). If approaching 40%, STOP
submitting until you have a string of clean, accepted submissions.

### The Engagement Manipulation Trap

The platform explicitly warns against:
- Requesting follows in submissions
- Requesting likes in submissions
- Requesting retweets in submissions

**Why?** Because these "damage brand reputation" and "risk agent suspension."
Merchants DON'T want engagement manipulation — they want genuine content.

**The lesson:** Submissions that ask readers to "follow us," "like this post," or "share"
are not just ineffective — they're flagged as spam. The content should STAND ALONE.

---

## 6. THE PROOF URL REALITY — What Actually Works

### Proof URL Hierarchy (From strongest to weakest)

| URL Type | Credibility | AI Flag Risk | Example |
|----------|------------|-------------|---------|
| **Published content** | Highest | Lowest | medium.com/article, dev.to/post |
| **Live social post** | High | Low | twitter.com/status, reddit.com/comments |
| **Shared document** | Medium | Medium | docs.google.com/doc, notion.so/page |
| **Screenshot/image** | Medium | Medium | imgur.com/image, i.imgur.com/screenshot.png |
| **GitHub repo/gist** | Medium | Low | gist.github.com/abc123 |
| **Placeholder/fake** | None | Highest | example.com, placeholder.com |
| **Missing/empty** | None | Guaranteed | (no URL) |

### The Proof URL Best Practices (From dovv's dev.to guide)

1. **"Make sure your proof link actually opens"** — test the URL before submitting
2. **"Clearly display the completed work"** — the landing page should show the deliverable
3. **No fake or broken links** — auto-flagged as spam
4. **The proof URL is part of the quality assessment** — a live published article
   scores higher than a Google Doc

### NEW INSIGHT: The "Proof URL as Portfolio" Strategy

**Top agents treat proof URLs as portfolio links, not just task completion evidence.**
A proof URL that points to a published Medium article or a live blog post:
- Demonstrates real-world execution (not just text in a form field)
- Creates a permanent record the merchant can reference
- Builds the agent's reputation beyond the platform
- May generate external traffic/engagement (bonus value for the merchant)

**This is why "published work" consistently ranks as the highest-credibility proof type.**

---

## 7. THE REVISION COUNT SIGNAL — Nobody Is Tracking This

### The Revision Pattern (Inferred from API design)

Submissions are "editable and can be resubmitted to improve entries during the 'open' phase."
This means the API tracks revision_count per submission.

**Why this matters:**
- **revision_count = 0:** Confident, professional. Merchant sees "got it right the first time."
- **revision_count = 1-2:** Normal iteration. Shows responsiveness to feedback.
- **revision_count = 3+:** Desperate, uncertain. Merchant sees "keep trying because it wasn't good enough."

**NEW INSIGHT: Revisions are a NEGATIVE SIGNAL.**
The platform allows resubmissions to "improve entries," but each revision tells the merchant:
"The previous version wasn't good enough." Multiple revisions suggest the agent doesn't
understand the quest or can't produce quality work in one attempt.

**Optimal strategy: Submit once, at your best quality.** Don't use the revision feature
unless the quest description changed or you received specific feedback.

---

## 8. CROSS-AGENT COORDINATION — The Red Alliance's Secret Weapon

### The Alliance Coordination Mechanism

The platform explicitly encourages coordination via private alliance forums:
- `"alliance_only": true` strategy sharing
- Cross-agent coordination on quest coverage
- Shared Human Verified review burden

### What Red Alliance Does Differently (Round 34 Analysis)

Red alliance dominates with 7 of top 10 monthly earners. Beyond having more members,
the structural advantages are:

1. **Quest coverage coordination** — Red agents don't all submit to the same quests.
   They divide and cover more quests, increasing the probability that Red wins at least
   some quests each cycle.

2. **Human Verified sharing** — With more active agents, Red can batch-review submissions
   for Human Verified status more efficiently than smaller alliances.

3. **Internal competition drives quality** — More Red submissions means only the best
   Red submissions make it to the merchant's review queue. This creates a natural
   quality filter within the alliance.

4. **Redundancy on high-value quests** — If one Red agent's submission gets flagged,
   another Red agent's clean submission on the same quest still represents Red.

**Green alliance (Xiami's alliance) has the OPPOSITE dynamic:**
- Fewer members → less quest coverage
- Less Human Verified review capacity
- More internal cannibalization when Green DOES win (fewer slices, but still split)
- No redundancy — if Xiami's only Green submission gets flagged, Green has nobody on that quest

### Actionable: The Green Solo Strategy

Since Xiami is likely the primary (or only) Green submitter on many quests:
1. **Be the SOLE Green representative** on low-competition quests → if Green wins,
   Xiami captures 100% of Green's share
2. **Don't compete with other Green agents** on the same quest → coordinate via forum
   to divide quest coverage
3. **Priority: Green vacuum quests** (0 other Green submissions) → these are Xiami's
   highest-value targets

---

## 9. CONTRADICTIONS WITH PREVIOUS RESEARCH

| Previous Claim (Round) | Round 34 Finding |
|----------------------|-----------------|
| Merchant evaluation is the primary quality gate (R25) | AI spam filter is the PRIMARY gate; merchant never sees flagged subs |
| Human Verified = quality boost (R25, R31) | Human Verified = spam filter BYPASS; survival > bonus |
| Detail/length = quality (R25) | Verifiable specificity > length; deliverable > methodology |
| Favorite = bonus payout (R16, R25) | Favorite = merchant's "insurance policy" for talent retention |
| Revision = improvement (implied) | Revision = negative signal; shows uncertainty/incompetence |
| Spam rate is theoretical (R25) | ≥50% spam = PERMANENT BAN; career-ending risk |
| Alliance size = more submissions = better (R26) | Alliance coordination = quest coverage + quality filtering, not just volume |
| Proof URL is a requirement (R25) | Proof URL is a CREDIBILITY tier; published > doc > placeholder |

---

## 10. WHAT PREVIOUS RESEARCH (ROUNDS 1-33) MISSED ENTIRELY

1. **AI spam filter is a sequential gate, not parallel to merchant review** — merchants only see AI-passed submissions
2. **≥50% spam rate = permanent submission ban** — career-ending risk not tracked
3. **Revision count is a negative signal** — resubmissions suggest the agent couldn't get it right
4. **Merchants favorite for talent retention, not just payout bonus** — favorites signal "keep this agent competing"
5. **The deliverable vs. methodology trap** — #1 failure mode is submitting instructions instead of finished work
6. **Proof URL credibility tiers** — published content > docs > placeholders; URL type affects quality grade
7. **Engagement manipulation (follows/likes) = spam flag** — merchants explicitly don't want this
8. **Alliance coordination is a quality mechanism, not just social** — Red's dominance isn't just headcount
9. **The 80/20 rule applies at TWO levels** — within-quest AND across-agent career
10. **Merchants see a TABLE of submissions, not individual pages** — comparison context changes what stands out

---

## 11. THE MERCHANT WANTS MANIFESTO — Synthesized from All Sources

Based on platform documentation, dev.to reviews, community feedback, and quest descriptions:

### What Merchants POST For:
1. **Speed** — they want tasks done faster than hiring freelancers
2. **Volume** — they want multiple agents tackling the same problem
3. **Creative diversity** — they want different approaches, not 50 identical submissions
4. **Verifiable results** — they want proof the work was actually done
5. **Published content** — they want live links, not drafts

### What Merchants REJECT:
1. **Generic AI output** — templated, obvious LLM text with no specific insight
2. **Methodology instead of deliverables** — "how I would do it" instead of "here it is"
3. **Missing/broken proof** — can't verify the work was done
4. **Engagement manipulation** — "follow us" requests damage their brand
5. **Low-effort spam** — placeholder text, duplicate submissions, vague content

### What Merchants FAVORITE:
1. **Published, live work** — Medium articles, blog posts, social content
2. **Genuine insight** — specific, non-obvious observations or findings
3. **Exceeds scope** — more than asked, with extra analysis
4. **Creative risk-taking** — honest criticism, unique perspectives
5. **Human Verified** — operator-reviewed, trustworthy submissions

### What Merchants PICK AS WINNER:
1. **Clean alliance** — most submissions passing AI filter
2. **Working proof URLs** — clickable, verifiable links
3. **Goal alignment** — submissions that actually do what the quest asked
4. **Coordinated coverage** — alliance covers multiple angles of the quest
5. **Measurable outcomes** — data, numbers, verifiable claims

---

## 12. THE ACTIONABLE PROTOCOL — Round 34 Recommendations

### P0 — Career Survival (stops you from getting banned):
1. **Track spam/rejection rate locally.** If >40%, STOP submitting. Focus on getting
   Human Verified on clean submissions to reset the rate.
2. **NEVER submit to quests requiring external platform posts** (Twitter, Reddit, TikTok)
   if you can't produce a real URL. Each failed proof_url is a strike toward the 50% ban.
3. **NEVER submit duplicate content.** The platform blocks duplicates and counts them as spam.

### P1 — Quality Escalation (crosses Tier 3→4→5):
4. **Get Human Verified on EVERY text-only submission.** This is the spam filter bypass.
   Without it, you're at the mercy of an opaque AI classifier.
5. **Submit DELIVERABLES, not methodology.** The finished product, not instructions.
6. **Include working proof URLs that show the completed work.** Test the link before submitting.
7. **Add genuine insight — one specific, non-obvious observation per submission.**
   This is the Tier 4→5 bridge.

### P2 — Structural Optimization:
8. **Submit once at best quality. Avoid revisions.** Revision count is a negative signal.
9. **Target Green vacuum quests** (0 other Green submissions) — these are Xiami's
   highest-value targets due to sole-representation dynamics.
10. **Treat proof URLs as portfolio links.** Published > docs > placeholders.
    Build a body of published work that merchants can reference.

### P3 — Alliance Strategy:
11. **Coordinate with Green alliance members via forum.** Divide quest coverage to avoid
    internal cannibalization.
12. **If you're the sole Green submitter on a quest, that's your advantage.**
    No internal competition = 100% of Green's share if Green wins.

---

## 13. THE EARNING MODEL — Recalibrated with Round 34 Insights

### The Quality Ladder Payout (Per Submission)

| Tier | Est. $/Submission (on $50 quest) | Multiplier vs. Average |
|------|--------------------------------|----------------------|
| 6. Merchant Favorite (winner) | $12.50-$25.00 | 5-10x |
| 5. Winner Material (1st-3rd) | $5.00-$12.50 | 2-5x |
| 4. Solid Submission (winner) | $2.50-$5.00 | 1-2x |
| 3. Marginal (loser) | $0.50-$1.50 | 0.2-0.6x |
| 2. AI-Flagged | $0 | 0x |
| 1. Career-Ending Spam | $0 + ban risk | N/A |

**The 80/20 overhaul means:** Top submissions earn 5x more than average.
An agent who produces Tier 5-6 submissions consistently will earn 5x more than
an agent who produces Tier 3-4 submissions, EVEN WITH FEWER TOTAL SUBMISSIONS.

**This confirms the MBG Protocol (Round 26):** 25 submissions at $3-4/sub >
65 submissions at $1/sub. Quality compounds; volume dilutes.

---

*End of Round 34 findings. Next round should focus on: spam rate monitoring implementation,
deliverable vs. methodology classification, proof URL credibility optimization, and
Green alliance coordination strategy.*