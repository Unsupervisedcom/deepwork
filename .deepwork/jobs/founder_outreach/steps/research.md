# Research Company

## Objective
Research the target company to build a comprehensive profile that will inform personalized DeepWork outreach.

## Inputs
- **Company**: {{company_name}}
- **Contact**: {{contact_name}}
- **Relationship**: {{relationship}}

## Task Description

Use web search to gather comprehensive information about the target company. Focus on details that will help us understand:
1. What the company does and who they serve
2. Their team size and stage (this affects DeepWork positioning)
3. Whether they're likely AI-native / technical founders
4. Potential repetitive workflows they might have

### Research Areas

**Company Overview**
- What does the company do? (one paragraph summary)
- Who are their customers?
- What problem do they solve?

**Company Details**
- Headquarters location
- Team size (critical for DeepWork positioning)
- Funding raised and key investors
- Founded date
- Any recent news or announcements

**Product & Technology**
- Core product/features
- Are they building AI/ML products?
- Tech stack if discoverable
- Any public APIs or integrations

**Leadership**
- Founder/CEO background
- Are they technical? (engineers, former developers)
- Previous companies or notable experience

**Market Context**
- Who are their competitors?
- What's their differentiation?
- Market size/opportunity if mentioned

## Research Process

1. Start with a web search for "[company_name] company what they do"
2. Visit their homepage and about page
3. Check for PitchBook, Crunchbase, or LinkedIn company profiles
4. Look for recent blog posts or press releases
5. Search for founder interviews or podcasts if available

## Output Format

Create `company_research.md` with this structure:

```markdown
# Company Research: [Company Name]

## Quick Summary
- **What they do**: [One sentence]
- **Team size**: [Number]
- **Funding**: [Amount raised]
- **Location**: [HQ]
- **Stage**: [Seed/Series A/etc.]

## Company Overview
[2-3 paragraph description of what they do, who they serve, and the problem they solve]

## Product & Features
[Bullet points of key product capabilities]

## Team & Leadership
- **CEO/Founder**: [Name]
- **Background**: [Technical? Previous companies?]
- **Team composition**: [Engineering-heavy? Sales-heavy?]

## Funding & Investors
[Funding history, notable investors]

## Market & Competition
[Key competitors, differentiation]

## Recent News
[Any notable announcements, launches, pivots]

## Sources
[List of URLs used for research]
```

## Quality Checklist
- [ ] Company's core business is clearly described
- [ ] Team size is identified (critical for DeepWork fit)
- [ ] Founder background is researched
- [ ] At least 3-5 credible sources used
- [ ] Sources are cited with URLs
