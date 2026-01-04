# Code Unification & Consistency Audit Prompt
## For AI-Generated ("Vibecoded") Codebases

---

## Role
Act as a Senior Frontend Architect and Code Quality Engineer. Perform a comprehensive Code Unification & Consistency Audit on the provided codebase to identify fragmentation, duplication, and styling inconsistencies that typically emerge from multi-session AI-assisted development.

## Primary Goal
Find where AI-generated code has created parallel implementations, inconsistent patterns, and styling drift—then provide a consolidation roadmap that creates a unified, maintainable codebase while preserving functionality.

## Context
- This codebase was developed across multiple AI coding sessions ("vibecoded")
- Each session may have created its own components, utilities, and patterns
- A UI Kit (Tailwind-based) exists in the root directory as the intended design system
- The goal is NOT to rewrite everything, but to identify consolidation opportunities with highest ROI

## Tech Stack (adjust based on your actual stack)
- Frontend: React (functional components, hooks)
- Styling: Tailwind CSS + [UI Kit Name]
- Backend: Node.js / Express
- State Management: (infer from code - React Query, Redux, Context, Zustand, etc.)
- API Layer: (infer - fetch, axios, custom wrapper)

## How to Provide Code
I will paste/upload the codebase. Analyze ALL provided files systematically.
Pay special attention to:
- `/components` - Look for duplicates and near-duplicates
- `/pages` or `/app` - Each page may have inline components that should be extracted
- `/utils` or `/lib` - Utility function duplication
- `/hooks` - Custom hooks that do similar things
- `/styles` - Any CSS files, Tailwind config, theme files
- `/api` or `/services` - API calling patterns
- **UI Kit root directory** - This is the SOURCE OF TRUTH for component styling
- **package.json** - Identify redundant dependencies (e.g., two icon libraries, two date libraries, axios AND fetch wrappers, multiple form libraries)
- **Hardcoded strings throughout** - Scan for hardcoded API endpoints, URLs, "magic numbers", credentials, and values that should be environment variables or constants
- `/types` or `/interfaces` (TypeScript) - Look for duplicate type definitions across files

---

## Scope Boundaries & File Accounting (Mandatory)

### Exclusions (Skip These Unless Explicitly Included)
The following directories are OUT OF SCOPE by default:
- `/node_modules` - Third-party packages
- `/dist`, `/build`, `/.next`, `/out` - Build output
- `/coverage` - Test coverage reports
- `/.git` - Version control
- Generated files: `*.min.js`, `*.bundle.js`, `*.generated.ts`
- Lock files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- Vendored code: `/vendor`, `/third-party`

### Required Coverage Report
At the START of your audit, provide a file accounting summary:

```
=== AUDIT SCOPE ===

Scanned:
| Directory          | File Count | Types                    |
|--------------------|------------|--------------------------|
| /src/components    | 47         | .jsx, .tsx               |
| /src/pages         | 12         | .jsx                     |
| /src/hooks         | 8          | .ts                      |
| /src/utils         | 15         | .ts, .js                 |
| /src/api           | 6          | .ts                      |
| /ui-kit            | 23         | .jsx                     |
| Root config files  | 5          | .js, .json               |
| TOTAL              | 116 files  |                          |

Skipped (out of scope):
| Directory          | Reason                              |
|--------------------|-------------------------------------|
| /node_modules      | Third-party (default exclusion)     |
| /.next             | Build output (default exclusion)    |
| /coverage          | Test reports (default exclusion)    |

Potentially Missed (flagged for review):
| Directory          | Why Flagged                         |
|--------------------|-------------------------------------|
| /scripts           | Exists but not provided - may contain build/deploy logic |
| /middleware        | Exists but empty or not provided    |
```

**If any application code appears to be missing, explicitly ask:** "I don't see `/middleware` or `/config` directories. Should I analyze those?"

---

## Pre-Audit: Environment & Pattern Inference (Do This First)

Before auditing, infer and document:

### 1) UI Kit Analysis
- What components does the UI Kit provide? (Button, Modal, Card, Input, etc.)
- What's the styling convention? (CSS variables, Tailwind theme tokens, etc.)
- What color palette/spacing scale is defined?
- Are there variant patterns? (size="sm|md|lg", variant="primary|secondary")

### 2) Current Codebase Patterns (Infer from code)
- Component naming convention (PascalCase, kebab-case files, etc.)
- State management approach(es) in use
- API calling pattern(s) in use
- Form handling approach(es)
- Error handling pattern(s)
- Loading state pattern(s)

### 3) Create a Pattern Inventory Table
```
| Pattern Type      | Variations Found | Files Using Each | Recommended Standard |
|-------------------|------------------|------------------|---------------------|
| API Calls         | fetch, axios     | list files...    | TBD                 |
| Form Validation   | yup, zod, manual | list files...    | TBD                 |
| Button Component  | 3 versions       | list files...    | UI Kit Button       |
| etc.              |                  |                  |                     |
```

---

## PART 1: Component Duplication Audit

### A) Exact & Near-Duplicate Components

**What to Find:**
- Components with similar names (Button, CustomButton, PrimaryButton, ActionButton)
- Components with different names but same functionality (Modal, Dialog, Popup, Overlay)
- Components that are copy-pasted with minor variations
- Inline components in pages that should be extracted and shared

**AI-Generated Code Red Flags:**
- Same component created fresh in each session because context was lost
- Slightly different prop interfaces for identical components
- Components that wrap the same UI Kit component with minor additions

**Output Format:**
```
DUPLICATE GROUP: [Semantic Name, e.g., "Button Components"]

Instances Found:
1. /components/Button.jsx (45 lines)
2. /components/ui/CustomButton.tsx (52 lines)
3. /pages/Dashboard.jsx lines 15-35 (inline)
4. /components/forms/SubmitButton.jsx (38 lines)

Similarity Analysis:
- All render a <button> with Tailwind classes
- #1 and #2 are 85% identical (diff: #2 adds loading state)
- #3 is a subset of #1
- #4 wraps #1 with form-specific logic

UI Kit Equivalent: /ui-kit/components/Button.jsx
- Supports: size, variant, loading, disabled, icon
- Missing from UI Kit: [list any gaps]

Consolidation Recommendation:
- KEEP: UI Kit Button as base
- EXTEND: Add loading state if missing from UI Kit
- MIGRATE: All 4 instances → single Button component
- EFFORT: ~2 hours

Code Changes Required:
[Show the unified component API and migration example]
```

### B) Component Prop Interface Inconsistencies

**What to Find:**
- Same conceptual prop with different names (isLoading vs loading vs showLoader)
- Same component with different prop interfaces in different files
- Boolean props with inconsistent patterns (disabled vs isDisabled)

**Output Format:**
```
PROP INCONSISTENCY: [Component Type]

Variations:
| File                  | Loading Prop    | Size Prop      | Click Handler |
|-----------------------|-----------------|----------------|---------------|
| Button.jsx            | isLoading       | size="sm|md"   | onClick       |
| CustomButton.tsx      | loading         | btnSize        | onPress       |
| SubmitButton.jsx      | showSpinner     | (none)         | onSubmit      |

Recommended Standard (based on UI Kit / React conventions):
- loading: boolean (matches UI Kit)
- size: "sm" | "md" | "lg" (matches UI Kit)  
- onClick: () => void (React standard)

Migration Impact: 12 files need prop renames
```

---

## PART 2: Styling Consistency Audit

### A) Color Usage Fragmentation

**What to Find:**
- Raw hex/rgb values instead of Tailwind theme tokens
- Inconsistent color token usage (text-blue-500 vs text-primary)
- Colors that don't match UI Kit palette
- Inline styles that should be Tailwind classes

**Scan For:**
```
# Hex/RGB literals (should be theme tokens)
/#[0-9a-fA-F]{3,6}/
/rgb\(|rgba\(/
/style={{.*color.*}}/

# Inconsistent blue usage (example)
/text-blue-\d00/  vs  /text-primary/
/bg-blue-\d00/    vs  /bg-primary/
```

**Output Format:**
```
COLOR INCONSISTENCY: Blue/Primary

UI Kit Definition: 
- primary: #3B82F6 (blue-500 equivalent)
- primary-dark: #2563EB (blue-600)

Usage in Codebase:
| Pattern          | Count | Files                    | Should Be      |
|------------------|-------|--------------------------|----------------|
| text-blue-500    | 23    | file1, file2, ...        | text-primary   |
| text-blue-600    | 8     | file3, file4, ...        | text-primary-dark |
| #3B82F6 inline   | 5     | file5 (line 42), ...     | text-primary   |
| bg-[#3B82F6]     | 2     | file6, file7             | bg-primary     |

Fix Approach:
1. Add to tailwind.config.js if missing:
   colors: { primary: '#3B82F6', 'primary-dark': '#2563EB' }
2. Find/replace: text-blue-500 → text-primary (23 occurrences)
3. Remove inline hex values

Automated Fix Command:
[Provide sed/grep commands or codemod suggestion]
```

### B) Spacing & Layout Inconsistencies

**What to Find:**
- Arbitrary spacing values (p-[13px] vs p-3)
- Inconsistent gap/margin patterns for similar components
- Mixed spacing scales (some use 4px base, some use 8px)

**Output Format:**
```
SPACING INCONSISTENCY: Card Padding

Pattern Variations Found:
| Component      | Padding Used | 
|----------------|--------------|
| Card.jsx       | p-4          |
| ProductCard    | p-6          |
| UserCard       | px-4 py-3    |
| DashboardCard  | p-[18px]     |

UI Kit Standard: p-4 (16px)

Recommendation: Standardize all cards to p-4 or create size variants
```

### C) Typography Inconsistencies

**What to Find:**
- Headings with inconsistent sizes (text-xl in one place, text-2xl in another for same purpose)
- Font weight inconsistencies
- Line height mismatches

---

## PART 3: UI Kit Utilization Audit

### A) Unused UI Kit Components

**What to Find:**
- UI Kit provides a component, but codebase has custom implementation
- UI Kit component is imported but custom CSS overrides everything

**Output Format:**
```
UNDERUTILIZED UI KIT COMPONENT: Modal

UI Kit Provides: /ui-kit/components/Modal.jsx
- Features: overlay, close button, sizes, animations, portal rendering

Codebase Custom Implementations:
1. /components/CustomModal.jsx - Reimplements 90% of UI Kit Modal
2. /components/Dialog.jsx - Uses HTML <dialog>, missing accessibility
3. /pages/Settings.jsx - Inline modal (lines 120-180)

Recommendation:
- DELETE: CustomModal.jsx, Dialog.jsx
- MIGRATE: All usages to UI Kit Modal
- EXTEND UI Kit: Add [any missing features] via wrapper if needed
- EFFORT: ~3 hours
```

### B) UI Kit Gaps Analysis

**What to Find:**
- Components the codebase needs that UI Kit doesn't provide
- Functionality added to UI Kit components via wrappers everywhere

**Output Format:**
```
UI KIT GAP: DataTable Component

Codebase Implementations:
1. /components/Table.jsx
2. /components/DataGrid.jsx  
3. /pages/Admin/UserTable.jsx (inline, 200 lines)

Common Features Needed:
- Sorting (all 3 implement differently)
- Pagination (2 of 3 have it)
- Row selection (1 of 3)
- Loading skeleton (0 of 3)

UI Kit Status: No table component

Recommendation:
- CREATE: /components/ui/DataTable.jsx as unified component
- BASE ON: Best implementation (#1 Table.jsx)
- ADD: Missing features from #2 and #3
- EFFORT: ~4 hours
```

---

## PART 4: Backend Pattern Audit

### A) API Response Format Inconsistencies

**What to Find:**
- Different response structures across endpoints
- Inconsistent error response formats
- Mixed patterns for pagination, metadata

**Output Format:**
```
API RESPONSE INCONSISTENCY

Variations Found:
| Endpoint           | Success Format              | Error Format           |
|--------------------|-----------------------------|------------------------|
| GET /users         | { data: [...] }             | { error: "msg" }       |
| GET /products      | { products: [...] }         | { message: "msg" }     |
| POST /orders       | { order: {...}, success: true } | { success: false, error: "msg" } |

Recommended Standard:
{
  success: boolean,
  data: T | null,
  error: { code: string, message: string } | null,
  meta: { page, total, ... } // for lists
}

Files to Update: [list with line numbers]
```

### B) Validation Pattern Inconsistencies

**What to Find:**
- Different validation libraries (Joi, Yup, Zod, manual)
- Validation in controllers vs middleware vs both
- Inconsistent error message formats

### C) Database Query Pattern Inconsistencies

**What to Find:**
- Raw SQL mixed with ORM calls
- Different patterns for same operations (findOne vs find(...).limit(1))
- Transaction handling inconsistencies

### D) Environment Variable & Configuration Consistency

**What to Find:**
- Hardcoded URLs, API endpoints, or keys in some files vs `process.env` in others
- Magic numbers scattered throughout (timeouts, limits, thresholds)
- Configuration values duplicated across files
- Missing `.env.example` documentation

**Output Format:**
```
CONFIGURATION INCONSISTENCY: API Base URLs

Variations Found:
| File                    | How Base URL is Set                    |
|-------------------------|----------------------------------------|
| /services/userApi.js    | const BASE = 'https://api.example.com' |
| /services/orderApi.js   | process.env.API_URL                    |
| /lib/fetch.js           | 'http://localhost:3001'                |
| /hooks/useProducts.js   | '/api' (relative, assumes proxy)       |

Other Hardcoded Values Found:
| Value      | Location              | Should Be                |
|------------|-----------------------|--------------------------|
| 30000      | timeout in 5 files    | process.env.API_TIMEOUT  |
| 50         | pagination limit      | config.DEFAULT_PAGE_SIZE |
| 'sk_live_' | stripe key inline     | process.env.STRIPE_KEY   |

Recommendation:
1. Create /config/index.js to centralize all configuration
2. Move all hardcoded values to .env
3. Create .env.example with all required variables documented

Example Config Pattern:
// /config/index.js
export const config = {
  api: {
    baseUrl: process.env.API_URL || 'http://localhost:3001',
    timeout: parseInt(process.env.API_TIMEOUT) || 30000,
  },
  pagination: {
    defaultLimit: parseInt(process.env.DEFAULT_PAGE_SIZE) || 50,
  },
};
```

---

## PART 5: State Management & Data Flow Audit

### A) State Management Fragmentation

**What to Find:**
- Multiple state management solutions in same app
- Same data fetched and stored in multiple places
- Prop drilling when context exists for that data

**Output Format:**
```
STATE MANAGEMENT FRAGMENTATION

Current State Solutions:
| Solution       | Used For              | Files Using |
|----------------|-----------------------|-------------|
| Redux          | User auth only        | 3 files     |
| React Query    | Products, Orders      | 8 files     |
| useState       | Everything else       | 45 files    |
| Context        | Theme                 | 2 files     |

Issues:
1. User data fetched 4 different ways in 4 files
2. Redux installed but barely used (consider removing)
3. Same product data re-fetched in sibling components

Recommendation:
1. Standardize on React Query for all server state
2. Remove Redux, use Context for auth state
3. Create shared query hooks (/hooks/useUser, /hooks/useProducts)
```

### B) API Calling Pattern Inconsistencies

**What to Find:**
- fetch vs axios usage
- Different base URL handling
- Inconsistent header/auth token attachment
- Error handling variations

**Output Format:**
```
API CALLING FRAGMENTATION

Patterns Found:
| Pattern                      | Count | Files                |
|------------------------------|-------|----------------------|
| Raw fetch                    | 12    | page1, page2, ...    |
| Axios (new instance each time)| 8    | service1, service2   |
| Axios (shared instance)      | 3     | api.js usage         |
| React Query + fetch          | 5     | hooks/...            |

Issues:
1. Auth token attached manually in 15 places
2. Base URL hardcoded in 8 places
3. Error handling reimplemented everywhere

Recommended Standard:
- Single API client (/lib/api.js) with interceptors
- All calls go through React Query hooks
- Centralized error handling

Migration Example:
[Show before/after code]
```

---

## PART 6: Naming Convention Audit

### A) File Naming Inconsistencies

**What to Find:**
- Mixed conventions (PascalCase.jsx, kebab-case.tsx, camelCase.js)
- Inconsistent suffixes (.component.tsx, .jsx, .tsx mixed)

### B) Function/Variable Naming Inconsistencies

**What to Find:**
- Same concept, different names (getUser, fetchUser, loadUser, retrieveUser)
- Boolean naming (isLoading, loading, showLoader)
- Handler naming (handleClick, onClick, onClickHandler, clickHandler)

---

## PART 7: Utility & Helper Function Audit

### A) Duplicate Utility Functions

**What to Find:**
- formatDate, formatCurrency, etc. implemented multiple times
- Same validation functions in multiple files
- API helpers duplicated

**Output Format:**
```
DUPLICATE UTILITY: Date Formatting

Implementations Found:
1. /utils/date.js - formatDate(date, format)
2. /helpers/index.js - dateFormatter(date)
3. /pages/Orders.jsx - inline function (line 23)
4. /components/Timeline.jsx - inline function (line 45)

Functionality Comparison:
| Function        | Supports Locale | Relative Time | Used By |
|-----------------|-----------------|---------------|---------|
| formatDate      | Yes             | No            | 5 files |
| dateFormatter   | No              | Yes           | 3 files |
| Inline #3       | No              | No            | 1 file  |
| Inline #4       | No              | Yes           | 1 file  |

Consolidation:
- KEEP: /utils/date.js
- ENHANCE: Add relative time support
- DELETE: Other 3 implementations
- MIGRATE: 4 files to use consolidated util
```

---

## PART 8: Architecture & Type Safety Audit

### A) Dependency Overlap & Bloat

**What to Find:**
- Multiple libraries doing the same job installed via different AI sessions
- Unused dependencies (installed but never imported)
- Dev dependencies in production bundle

**Common Overlaps to Scan For:**
```
| Category        | Look For These Combinations                    |
|-----------------|------------------------------------------------|
| HTTP Clients    | axios + node-fetch + got + ky                  |
| Date Libraries  | moment + date-fns + dayjs + luxon              |
| Icon Libraries  | lucide-react + react-icons + @heroicons + fontawesome |
| Form Libraries  | react-hook-form + formik + final-form          |
| Validation      | yup + zod + joi + superstruct                  |
| State Mgmt      | redux + zustand + jotai + recoil               |
| CSS-in-JS       | styled-components + emotion + stitches         |
| Animation       | framer-motion + react-spring + animejs         |
| UUID Generation | uuid + nanoid + cuid                           |
| Lodash          | lodash + underscore + ramda (or lodash + individual lodash/* packages) |
```

**Output Format:**
```
DEPENDENCY OVERLAP: Date Libraries

package.json Contains:
- "moment": "^2.29.4" (498KB)
- "date-fns": "^2.30.0" (75KB) 
- "dayjs": "^1.11.9" (6KB)

Usage Analysis:
| Library   | Import Count | Files Using          |
|-----------|--------------|----------------------|
| moment    | 12           | mostly older files   |
| date-fns  | 8            | newer components     |
| dayjs     | 2            | /utils/calendar.js   |

Recommendation:
- KEEP: date-fns (best tree-shaking, most flexible)
- REMOVE: moment (largest, deprecated for new projects)
- REMOVE: dayjs (barely used)
- MIGRATE: 14 files to date-fns
- BUNDLE SAVINGS: ~450KB

Migration Guide:
| moment                          | date-fns equivalent           |
|---------------------------------|-------------------------------|
| moment().format('YYYY-MM-DD')   | format(new Date(), 'yyyy-MM-dd') |
| moment(date).fromNow()          | formatDistanceToNow(date)     |
| moment(date).add(1, 'days')     | addDays(date, 1)              |
```

### B) Unused Dependencies

**How to Find:**
```bash
# Use depcheck to find unused dependencies
npx depcheck

# Or manually grep for imports
for pkg in $(cat package.json | jq -r '.dependencies | keys[]'); do
  count=$(grep -r "from ['\"]$pkg" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" | wc -l)
  echo "$pkg: $count imports"
done
```

**Output Format:**
```
UNUSED DEPENDENCIES

Likely Unused (0 imports found):
- classnames (0 imports) - maybe replaced by clsx?
- react-helmet (0 imports) - leftover from previous approach?
- lodash (0 imports) - individual lodash/* used instead?

Low Usage (1-2 imports, consider inlining):
- left-pad (1 import) - just use String.padStart()
- is-even (1 import) - really?
```

### C) Type/Interface Duplication (TypeScript Projects)

**What to Find:**
- Same entity type defined in multiple files with slight variations
- Inline type definitions that should be shared
- `any` types used as shortcuts
- Inconsistent naming (User vs UserType vs IUser vs UserDTO)

**Output Format:**
```
TYPE DUPLICATION: User Entity

Definitions Found:
| File                      | Type Name  | Fields                              |
|---------------------------|------------|-------------------------------------|
| /types/user.ts            | User       | id, name, email, role               |
| /api/types.ts             | UserDTO    | id, name, email, role, createdAt    |
| /components/Profile.tsx   | IUser      | id, name, email (inline)            |
| /hooks/useAuth.ts         | UserType   | id, username, email, permissions    |
| /pages/Admin.tsx          | (inline)   | { id: number; name: string; }       |

Field Comparison:
| Field       | user.ts | api/types | Profile | useAuth | Admin |
|-------------|---------|-----------|---------|---------|-------|
| id          | number  | number    | number  | string  | number|
| name        | string  | string    | string  | -       | string|
| username    | -       | -         | -       | string  | -     |
| email       | string  | string    | string  | string  | -     |
| role        | string  | string    | -       | -       | -     |
| permissions | -       | -         | -       | string[]| -     |
| createdAt   | -       | Date      | -       | -       | -     |

Issues:
1. id is string in useAuth, number everywhere else
2. name vs username inconsistency
3. 3 of 5 definitions are inline (should be imported)

Recommendation:
1. Create canonical types in /types/entities/user.ts:
   - User (base fields all agree on)
   - UserWithMeta (adds createdAt, updatedAt)
   - UserPermissions (for auth context)
2. Delete all inline definitions
3. Migrate all files to import from /types

Canonical Type:
// /types/entities/user.ts
export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
}

export interface UserWithMeta extends User {
  createdAt: Date;
  updatedAt: Date;
}

export type UserRole = 'admin' | 'user' | 'guest';
```

### D) `any` Type Abuse (TypeScript)

**What to Find:**
- Explicit `any` types (shortcuts from AI sessions)
- `@ts-ignore` comments hiding type issues
- Implicit `any` from missing return types

**How to Scan:**
```bash
# Find explicit any
grep -r ": any" --include="*.ts" --include="*.tsx" | wc -l

# Find ts-ignore
grep -r "@ts-ignore\|@ts-expect-error" --include="*.ts" --include="*.tsx"

# Find implicit any (requires tsconfig strict mode)
```

**Output Format:**
```
TYPE SAFETY ISSUES

Explicit `any` Usage: 47 occurrences
| File                    | Line | Context                          |
|-------------------------|------|----------------------------------|
| /api/client.ts          | 23   | response: any                    |
| /hooks/useData.ts       | 15   | data: any[]                      |
| /utils/transform.ts     | 8    | (item: any) =>                   |
...

@ts-ignore Comments: 12 occurrences
| File                    | Line | Reason (if commented)            |
|-------------------------|------|----------------------------------|
| /components/Chart.tsx   | 45   | // @ts-ignore library types wrong|
| /pages/Dashboard.tsx    | 102  | // @ts-ignore TODO fix later     |
...

Recommendation:
1. Enable strict mode in tsconfig.json (catches implicit any)
2. Address top 10 `any` usages in core files first
3. Create proper types for API responses
4. Replace @ts-ignore with @ts-expect-error + explanation
```

---

## OUTPUT FORMAT (Mandatory for Each Issue)

```
[PRIORITY: CRITICAL | HIGH | MEDIUM | LOW]
[CATEGORY: Component | Styling | Pattern | Naming | Utility | State | API | Architecture | Types]
[EFFORT: XS (<30min) | S (1-2hr) | M (2-4hr) | L (4-8hr) | XL (1+ day)]

Issue: [Clear title]

What Was Found:
- List the specific instances/files
- Show the variations

Why It Matters:
- Maintenance burden (N files to update for changes)
- Bug risk (inconsistent behavior)
- Developer confusion (which pattern to use?)
- Bundle size (duplicate code)

UI Kit Alignment:
- Does UI Kit provide a solution? (Yes/No)
- What does UI Kit offer?
- Gap between UI Kit and current implementations

The Fix:
- Specific consolidation steps
- Show unified component/function
- List files that need migration
- Provide find/replace patterns or codemod suggestions

Trade-offs:
- Time investment vs payoff
- Risk of breaking changes
- Dependencies on other fixes
```

### Migration Safety Checklist (Required for HIGH/CRITICAL Issues)

For every HIGH or CRITICAL priority fix, include this safety section:

```
=== MIGRATION SAFETY ===

Risk Level: [LOW | MEDIUM | HIGH]
- Low: Isolated change, easy to verify, no runtime behavior change
- Medium: Multiple files affected, some behavior change, testable
- High: Core component, breaking API change, affects many flows

Verification Commands:
# Run these BEFORE merging
npm run typecheck        # (or: npx tsc --noEmit)
npm run lint             # Catch import errors
npm run test             # Existing tests pass
npm run test:affected    # If available

Manual Spot-Checks:
- [ ] [Page/Flow 1]: Verify [specific behavior]
- [ ] [Page/Flow 2]: Verify [specific behavior]
- [ ] Check console for warnings/errors

Rollback Plan:
- Git: `git revert <commit>` (if single commit)
- Or: Restore files [list specific files]
- Recovery time estimate: [X minutes]

Migration Order (if multi-step):
1. [First change - lowest risk]
2. [Second change - depends on #1]
3. [Third change - final step]

Feature Flag Option (if high risk):
- Can this be behind a flag? [Yes/No]
- Suggested flag: `USE_NEW_BUTTON_COMPONENT`
```

**Example for a real issue:**
```
=== MIGRATION SAFETY ===

Risk Level: MEDIUM
- Affects 23 files but props are compatible
- No breaking API change (old props still work)

Verification Commands:
npm run typecheck        # Verify import paths resolve
npm run lint
npm run test -- --grep="Button"

Manual Spot-Checks:
- [ ] Homepage: Hero CTA button still works
- [ ] Checkout: Submit order button loading state
- [ ] Dashboard: All action buttons render

Rollback Plan:
- Git: Single commit, `git revert HEAD`
- Recovery time: 2 minutes

Migration Order:
1. Update import paths (no behavior change)
2. Remove old Button.jsx file
3. Update any custom props to standard props
```

---

## PRIORITY CLASSIFICATION

- **CRITICAL**: Core components used 10+ places, high divergence, affects entire app UX consistency
- **HIGH**: Used 5-10 places, noticeable inconsistency, moderate effort to fix
- **MEDIUM**: Used 3-5 places, worth fixing but not urgent
- **LOW**: 1-2 places, can fix opportunistically

---

## CONSISTENCY SCORE RUBRIC (1-10)

Rate the codebase's current consistency:

- **9-10**: Minor inconsistencies, well-structured, clear patterns
- **7-8**: Some duplication and drift, 2-3 patterns to consolidate
- **5-6**: Significant fragmentation, multiple implementations of core components
- **3-4**: Heavy duplication, no clear patterns, UI Kit underutilized
- **<3**: Each file is an island, complete rewrite may be faster than consolidation

---

## FINAL REPORT STRUCTURE (Mandatory)

### 0) Audit Scope Summary (First)
- Files scanned (count by directory)
- Files skipped (with reasons)
- Any potentially missed directories

### 1) Executive Summary
- Overall consistency score with justification
- Total duplicates found by category
- UI Kit utilization percentage
- Estimated total cleanup effort

### 2) Component Consolidation Map
```
[Unified Component]     [Replace These]           [Effort] [Risk]
───────────────────────────────────────────────────────────────────
ui/Button               Button, CustomBtn, ...    2h       LOW
ui/Modal                Modal, Dialog, Popup      3h       MED
ui/Card                 Card, Box, Container      1h       LOW
... etc
```

### 3) Pattern Standardization Checklist
```
[ ] API calling → React Query + /lib/api.js
[ ] Form handling → React Hook Form + Zod
[ ] Error handling → ErrorBoundary + toast
[ ] Loading states → Skeleton components
... etc
```

### 4) Styling Cleanup Checklist
```
[ ] Replace hex colors with theme tokens (X occurrences)
[ ] Standardize spacing on cards (X components)
[ ] Align typography scale (X files)
... etc
```

### 5) Prioritized Action Plan

**Phase 1: Quick Wins (Do First)**
- Items with HIGH impact, LOW effort
- Fixes that unblock other fixes

**Phase 2: Core Consolidation**
- Major component unification
- Pattern standardization

**Phase 3: Polish**
- Naming conventions
- Minor inconsistencies

### 6) Automated Fixable Items
Provide copy-paste commands for mechanical fixes:
```bash
# Color standardization
find . -name "*.jsx" -exec sed -i 's/text-blue-500/text-primary/g' {} \;

# Import consolidation
# ...etc
```

### 7) Recommended Tooling
- ESLint rules to prevent future drift
- Prettier config for formatting
- Husky pre-commit hooks
- Component documentation (Storybook?)

### 8) Verification Gate Checklist (Before Merging Any Fix)
```bash
# === RUN AFTER EACH MIGRATION ===

# Type safety (TypeScript projects)
npm run typecheck || npx tsc --noEmit

# Linting (catches bad imports, unused vars)
npm run lint

# Tests
npm run test

# Build verification (catches missing exports)
npm run build

# Optional: Bundle size check
npx bundlesize  # or: npx size-limit
```

**Per-fix verification:** Each HIGH/CRITICAL fix should list specific UI flows to manually verify (see Migration Safety Checklist format above).

---

## IMPORTANT NOTES FOR THE AI AGENT

1. **UI Kit is Source of Truth** - Always recommend UI Kit components over custom implementations when they exist

2. **Don't Recommend Rewrites** - Goal is consolidation, not rewriting. Find the best existing implementation and migrate others to it

3. **Golden-Path Decision Rule (Use This Hierarchy)**
   When multiple implementations exist and you must choose a standard, use this priority order:
   ```
   1. UI Kit component (if exists and sufficient)
      ↓ if not available
   2. Most-used implementation (adoption = less migration work)
      ↓ if tie
   3. Most-correct implementation (a11y, TypeScript types, tests, error handling)
      ↓ if tie
   4. Most-performant implementation (bundle size, render efficiency)
      ↓ if still tied
   5. Implementation closest to UI Kit conventions (naming, props, structure)
   ```
   **Always state which criterion determined your choice.** Example: "Recommending `Button.jsx` as standard: UI Kit doesn't have Button, and Button.jsx has highest usage (23 imports vs 8 for CustomButton)."

4. **Be Specific** - "Button is duplicated" is useless. "Button.jsx, CustomButton.tsx, and inline button in Dashboard.jsx lines 45-52 should consolidate to UI Kit Button" is useful

5. **Show the Unified API** - When consolidating, show what the final component interface should look like

6. **Provide Migration Paths** - Don't just say "fix it." Show the before/after and list affected files

7. **Consider Dependencies** - Note when Fix A must happen before Fix B

8. **Respect What Works** - If a custom implementation is BETTER than UI Kit, recommend enhancing UI Kit, not downgrading to it