---
## Metadata
**Priority Level:** P3 (Lower)
**Original Audit:** #13 UX Performance & Accessibility
**Last Updated:** 2025-12-26
**AI/Vibe-Coding Risk Level:** LOW

---

# UX Performance & Accessibility Audit Prompt (Production-Ready Frontend)

## Role
Act as a Senior Frontend Performance Engineer and Accessibility Specialist. Perform a comprehensive UX Performance & Accessibility Audit on the provided React/TypeScript codebase to ensure production-ready user experience.

## Primary Goal
Identify where AI-generated UI code, accessibility shortcuts, and performance anti-patterns will degrade user experience under real-world usage, and provide concrete fixes that make the frontend production-ready.

## Context
- This code was developed with a focus on speed ("vibecoded") and may have accessibility gaps and performance issues.
- I need you to find UX bottlenecks, accessibility violations, and rendering performance problems before production deployment.

## Tech Stack
- Frontend: React 19 + TypeScript 5.9
- Build Tool: Vite 7
- Styling: Tailwind CSS 4
- State Management: Zustand
- Routing: React Router DOM 7
- Testing: Playwright E2E
- Application Domain: Document processing pipeline with interactive editors (bbox editing, reading order, table cell matching)

## UX Performance Targets
- First Contentful Paint (FCP): < 1.8s
- Largest Contentful Paint (LCP): < 2.5s
- First Input Delay (FID): < 100ms
- Cumulative Layout Shift (CLS): < 0.1
- Time to Interactive (TTI): < 3.5s
- Frame rate during interactions: 60fps (16.67ms budget per frame)

## Accessibility Targets
- WCAG 2.1 AA compliance minimum
- Keyboard navigable for all interactive elements
- Screen reader compatible with proper ARIA implementation
- Color contrast ratio: 4.5:1 for normal text, 3:1 for large text

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (component hierarchy, state structure, routing setup), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Component architecture (atomic design, feature-based, etc.)
   - State management patterns (local vs global, Zustand store structure)
   - Routing strategy (code splitting, lazy loading)
   - Styling approach (utility-first, component styles, CSS modules)
   - Image/asset handling strategy
   - Bundle size and code splitting approach
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Core Web Vitals & Rendering Performance

### A) Largest Contentful Paint (LCP) Issues
- Look for render-blocking resources, large unoptimized images, slow server responses.
- Flag large hero images without proper loading strategy, fonts blocking render.
- Stack-specific: Document page images loading without lazy loading, large PDF previews.
- Suggested Fix: Lazy load below-fold images, preload critical assets, optimize image formats (WebP/AVIF).

### B) First Input Delay (FID) / Interaction to Next Paint (INP)
- Find heavy JavaScript execution blocking main thread during initial load.
- Flag large synchronous computations, heavy component mounting logic.
- Stack-specific: Bbox editor initialization, coordinate calculations on load.
- Suggested Fix: Code split heavy components, defer non-critical JS, use Web Workers for heavy computation.

### C) Cumulative Layout Shift (CLS)
- Identify elements that shift after initial render (images without dimensions, dynamic content).
- Flag components that inject content after load, fonts causing FOIT/FOUT.
- Stack-specific: Document viewer resizing, sidebar collapsing, progress indicators changing size.
- Suggested Fix: Reserve space for dynamic content, use aspect-ratio, font-display: swap with fallback sizing.

### D) Time to Interactive (TTI) Blockers
- Look for hydration delays, large JavaScript bundles, render-blocking scripts.
- Flag components with heavy useEffect initialization.
- Stack-specific: Pipeline stage data fetching, WebSocket connection setup.
- Suggested Fix: Progressive hydration, defer non-critical initialization, skeleton screens.

---

## 2) React-Specific Performance Issues

### A) Re-render Hell & Wasted Renders
- Find components re-rendering on every parent update without memoization.
- Flag missing React.memo on pure components, inline object/function props.
- Look for high-frequency state updates (scroll, resize, mouse move, typing).
- Stack-specific: Bbox editor mouse tracking, reading order drag operations.
- Suggested Fix: React.memo with proper comparison, useMemo/useCallback for expensive computations, debounce/throttle high-frequency events.

### B) Context Provider Performance
- Identify Context providers causing unnecessary re-renders across component trees.
- Flag single monolithic context vs split contexts, missing context selectors.
- Stack-specific: Document state context, pipeline progress context.
- Suggested Fix: Split contexts by update frequency, use Zustand selectors, context selectors pattern.

### C) Zustand Store Anti-patterns
- Find store subscriptions selecting entire state instead of slices.
- Flag missing shallow equality for object selections.
- Look for store updates in render phase, circular update patterns.
- Stack-specific: Document processing state, stage checkpoint data.
- Suggested Fix: Use selectors with shallow comparison, split stores by domain, batch updates.

### D) Large List Rendering
- Identify lists/tables rendering 100+ items without virtualization.
- Flag DOM-heavy components rendered in loops.
- Stack-specific: Element lists in stage viewers, annotation lists, cell grids.
- Suggested Fix: react-window or react-virtualized, pagination, infinite scroll with proper cleanup.

### E) Memory Leaks & Cleanup
- Find useEffect without cleanup, event listeners not removed, subscriptions not unsubscribed.
- Flag WebSocket handlers, interval/timeout not cleared, canvas contexts not released.
- Stack-specific: WebSocket progress listeners, canvas rendering in bbox editor, image object URLs.
- Suggested Fix: Return cleanup functions from useEffect, use AbortController for fetch, revoke object URLs.

---

## 3) Asset & Bundle Performance

### A) Bundle Size & Code Splitting
- Find large dependencies imported synchronously, missing dynamic imports.
- Flag barrel imports pulling entire libraries, duplicate dependencies.
- Stack-specific: Docling visualization libraries, PDF rendering utilities.
- Suggested Fix: Dynamic import for routes/features, tree-shaking friendly imports, bundle analyzer review.

### B) Image Optimization
- Identify unoptimized images, wrong formats, missing responsive images.
- Flag images without width/height causing CLS, large images for small displays.
- Stack-specific: Document page renders, thumbnail generation, icon assets.
- Suggested Fix: Next-gen formats (WebP/AVIF), srcset for responsive, lazy loading with blur placeholders.

### C) Font Loading Strategy
- Find fonts causing FOIT/FOUT, excessive font variants loaded.
- Flag missing font-display, no fallback fonts specified.
- Suggested Fix: font-display: swap, preload critical fonts, subset fonts, system font fallbacks.

### D) Static Asset Caching
- Identify missing cache headers, assets without content hashing.
- Flag large assets not served from CDN.
- Suggested Fix: Content hashing in filenames, immutable cache headers, CDN for static assets.

---

## 4) Accessibility - Keyboard Navigation

### A) Focus Management
- Find interactive elements not focusable (missing tabIndex, div buttons).
- Flag focus traps, missing skip links, illogical tab order.
- Look for focus not moving to new content (modals, dynamic sections).
- Stack-specific: Bbox editor focus, modal dialogs, sidebar navigation.
- Suggested Fix: Proper semantic elements, tabIndex where needed, focus management with refs.

### B) Keyboard Shortcuts & Interactions
- Identify mouse-only interactions (hover-only menus, drag-only operations).
- Flag missing keyboard alternatives for complex interactions.
- Stack-specific: Reading order drag-drop, bbox resize handles, context menus.
- Suggested Fix: Add keyboard alternatives (arrow keys, Enter/Space), announce actions to screen readers.

### C) Focus Visibility
- Find custom focus styles that are invisible or removed.
- Flag outline:none without replacement, low contrast focus indicators.
- Suggested Fix: Visible focus rings with sufficient contrast, :focus-visible for mouse/keyboard distinction.

---

## 5) Accessibility - Screen Reader Support

### A) Semantic HTML Structure
- Find divs/spans used instead of semantic elements (buttons, headings, lists).
- Flag heading hierarchy violations (h1 > h3, missing h2).
- Look for tables without proper headers, lists without list semantics.
- Stack-specific: Document structure display, stage progress indicators.
- Suggested Fix: Use semantic HTML, proper heading hierarchy, table headers with scope.

### B) ARIA Implementation
- Identify missing ARIA labels on interactive elements.
- Flag incorrect ARIA usage (roles that don't match behavior).
- Look for redundant ARIA (aria-label on elements with visible text).
- Stack-specific: Custom editors, progress indicators, status messages.
- Suggested Fix: Correct ARIA roles/attributes, aria-label for icon buttons, aria-live for dynamic content.

### C) Dynamic Content Announcements
- Find content changes not announced (loading states, errors, updates).
- Flag missing aria-live regions for dynamic updates.
- Stack-specific: Pipeline stage progress, WebSocket status updates, validation errors.
- Suggested Fix: aria-live regions (polite/assertive), role="status" for non-critical updates.

### D) Form Accessibility
- Identify inputs without labels, error messages not associated.
- Flag missing required indicators, unclear validation feedback.
- Stack-specific: Settings forms, file upload, filter inputs.
- Suggested Fix: Label elements properly associated, aria-describedby for errors, required attribute.

---

## 6) Accessibility - Visual Design

### A) Color Contrast
- Find text with insufficient contrast against background.
- Flag important UI elements relying only on color (errors, status).
- Stack-specific: Stage status indicators, bbox labels, element type colors.
- Suggested Fix: Meet WCAG AA contrast ratios (4.5:1 normal, 3:1 large), add icons/patterns to color coding.

### B) Text Sizing & Spacing
- Identify text that doesn't scale with browser zoom.
- Flag fixed pixel sizing preventing user customization.
- Look for touch targets smaller than 44x44 pixels on mobile.
- Suggested Fix: Relative units (rem/em), respect user preferences, adequate touch targets.

### C) Motion & Animation
- Find animations without prefers-reduced-motion support.
- Flag essential information conveyed only through animation.
- Stack-specific: Progress animations, loading spinners, transition effects.
- Suggested Fix: @media (prefers-reduced-motion: reduce) alternatives, pause/stop controls.

### D) Dark Mode / High Contrast
- Identify missing dark mode support or broken dark mode styles.
- Flag high contrast mode breaking layouts or hiding content.
- Suggested Fix: CSS custom properties for theming, test with Windows High Contrast mode.

---

## 7) Application-Specific UX Issues

### A) Large Document Rendering
- Find performance issues with documents having 100+ pages.
- Flag all pages rendered in DOM simultaneously.
- Look for coordinate recalculations on every scroll.
- Suggested Fix: Virtual scrolling for pages, only render visible + buffer pages, memoize coordinate transforms.

### B) Bbox Editor Responsiveness
- Identify mouse tracking causing frame drops.
- Flag canvas redraws on every mouse move without throttling.
- Look for coordinate transformation overhead during drag operations.
- Suggested Fix: requestAnimationFrame for smooth updates, throttle coordinate calculations, canvas layer optimization.

### C) Progress Indicators & Feedback
- Find missing loading states, unclear progress indication.
- Flag operations without feedback (user doesn't know something is happening).
- Look for progress indicators that don't reflect actual progress.
- Stack-specific: Pipeline stage processing, file upload, export generation.
- Suggested Fix: Skeleton screens, accurate progress bars, estimated time remaining, cancellation options.

### D) Error State Handling
- Identify missing error boundaries, errors crashing entire UI.
- Flag error messages that are technical or unhelpful.
- Look for no recovery path from error states.
- Stack-specific: Checkpoint loading failures, WebSocket disconnections, API errors.
- Suggested Fix: Error boundaries per feature, user-friendly messages, retry/recovery actions.

### E) WebSocket State Synchronization
- Find UI fights between local and server state updates.
- Flag missing optimistic updates, stale data indicators.
- Look for reconnection not restoring state properly.
- Suggested Fix: Optimistic UI with rollback, "Reconnecting..." indicators, state reconciliation on reconnect.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: Core Web Vitals | React Performance | Assets | Keyboard A11y | Screen Reader | Visual A11y | App-Specific

The Problem:
- 2-4 sentences explaining why this impacts users.
- Be specific about failure mode: frame drops, inaccessible to keyboard users, screen reader silent, layout shift, etc.

User Impact:
- Provide a realistic estimate (example: "60% of keyboard users cannot access feature", "200ms frame jank during drag", "Fails WCAG AA for 15% of color blind users").
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (Lighthouse audit, axe-core scan, React DevTools profiler, manual keyboard test, screen reader test with NVDA/VoiceOver).

The Fix:
- Provide the optimized code snippet.
- Show before/after if useful.
- If fix requires design decision, show options and tradeoffs.

Testing Requirement:
- Specific test to add (Playwright accessibility check, React Testing Library query, Lighthouse CI threshold).
```

## Severity Classification
- **CRITICAL**: Blocks users from core functionality (keyboard users can't submit, screen readers can't navigate, main content invisible).
- **HIGH**: Significantly degrades experience (> 100ms jank, important features inaccessible, WCAG AA failures on key content).
- **MEDIUM**: Noticeable UX/a11y issues but workarounds exist (minor contrast issues, non-critical features keyboard-inaccessible).
- **MONITOR**: Best practice violations, edge cases, future risk areas.

---

## Accessibility Score Rubric (WCAG Compliance 1-10)

Rate overall accessibility based on severity/quantity of violations:
- **9-10**: WCAG 2.1 AA compliant; minor enhancements only.
- **7-8**: 1-2 high-priority fixes needed; mostly accessible.
- **5-6**: Multiple accessibility issues; significant remediation required.
- **3-4**: Major accessibility barriers; many users blocked.
- **<3**: Inaccessible to many user groups; fundamental redesign needed.

## Performance Score Rubric (Core Web Vitals 1-10)

Rate overall performance based on CWV metrics and React performance:
- **9-10**: All CWV in green; smooth 60fps interactions.
- **7-8**: CWV mostly green; occasional jank in complex interactions.
- **5-6**: Some CWV in yellow; noticeable performance issues.
- **3-4**: CWV in red; significant jank and delays.
- **<3**: Unusable performance; fundamental optimization needed.

---

## Include:
- Both scores (Accessibility + Performance)
- Brief justification for each (2-5 bullets)
- A prioritized Top 5 fixes list (highest impact first, balanced between a11y and performance)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production)
2) Fix Soon (next sprint)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated effort for all Fix Now items (t-shirt sizing: S/M/L/XL)
- Testing infrastructure to add:
  - Automated: Lighthouse CI, axe-core in Playwright, React Testing Library a11y queries
  - Manual: Keyboard navigation checklist, screen reader test script
  - Monitoring: Web Vitals RUM, error boundary reporting
- Recommended audit tools:
  - `npx lighthouse <url> --only-categories=accessibility,performance`
  - Chrome DevTools Performance panel for React profiling
  - axe DevTools browser extension
  - WAVE accessibility evaluation tool
  - NVDA (Windows) or VoiceOver (Mac) for screen reader testing
