# AI AGENT CODEBASE STRUCTURE GUIDE
## Instructions for AI Coding Agents During Project Planning and Development

> **PURPOSE**: This document provides structured instructions for AI coding agents to follow when planning, creating, or refactoring a codebase. Follow these rules systematically.

---

## HOW TO USE THIS GUIDE

| Scenario | Action |
|----------|--------|
| **New project setup** | Follow sections 1-3 as templates |
| **Auditing existing project** | Compare against sections 1-3, report discrepancies to user |
| **Pre-implementation checkpoint** | Review section 4.2 |
| **Planning non-trivial work** | Follow section 5.3 protocol |
| **Troubleshooting** | Use section 12 diagnostic |

### Quick Navigation
| Section | Purpose |
|---------|---------|
| 1. Core Principles | Mandatory rules (always apply) |
| 2. Project Templates | Structure references (new projects) or audit baselines |
| 3. AI Instructions File | Setup template |
| 4. Checklists | Pre/post implementation verification |
| 5. AI Strengths | Task delegation guidance |
| 6. AI Limitations | Self-awareness and mitigation |
| 7. Error Handling | Standards template (compare with existing) |
| 8. Testing Standards | Standards template (compare with existing) |
| 9. Documentation | Requirements template (compare with existing) |
| 10. Quick Reference | Fast lookups |
| 11. Final Reminders | Session workflow |
| 12. Diagnostic | Troubleshooting |

---

## SECTION 1: CORE PRINCIPLES (ALWAYS APPLY)

### 1.1 Foundational Rules

```
RULE: Keep files small and focused
- TARGET: 200-300 lines per file (optimal for AI context)
- HARD CAP: 500 lines (split if exceeded)
- One primary responsibility per file
- AI agents work better with smaller context windows
- Smaller files = fewer hallucinations and better code quality

EXCEPTIONS (may exceed 300, but still cap at 500):
- Test files with many test cases
- Configuration files
- Type definition files with many interfaces
- Generated files (but prefer splitting if possible)

RULE: Use descriptive, consistent naming
- Files: kebab-case or snake_case (pick one, be consistent)
- Functions/methods: camelCase or snake_case (language-appropriate)
- Classes: PascalCase
- Constants: SCREAMING_SNAKE_CASE
- Names should describe WHAT, not HOW

RULE: Flat over nested structure
- Maximum 3-4 levels of directory nesting
- Deep nesting makes navigation painful for both humans and AI
- If you can't find a file in 3 clicks, restructure
- EXCEPTION: Feature module boundaries (e.g., src/features/auth/components/) 
  may add one extra level - this is acceptable for organization

RULE: Zero new dependencies without approval
- Do NOT add packages to package.json, requirements.txt, Cargo.toml, etc.
- Before suggesting any install, check what's already available:
  * Read package.json/requirements.txt for existing dependencies
  * Check lockfiles (package-lock.json, yarn.lock, poetry.lock)
  * Search existing imports in codebase for similar functionality
  * Verify if native/built-in solutions exist (e.g., fetch vs axios)
- If a new dependency is truly needed, ASK for human approval first
- AI agents frequently hallucinate helpful libraries that aren't needed

RULE: Co-locate related files
- Tests next to source files (file.ts → file.test.ts)
- Styles next to components
- Types/interfaces with their implementations
```

### 1.2 The DRY Principle (Critical for AI Agents)

```
WARNING: AI agents often duplicate code accidentally

BEFORE writing new code, ALWAYS:
1. Search the codebase for similar functionality
2. Check if utility functions exist
3. Look for shared components/modules
4. Fix existing code instead of adding new duplicated code

INSTRUCTION: When asked to add functionality:
- First grep/search for similar patterns
- Apply the "Rule of Three": Refactor to shared function when pattern exists 3+ times
  (Note: Some teams use 2+ to be more conservative with AI-generated code)
- Add to existing module rather than creating new file

ANTI-PATTERN: Creating new utility files when shared/utils already has similar functions
```

### 1.3 Separation of Concerns

```
STRUCTURE each module/feature with clear layers:

├── feature/
│   ├── components/     # UI components (if applicable)
│   ├── hooks/          # Custom hooks/state logic
│   ├── services/       # API calls, external integrations
│   ├── utils/          # Pure utility functions
│   ├── types/          # TypeScript types/interfaces
│   ├── constants/      # Static values, configs
│   └── index.ts        # Public API exports

NEVER mix:
- Business logic with UI rendering
- Data fetching with data transformation
- Configuration with implementation
```

### 1.4 State Management Strategy (Frontend Projects)

```
AI agents often struggle with state management decisions.
Follow this hierarchy:

FIRST: Use whatever state management the project already uses.
Check package.json for: Redux, Zustand, Pinia, MobX, Jotai, Recoil, etc.
Do NOT introduce a new state library if one exists.

LEVEL 1: Local State (useState/reactive/ref)
- Default choice for component-specific data
- Use when only the component and direct children need the value

LEVEL 2: Lifted State (props)
- When parent and 1-2 children need shared state
- Acceptable prop drilling depth: maximum 2 levels

LEVEL 3: Global State (project's existing state manager)
- ONLY when a value is needed by 3+ non-child components
- Use the project's designated state manager
- Do NOT create new Context providers for small features

RULE: Start local, escalate only when necessary
- AI agents tend to prop-drill until unreadable OR jump to global too early
- Ask: "How many unrelated components need this data?"
- If answer is < 3, keep it local or lifted
```

---

## SECTION 2: PROJECT STRUCTURE TEMPLATES

> **USAGE MODE:**
> - **New project**: Use these as starting templates
> - **Existing project**: Compare structure, report significant deviations to user for decision. Do NOT refactor to match without approval.

### 2.1 Small Project (< 10 files)

```
project/
├── src/
│   ├── main.ts              # Entry point
│   ├── config.ts            # Configuration
│   ├── types.ts             # Shared types
│   └── utils.ts             # Utility functions
├── tests/
│   └── main.test.ts
├── README.md
├── package.json             # or requirements.txt, Cargo.toml, etc.
└── .gitignore
```

### 2.2 Medium Project (10-50 files)

```
project/
├── src/
│   ├── index.ts             # Entry point
│   ├── config/
│   │   ├── index.ts
│   │   └── constants.ts
│   ├── features/
│   │   ├── auth/
│   │   │   ├── auth.service.ts
│   │   │   ├── auth.types.ts
│   │   │   └── auth.test.ts
│   │   └── users/
│   │       ├── users.service.ts
│   │       ├── users.types.ts
│   │       └── users.test.ts
│   ├── shared/
│   │   ├── utils/
│   │   ├── types/
│   │   └── constants/
│   └── infrastructure/
│       ├── database/
│       ├── logging/
│       └── http/
├── docs/
│   ├── ARCHITECTURE.md
│   └── API.md
├── README.md
└── package.json
```

**VISUAL: Flat vs Nested Structure**

```
❌ BAD: Deep Nesting (6+ levels)
src/modules/features/user/management/profile/settings/theme.ts
     1      2       3    4          5        6       7

✅ GOOD: Flat Structure (3-4 levels max)
src/features/user/profile-settings.ts
     1        2     3         (file)

RULE: If path has more than 4 slashes, restructure.
```

**VISUAL: Data Flow in Medium Project**

```
┌─────────────────────────────────────────────────────────────┐
│                        Entry Point                          │
│                       (src/index.ts)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Config  │    │ Features │    │  Shared  │
    │          │    │          │    │          │
    │ constants│    │ ┌──────┐ │    │  utils   │
    │ env vars │    │ │ auth │ │    │  types   │
    └──────────┘    │ ├──────┤ │    │  errors  │
                    │ │users │ │    └──────────┘
                    │ └──────┘ │          ▲
                    └────┬─────┘          │
                         │                │
                         └────────────────┘
                         (features import shared)
```

### 2.3 Large Project (50+ files)

```
project/
├── apps/                    # If monorepo
│   ├── web/
│   ├── api/
│   └── mobile/
├── packages/                # Shared packages
│   ├── ui/
│   ├── utils/
│   └── types/
├── src/                     # If not monorepo
│   ├── modules/             # Feature modules
│   │   ├── auth/
│   │   ├── billing/
│   │   └── notifications/
│   ├── core/                # Core infrastructure
│   │   ├── database/
│   │   ├── cache/
│   │   └── queue/
│   ├── shared/              # Shared utilities
│   └── config/
├── docs/
│   ├── ARCHITECTURE.md      # CRITICAL: Keep updated
│   ├── llms.txt             # AI-friendly documentation
│   └── decisions/           # ADRs (Architecture Decision Records)
├── scripts/
└── README.md
```

---

## SECTION 3: AI AGENT INSTRUCTIONS FILE (CREATE THIS FIRST)

### 3.1 Required: Create an AI Instructions File

```markdown
# FILE: .cursor/rules/project.mdc OR .cursorrules OR AGENTS.md OR llms.txt

## Project Overview
[Brief description of what this project does]

## Technology Stack
- Language: [e.g., TypeScript 5.x]
- Framework: [e.g., Next.js 14]
- Database: [e.g., PostgreSQL with Prisma]
- Testing: [e.g., Vitest + Testing Library]

## Directory Structure
[Copy your actual structure with explanations]

## Code Conventions
- Naming: [your conventions]
- File organization: [your patterns]
- Import order: [your preferences]

## DO NOT
- [ ] Do not use deprecated APIs (list them)
- [ ] Do not add dependencies without approval
- [ ] Do not modify files in /generated or /vendor
- [ ] Do not hardcode secrets or API keys
- [ ] Do not create files longer than 500 lines (target 200-300)

## ALWAYS
- [ ] Add types for all function parameters and returns
- [ ] Write tests for new functionality
- [ ] Use existing utility functions before creating new ones
- [ ] Follow error handling patterns in /src/shared/errors
- [ ] Update documentation when changing public APIs

## Common Patterns
[Include code examples for your project's patterns]

## Known Issues / Gotchas
[Document things that trip up AI agents]
```

### 3.2 Template: llms.txt File

```markdown
# [Project Name]

> LLM-friendly documentation for AI coding assistants

## Quick Start
[One-paragraph description]

## Architecture
[High-level overview with ASCII diagram if helpful]

## Key Files
- `/src/index.ts` - Application entry point
- `/src/config/` - All configuration
- `/src/modules/` - Feature modules
- `/src/shared/` - Shared utilities

## API Patterns
[Show example of how to create new endpoints/features]

## Testing
[Show example test structure]

## Common Tasks
### Adding a new feature
1. Create module in `/src/modules/[feature-name]/`
2. Add types in `[feature-name].types.ts`
3. Add service in `[feature-name].service.ts`
4. Add tests in `[feature-name].test.ts`
5. Export from `index.ts`

### Adding a new API endpoint
[Steps specific to your project]
```

---

## SECTION 4: CHECKLISTS

### 4.1 Pre-Project Checklist

```
BEFORE starting any new project:

□ Define the technology stack
□ Create directory structure skeleton
□ Set up AI instructions file (.cursorrules, AGENTS.md, or llms.txt)
□ Configure linting and formatting tools
□ Set up version control with .gitignore
□ Create README.md with project overview
□ Set up test framework
□ Define naming conventions
□ Create shared types file
□ Set up environment configuration pattern
```

### 4.2 New Feature Checklist

```
BEFORE implementing any new feature:

□ Search codebase for similar existing functionality
□ Check if shared utilities can be reused
□ Review existing patterns in similar modules
□ Plan file structure (target 200-300 lines, max 500 per file)
□ Define types/interfaces first
□ Identify what tests are needed

AFTER implementing:

□ Verify no code duplication was introduced
□ Ensure all functions have proper types
□ Write or update tests
□ Update documentation if public API changed
□ Check file sizes (split if > 500 lines, consider splitting > 300)
□ Verify consistent naming
```

### 4.3 Code Quality Checklist

```
BEFORE submitting any code:

□ All files under 500 lines (ideally under 300)
□ Functions under 50 lines
□ No hardcoded values (use constants)
□ No commented-out code
□ No console.log/print debugging statements
□ Error handling in place
□ Types defined for all parameters and returns
□ Tests written and passing
□ No duplicate code
□ Imports organized consistently
```

---

## SECTION 5: WHAT AI AGENTS DO WELL

### 5.1 Tasks to Delegate to AI

```
OPTIMAL AI TASKS:

✓ Boilerplate generation
  - CRUD operations
  - API endpoint scaffolding
  - Test file creation
  - Type definitions from examples

✓ Pattern replication
  - "Create X similar to Y"
  - Extending existing modules
  - Adding fields to existing types

✓ Code transformations
  - Refactoring to new patterns
  - Converting between syntaxes
  - Adding TypeScript types to JavaScript

✓ Small, focused tasks
  - Single function implementation
  - Bug fixes with clear reproduction
  - Adding tests for existing code
  - Documentation generation

✓ Repetitive tasks
  - Creating multiple similar components
  - Batch file renaming/restructuring
  - Adding logging/error handling consistently
```

### 5.2 Effective Prompting Patterns

```
GOOD PROMPT STRUCTURE:

1. Context: "In this Next.js 14 project using App Router..."
2. Reference: "Following the pattern in /src/modules/users/..."
3. Specific task: "Create a new module for 'products' that..."
4. Constraints: "Keep each file under 200 lines, use existing shared utilities"
5. Output format: "Create these files: products.types.ts, products.service.ts, products.test.ts"

EXAMPLE EFFECTIVE PROMPT:
"Looking at /src/modules/users/ as a reference, create a new 'products' 
module following the same structure. It needs:
- ProductType with id, name, price, description
- ProductService with CRUD operations using our existing /shared/database client
- Tests following our Vitest patterns
Use existing utilities from /shared/utils. Keep files under 200 lines."
```

### 5.3 MANDATORY: Plan-Before-Action Handshake

```
CRITICAL RULE: Never start writing code immediately for non-trivial tasks.

BEFORE writing any code for a new feature or significant change:

1. OUTPUT an "Implementation Plan" containing:
   □ Files to be created (with paths)
   □ Files to be modified (with paths)
   □ Files to be deleted (if any)
   □ Dependencies required (if any - requires approval)
   □ Estimated complexity (simple/medium/complex)
   □ Potential risks or concerns

2. WAIT for human "Go" / approval

3. ONLY THEN begin implementation

EXAMPLE IMPLEMENTATION PLAN:
"""
## Implementation Plan: Add Products Module

### Files to Create:
- /src/modules/products/products.types.ts (define Product interface)
- /src/modules/products/products.service.ts (CRUD operations)
- /src/modules/products/products.test.ts (unit tests)
- /src/modules/products/index.ts (exports)

### Files to Modify:
- /src/modules/index.ts (add products export)

### Dependencies: None (using existing database client)

### Complexity: Simple

### Risks: None identified

Awaiting approval to proceed.
"""

WHY THIS MATTERS:
- Prevents large-scale refactoring disasters
- Catches architectural misunderstandings early
- Allows human to redirect before wasted effort
- Creates documentation of intent
```

---

## SECTION 6: WHAT AI AGENTS STRUGGLE WITH (AVOID OR SUPERVISE)

### 6.1 Known AI Agent Limitations

```
LIMITATIONS - REQUIRE HUMAN OVERSIGHT:

✗ Large-scale refactoring
  - AI loses context across many files
  - Errors compound across changes
  - Break into small, testable chunks instead

✗ Security-sensitive code
  - Authentication implementations
  - Input validation/sanitization
  - API key/secret handling
  - AI often uses outdated or insecure patterns

✗ Complex architectural decisions
  - System design trade-offs
  - Scalability considerations
  - Database schema design

✗ Long context tasks
  - Changes spanning 10+ files
  - Understanding entire large codebase
  - Session context is limited

✗ Edge cases and error handling
  - AI optimizes for happy path
  - Often misses failure scenarios
  - Needs explicit prompting for edge cases

✗ Staying current
  - May use deprecated APIs
  - May not know latest SDK versions
  - Always specify versions explicitly
```

### 6.2 Mitigation Strategies

```
FOR LARGE REFACTORS:
- Break into batches of 3-5 file changes
- Test each batch before proceeding
- Provide explicit file list for each batch

FOR SECURITY CODE:
- Always specify: "ensure authentication, validate inputs, prevent injection"
- Run security scans on AI-generated code
- Never skip human review

FOR CONTEXT LIMITS:
- Keep prompts focused on 1-3 files
- Reference specific files by path
- Don't assume AI remembers previous conversation

FOR EDGE CASES:
- Explicitly request: "Handle error cases including: [list cases]"
- Ask for: "What edge cases should we consider?"
- Review error handling paths manually

FOR CURRENT APIs:
- Specify versions: "Using React 18, Next.js 14, TypeScript 5.3"
- Include: "Do NOT use deprecated methods"
- Provide correct examples when known
```

### 6.3 Patterns That Cause AI Failures

```
AVOID THESE PATTERNS:

✗ Vague prompts
  BAD: "Add login"
  GOOD: "Add login using our existing AuthService in /src/services/auth.ts, 
         following the pattern in /src/pages/signup.tsx"

✗ Multi-step tasks without checkpoints
  BAD: "Build the entire checkout flow"
  GOOD: "First, create the cart types and service. 
         After I review, we'll add the UI."

✗ Assuming context from previous sessions
  BAD: "Continue where we left off"
  GOOD: "In /src/modules/orders/orders.service.ts, add the getOrderById method"

✗ No file size constraints
  BAD: "Create the user management module"
  GOOD: "Create user management with separate files for types, service, 
         and controller. Keep each under 200 lines."

✗ No pattern references
  BAD: "Add a new API endpoint"
  GOOD: "Add a new API endpoint following the pattern in 
         /src/routes/users.ts, using our standard error handling"
```

---

## SECTION 7: ERROR HANDLING STANDARDS

> **USAGE MODE:**
> - **New project**: Implement this pattern as the standard
> - **Existing project**: If project has established error handling, document differences and ask user which to follow. Prefer existing patterns unless explicitly asked to standardize.

### 7.1 Required Error Handling Pattern

```typescript
// ALWAYS use this pattern for error handling

// 1. Define custom error types
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'AppError';
  }
}

// 2. Use early returns for error conditions
function processOrder(order: Order): Result {
  // Guard clauses first
  if (!order) {
    throw new AppError('Order is required', 'MISSING_ORDER', 400);
  }
  if (!order.items?.length) {
    throw new AppError('Order must have items', 'EMPTY_ORDER', 400);
  }
  
  // Happy path last
  return calculateTotal(order);
}

// 3. Wrap external calls
async function fetchUser(id: string): Promise<User> {
  try {
    const response = await api.get(`/users/${id}`);
    return response.data;
  } catch (error) {
    throw new AppError(
      `Failed to fetch user ${id}`,
      'USER_FETCH_FAILED',
      502
    );
  }
}
```

---

## SECTION 8: TESTING STANDARDS

> **USAGE MODE:**
> - **New project**: Implement this structure as the standard
> - **Existing project**: If project has established test patterns, follow those. Report deviations and let user decide whether to standardize.

### 8.1 Required Test Structure

```typescript
// ALWAYS follow this test structure

describe('ModuleName', () => {
  // Setup
  beforeEach(() => {
    // Reset state
  });

  describe('functionName', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      const input = createTestInput();
      
      // Act
      const result = functionName(input);
      
      // Assert
      expect(result).toEqual(expectedOutput);
    });

    it('should throw error when [error condition]', () => {
      // Test error cases explicitly
      expect(() => functionName(invalidInput)).toThrow('Expected error');
    });

    it('should handle edge case: [description]', () => {
      // Explicitly test edge cases
    });
  });
});
```

### 8.2 Test Coverage Requirements

```
MINIMUM TEST COVERAGE:

□ Every public function must have at least one test
□ Error paths must be tested
□ Edge cases must be documented and tested:
  - Empty inputs
  - Null/undefined values
  - Boundary values
  - Invalid types (if applicable)
□ Integration points must have tests
```

---

## SECTION 9: DOCUMENTATION REQUIREMENTS

> **USAGE MODE:**
> - **New project**: Create these documentation files
> - **Existing project**: Audit against this list, report missing items to user. Do NOT create documentation without approval.

### 9.1 Required Documentation Files

```
EVERY PROJECT MUST HAVE:

□ README.md
  - Project description
  - Setup instructions
  - Usage examples
  - Contributing guidelines

□ ARCHITECTURE.md (for projects > 20 files)
  - System overview
  - Directory structure explanation
  - Data flow diagrams
  - Key decisions

□ llms.txt or AGENTS.md
  - AI-friendly project summary
  - Key patterns and conventions
  - Things to avoid
  - Common tasks with examples

□ CHANGELOG.md
  - Version history
  - Breaking changes
  - Migration guides

□ MEMORY.md (Recommended for multi-session projects)
  - Living document updated by AI agent
  - Logs what was completed in current session
  - Lists immediate next steps
  - Records recent decisions and their rationale
  - Acts as a "save game" for the next AI session
  
  MEMORY.md TEMPLATE:
  """
  # Session Memory
  
  ## Last Updated: [Date/Time]
  
  ## Completed This Session:
  - [x] Added products module with CRUD operations
  - [x] Fixed authentication bug in /src/auth/login.ts
  
  ## In Progress:
  - [ ] Adding unit tests for products.service.ts (70% done)
  
  ## Next Steps:
  1. Complete products tests
  2. Add products API endpoints
  3. Update API documentation
  
  ## Recent Decisions:
  - Chose Zustand over Context for cart state (needed in 4+ components)
  - Using zod for validation (already in project dependencies)
  
  ## Blockers/Questions:
  - Need clarification on product pricing structure
  """
```

### 9.2 Cursor-Specific: MDC Files with Globs

```
FOR CURSOR USERS:

.cursor/rules/*.mdc files support glob patterns to save context window space.

Instead of applying all rules to all files, scope rules to relevant files:

EXAMPLE: backend-rules.mdc
---
description: Backend API conventions
globs: src/api/**/*.ts, src/services/**/*.ts
alwaysApply: false
---
[rules for backend code only]

EXAMPLE: react-rules.mdc
---
description: React component conventions  
globs: src/components/**/*.tsx, src/pages/**/*.tsx
alwaysApply: false
---
[rules for React components only]

BENEFITS:
- Reduces token usage significantly
- Rules only load when working on relevant files
- Cleaner separation of concerns in AI instructions
```

### 9.3 Code Documentation Standards

```typescript
/**
 * FUNCTION DOCUMENTATION FORMAT:
 * 
 * Brief description of what the function does.
 * 
 * @param paramName - Description of parameter
 * @returns Description of return value
 * @throws {ErrorType} When error condition occurs
 * 
 * @example
 * const result = functionName(input);
 */
function functionName(paramName: Type): ReturnType {
  // Implementation
}

// INLINE COMMENTS:
// - Explain WHY, not WHAT
// - Document non-obvious business logic
// - Reference tickets/issues for complex workarounds

// BAD: Increment counter
counter++;

// GOOD: Increment retry counter (max 3 attempts per rate limit policy)
counter++;
```

---

## SECTION 10: QUICK REFERENCE

### 10.1 File Naming Conventions

```
NAMING PATTERNS:

Components:     UserProfile.tsx, OrderCard.tsx
Services:       user.service.ts, order.service.ts
Types:          user.types.ts, order.types.ts
Tests:          user.service.test.ts, UserProfile.test.tsx
Utilities:      format-date.ts, validate-email.ts
Constants:      api-endpoints.ts, error-codes.ts
Hooks:          use-user.ts, use-orders.ts
Config:         database.config.ts, auth.config.ts
```

### 10.2 Import Order Standard

```typescript
// IMPORT ORDER (enforce with linter):

// 1. External packages
import React from 'react';
import { z } from 'zod';

// 2. Internal absolute imports
import { Button } from '@/components/ui';
import { useAuth } from '@/hooks';

// 3. Relative imports
import { UserCard } from './UserCard';
import { formatUser } from './utils';

// 4. Types (if separate)
import type { User } from './types';

// 5. Styles (if applicable)
import styles from './styles.module.css';
```

### 10.3 Git Commit Convention

```
COMMIT MESSAGE FORMAT:

type(scope): brief description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance

Examples:
feat(auth): add password reset flow
fix(orders): handle empty cart edge case
docs(readme): update installation steps
refactor(users): extract validation logic
```

---

## SECTION 11: FINAL REMINDERS FOR AI AGENTS

```
BEFORE EVERY TASK:
1. Read the AI instructions file (.cursorrules, AGENTS.md, llms.txt)
2. Check MEMORY.md for recent context (if exists)
3. Search for existing similar code
4. Review referenced patterns
5. **FOR NON-TRIVIAL TASKS: Output Implementation Plan and WAIT for approval**
6. Confirm understanding before large changes

DURING IMPLEMENTATION:
1. Keep files small (target 200-300 lines, max 500)
2. Follow existing patterns exactly
3. Add types to everything
4. Include error handling
5. Write tests
6. Do NOT add new dependencies without approval

AFTER IMPLEMENTATION:
1. Verify no duplication introduced
2. Check all files are under size limit
3. Ensure tests pass
4. Update MEMORY.md with what was completed
5. Update documentation if needed
6. Self-review for security issues

WHEN STUCK OR UNCERTAIN:
- Ask for clarification rather than assume
- Break large tasks into smaller chunks
- Reference specific files and patterns
- Test incrementally, not at the end
- Output your plan and wait for feedback

THE GOLDEN RULE:
Plan → Approve → Implement → Test → Document
Never skip the approval step for anything beyond trivial changes.
```

---

## SECTION 12: QUICK DIAGNOSTIC CHECKLIST

```
USE THIS WHEN SOMETHING GOES WRONG:

□ Did I read the project's AI instructions file?
□ Did I check MEMORY.md for recent context?
□ Did I search for existing code before writing new code?
□ Did I output an Implementation Plan for non-trivial work?
□ Did I wait for approval before making large changes?
□ Are all my files under 500 lines (ideally under 300)?
□ Did I use existing dependencies instead of adding new ones?
□ Did I follow the patterns in referenced files exactly?
□ Did I handle error cases, not just the happy path?
□ Did I update MEMORY.md after completing work?

IF ERRORS KEEP OCCURRING:
1. Stop and re-read the full context
2. Check if you're modifying the right files
3. Verify you're using the correct API versions
4. Ask the human for clarification
5. Break the task into smaller pieces
```

---

*Last updated: December 2025*
*For AI coding agents: Parse this document completely before beginning any project planning or coding task.*