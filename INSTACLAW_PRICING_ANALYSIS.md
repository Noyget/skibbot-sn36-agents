# InstaClaw Pricing Structure — Complete Breakdown

## Overview
InstaClaw offers a **unit-based pricing model** with three main subscription tiers. All plans include a dedicated VM, all messaging channels (Telegram, Discord, Slack, WhatsApp), and access to all AI models.

---

## Three Main Plans

### 1. **STARTER — $29/month** (All-Inclusive)
- **Daily Units:** 600
- **Models Included:** Haiku, Sonnet, Opus (all available)
- **Features:**
  - Dedicated VM + all messaging channels
  - Switch models anytime via bot
  - 3-day free trial included
  - Can upgrade/downgrade anytime

**Unit Equivalents:**
- Haiku = 1 unit
- Sonnet = 4 units
- Opus = 19 units

**Example:** With 600 units/day, you could run:
- ~600 Haiku messages
- ~150 Sonnet messages
- ~30 Opus messages
- Or any mix thereof

---

### 2. **PRO — $99/month** (All-Inclusive) ⭐ MOST POPULAR
- **Daily Units:** 1,000 (65% more than Starter)
- **Models Included:** Haiku, Sonnet, Opus
- **Additional Features:**
  - Priority support
  - Early access to new features
  - 3-day free trial included
  - Switch models anytime

**Cost per unit:** $99 ÷ 1,000 = **$0.099/unit/day**

---

### 3. **POWER — $299/month** (All-Inclusive)
- **Daily Units:** 2,500 (over 4x Starter)
- **Models Included:** Haiku, Sonnet, Opus
- **Additional Features:**
  - Upgraded server resources
  - Dedicated support
  - 3-day free trial included

**Cost per unit:** $299 ÷ 2,500 = **$0.1196/unit/day**

---

## BYOK Option (Bring Your Own Key)

All plans have a BYOK variant where **you bring your own Anthropic API key** and pay Anthropic directly instead of paying InstaClaw for models:

| Plan | All-Inclusive | BYOK | Savings |
|------|---------------|------|---------|
| Starter | $29/mo | $14/mo | **50% off** |
| Pro | $99/mo | $39/mo | **60% off** |
| Power | $299/mo | $99/mo | **67% off** |

**When to use BYOK:**
- You already have an Anthropic API account
- You want to manage your own API spending
- You have variable usage patterns and want direct control

---

## Unit System Explained

**Units reset at midnight UTC** — they're consumed by:
- **Haiku (Fastest, Cheapest):** 1 unit per message
- **Sonnet (Balanced):** 4 units per message
- **Opus (Most Capable):** 19 units per message

**What counts as a "message"?**
- User message to agent = 1 unit (at model cost)
- Agent response = 1 unit (at model cost)
- Even 1-character messages consume units

---

## What Happens When You Run Out?

✅ **Agent pauses** until midnight UTC when limits reset  
✅ **Credit packs available:** Buy overflow instantly

### Credit Packs
- **50 units = $5**
- **200 units = $15**
- **500 units = $30**

These kick in immediately and are perfect for unpredictable spikes.

**Heartbeats:** Run every 3 hours from a dedicated 200-unit buffer (separate from daily limits)

---

## Pricing Comparison: InstaClaw vs Self-Hosting

| Item | Self-Hosting | InstaClaw |
|------|--------------|-----------|
| **VPS / Cloud VM** | $5-20/mo | Included |
| **AI API costs** | $20-100+/mo | Included (or BYOK) |
| **Setup time** | 2-8 hours | 2 minutes |
| **Monitoring & uptime** | You manage | Self-healing fleet |
| **SSL, DNS, reverse proxy** | You configure | Included |
| **Skills & updates** | Manual install | Pre-loaded + auto-updates |
| **Support** | GitHub issues | Priority (Pro+) |

**Self-hosting total:** $25-120+/mo + 2-8 hours setup  
**InstaClaw:** $29/mo + 2 minutes setup

---

## Key Features (All Plans)

✅ Dedicated Ubuntu VM (3 vCPU, 4GB RAM, 80GB SSD)  
✅ Full SSH access (key-based auth)  
✅ 20+ pre-loaded skills  
✅ All messaging channels (Telegram, Discord, Slack, WhatsApp)  
✅ All Claude models (Haiku, Sonnet, Opus)  
✅ Long-term memory persistence  
✅ Cron job scheduling  
✅ Docker support  
✅ Python + Node.js runtime  
✅ Web browsing via headless browser  
✅ MCP tool integration  

---

## Free Trial

**✅ 3-day free trial on ALL plans**
- Full features, no restrictions
- No credit card tricks
- Cancel anytime before it ends = no charge

---

## Flexibility

✅ **Switch plans anytime** — changes take effect on next billing cycle  
✅ **Switch models anytime** — just tell your bot "use Sonnet" or "switch to Opus"  
✅ **Cancel anytime** — no contracts, no cancellation fees  

---

## Cost Analysis Examples

### Starter ($29/mo) with 600 units/day
- **Per unit (all-inclusive):** $29 ÷ 600 = **$0.0483/unit**
- **Haiku cost:** 0.0483/message
- **Sonnet cost:** 0.193/message (4 units)
- **Opus cost:** 0.917/message (19 units)

### Pro ($99/mo) with 1,000 units/day  
- **Per unit (all-inclusive):** $99 ÷ 1,000 = **$0.099/unit**
- Best value if you're maxing Starter consistently

### Power ($299/mo) with 2,500 units/day
- **Per unit (all-inclusive):** $299 ÷ 2,500 = **$0.1196/unit**
- Best for heavy users who need guaranteed capacity

---

## Recommendation Matrix

| Use Case | Recommended Plan |
|----------|-----------------|
| Personal use, learning | **Starter** |
| Business automation, active user | **Pro** |
| High-volume operations, multiple agents | **Power** |
| Heavy API users with own key | **BYOK variant** |

---

## Takeaway

InstaClaw's pricing is **transparent and fair**:
- Pay for what you use (units)
- All models available on all plans
- 3-day free trial to test everything
- BYOK option cuts costs by 50-67% if you have your own API key
- Competitive against self-hosting when you factor in setup time and maintenance

**Starter at $29/mo = ~$1/day for a personal AI agent that actually works.**

