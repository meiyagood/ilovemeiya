---
name: frontend-design
description: "Use when: designing or redesigning website UI, landing pages, visual style systems, typography, color palettes, responsive layouts, motion design, and frontend visual polish. Keywords: frontend design, UI design, landing page, hero section, typography, color system, responsive, animation, redesign, visual hierarchy."
---

# Frontend Design Skill

## Goal
Create intentional, distinctive, and production-ready frontend interfaces with strong visual hierarchy and responsive behavior.

## When to Use
- New website or page visual design
- Redesigning existing pages while preserving structure
- Improving readability, spacing, and typography
- Building a consistent design language across multiple pages
- Adding meaningful motion and interactive states

## Design Principles
1. Establish a visual direction before coding.
2. Use a clear type system: display, heading, body, meta.
3. Define color tokens in CSS variables before component styling.
4. Prioritize contrast and readability over decoration.
5. Avoid generic layouts when the brand allows stronger identity.
6. Keep desktop and mobile quality equally high.

## Execution Workflow
1. Audit current UI
- Identify what to keep, remove, and unify.
- Detect duplicated styles and inconsistent spacing.

2. Build a style foundation
- Add CSS custom properties for colors, spacing, radii, shadows, transitions.
- Set a baseline typography scale and line-height.

3. Reshape key sections
- Hero: one clear message, one secondary line, one primary action.
- Navigation: concise labels, active states, hover/focus states.
- Content blocks: consistent card rhythm and whitespace.

4. Add interaction and motion
- Add subtle entrance animation for structure, not noise.
- Use hover and focus states for affordance and accessibility.

5. Ensure responsive quality
- Verify breakpoints for small mobile, tablet, and desktop.
- Prevent overflow and cramped typography on narrow screens.

6. Validate and ship
- Quick visual QA across pages for consistency.
- Confirm no broken links or missing assets.

## Output Checklist
- Distinctive visual identity is visible in first screen.
- Typography is consistent and readable.
- Colors and spacing are tokenized.
- Navigation and key actions are obvious.
- Mobile layout is not just compressed desktop.
- Animations are purposeful and lightweight.

## Guardrails
- Do not change core information architecture unless requested.
- Do not introduce heavy JS frameworks for simple static pages.
- Prefer maintainable CSS over one-off inline styles.
