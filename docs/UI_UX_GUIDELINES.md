# UI/UX Guidelines — Waste-IQ

> This document defines the design language, component standards, and interaction patterns for the Waste-IQ frontend. All contributors building UI features should read and follow these guidelines to maintain a consistent, accessible, and professional user experience.

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Color Palette](#2-color-palette)
3. [Status Color Mapping](#3-status-color-mapping)
4. [Typography](#4-typography)
5. [Icons](#5-icons)
6. [Spacing & Layout System](#6-spacing--layout-system)
7. [Responsive Design](#7-responsive-design)
8. [Component Standards](#8-component-standards)
9. [Accessibility Standards](#9-accessibility-standards)
10. [Page Templates](#10-page-templates)
11. [Naming Conventions](#11-naming-conventions)
12. [Animation & Motion](#12-animation--motion)

---

## 1. Design Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Clarity First** | Every screen should make it immediately obvious what the user can do next. Reduce cognitive load through hierarchy, white space, and progressive disclosure. |
| 2 | **Role-Specific UX** | Citizens, collectors, dealers, and admins have fundamentally different mental models. Each role receives a purpose-built dashboard — avoid one-size-fits-all interfaces. |
| 3 | **Consistency** | Use the same patterns, colors, and component variants for the same types of information everywhere. Predictability builds trust. |
| 4 | **Accessibility by Default** | Design for WCAG 2.1 AA from the start — not as an afterthought. Color is never the only means of conveying information. |
| 5 | **Performance Perception** | Use skeleton loaders, optimistic UI updates, and progressive loading to make the app feel fast even on slow connections. |

---

## 2. Color Palette

Waste-IQ uses a green-anchored palette that reinforces the environmental mission.

### Primary Colors

| Name | Hex | Tailwind Class | Usage |
|------|-----|----------------|-------|
| **Primary Green** | `#16a34a` | `green-600` | Primary action buttons, active nav items, success indicators |
| **Primary Dark** | `#15803d` | `green-700` | Hover state for primary elements |
| **Primary Light** | `#dcfce7` | `green-100` | Background tints, light badges, success alert backgrounds |
| **Primary Subtle** | `#f0fdf4` | `green-50` | Page section backgrounds, card highlights |

### Semantic Colors

| Name | Hex | Tailwind Class | Usage |
|------|-----|----------------|-------|
| **Accent Orange** | `#ea580c` | `orange-600` | Pending status, warnings, secondary CTAs |
| **Accent Orange Light** | `#ffedd5` | `orange-100` | Pending status badge background |
| **Info Blue** | `#2563eb` | `blue-600` | Accepted status, informational elements |
| **Info Blue Light** | `#dbeafe` | `blue-100` | Accepted status badge background |
| **Error Red** | `#dc2626` | `red-600` | Destructive actions, error states, cancelled status |
| **Error Red Light** | `#fee2e2` | `red-100` | Error alert backgrounds |
| **Purple** | `#9333ea` | `purple-600` | Collected status |
| **Purple Light** | `#f3e8ff` | `purple-100` | Collected status badge background |
| **Indigo** | `#4f46e5` | `indigo-600` | On-the-way status |
| **Indigo Light** | `#e0e7ff` | `indigo-100` | On-the-way status badge background |

### Neutral Grayscale

| Name | Hex | Tailwind Class | Usage |
|------|-----|----------------|-------|
| **Surface** | `#ffffff` | `white` | Card, modal, and input backgrounds |
| **Background** | `#f9fafb` | `gray-50` | Page background |
| **Border** | `#e5e7eb` | `gray-200` | Dividers, input borders, card borders |
| **Muted** | `#9ca3af` | `gray-400` | Placeholder text, disabled elements |
| **Secondary Text** | `#6b7280` | `gray-500` | Supporting copy, labels |
| **Body Text** | `#374151` | `gray-700` | Primary body copy |
| **Heading** | `#111827` | `gray-900` | Page titles, primary headings |

### Usage Rules

- Never use color as the **only** differentiator — always pair with an icon, label, or pattern.
- Minimum contrast ratio of **4.5:1** for normal text, **3:1** for large text (WCAG AA).
- In dark mode (if implemented): invert the neutral scale and reduce primary color saturation.

---

## 3. Status Color Mapping

All status badges must use these exact color classes for consistency.

### Pickup Request Status

| Status | Badge Background | Badge Text | Icon |
|--------|-----------------|------------|------|
| `pending` | `bg-orange-100` | `text-orange-700` | `Clock` |
| `accepted` | `bg-blue-100` | `text-blue-700` | `CheckCircle` |
| `on_the_way` | `bg-indigo-100` | `text-indigo-700` | `Truck` |
| `collected` | `bg-purple-100` | `text-purple-700` | `Package` |
| `completed` | `bg-green-100` | `text-green-700` | `CheckCircle2` |
| `cancelled` | `bg-red-100` | `text-red-700` | `XCircle` |

### Inventory Lot Status

| Status | Badge Background | Badge Text | Icon |
|--------|-----------------|------------|------|
| `available` | `bg-green-100` | `text-green-700` | `ShoppingBag` |
| `reserved` | `bg-yellow-100` | `text-yellow-700` | `Lock` |
| `sold` | `bg-gray-100` | `text-gray-600` | `Archive` |

### Dealer Verification Status

| Status | Badge Background | Badge Text | Icon |
|--------|-----------------|------------|------|
| `pending` | `bg-orange-100` | `text-orange-700` | `Clock` |
| `approved` | `bg-green-100` | `text-green-700` | `ShieldCheck` |
| `rejected` | `bg-red-100` | `text-red-700` | `ShieldX` |

---

## 4. Typography

Waste-IQ uses the system font stack for optimal performance and native rendering.

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
             "Helvetica Neue", Arial, "Noto Sans", sans-serif;
```

### Type Scale

| Element | Size | Weight | Tailwind | Usage |
|---------|------|--------|----------|-------|
| Page Title (h1) | 30px / 1.875rem | 700 Bold | `text-3xl font-bold` | One per page, main page heading |
| Section Title (h2) | 24px / 1.5rem | 600 SemiBold | `text-2xl font-semibold` | Card titles, section headings |
| Subsection (h3) | 20px / 1.25rem | 600 SemiBold | `text-xl font-semibold` | Sub-card headings |
| Body Large | 18px / 1.125rem | 400 Regular | `text-lg` | Lead paragraph, feature descriptions |
| Body Default | 16px / 1rem | 400 Regular | `text-base` | General body copy |
| Body Small | 14px / 0.875rem | 400 Regular | `text-sm` | Supporting text, table cells |
| Caption / Label | 12px / 0.75rem | 500 Medium | `text-xs font-medium` | Form labels, badges, helper text |
| Stat Number | 36px / 2.25rem | 700 Bold | `text-4xl font-bold` | Dashboard KPI numbers |
| Code | 14px / 0.875rem | 400 Regular | `text-sm font-mono` | Code snippets, lot numbers |

### Rules

- Use **one `<h1>` per page** — required for accessibility and SEO.
- Heading hierarchy must be logical: `h1 → h2 → h3` with no skipping levels.
- Line height for body text: `leading-relaxed` (1.625).
- Max line length for readable paragraphs: **65–75 characters** (`max-w-prose`).
- Do **not** use `font-black` (weight 900) — it is too heavy for the design.

---

## 5. Icons

Waste-IQ uses **[Lucide React](https://lucide.dev)** exclusively.

### Standard Sizes

| Context | Size Class | Pixel | Usage |
|---------|-----------|-------|-------|
| Inline text icon | `size-4` | 16px | Inside buttons, badges, table cells |
| Button icon | `size-5` | 20px | Icon-only buttons, icon+label buttons |
| Standalone / nav | `size-6` | 24px | Navigation items, standalone icons |
| Empty state | `size-12` | 48px | Empty state illustrations |
| Hero / feature | `size-16` | 64px | Feature section icons |

### Domain Icon Reference

| Concept | Icon Name | Usage |
|---------|----------|-------|
| Recyclable Waste | `Recycle` | App logo areas, empty state for pickups |
| Pickup Request | `Trash2` | Pickup-related actions and headings |
| Collector / Truck | `Truck` | Collector dashboard, on-the-way status |
| Scrap Dealer | `Store` | Dealer marketplace, dealer headings |
| Admin | `Shield` | Admin panel items |
| Municipality | `Building2` | Municipal features |
| Location / GPS | `MapPin` | Address fields, nearby requests |
| Weight | `Weight` | Weight fields in completion forms |
| Calendar / Date | `Calendar` | Date pickers, timestamps |
| Analytics | `BarChart3` | Admin analytics |
| User Profile | `UserCircle` | Profile section |
| Settings | `Settings` | Settings page |
| Notification | `Bell` | Notification badge |
| Search | `Search` | Search inputs |
| Filter | `SlidersHorizontal` | Filter dropdowns |
| Add / Create | `Plus` | Create new item buttons |
| Edit | `Pencil` | Edit action buttons |
| Archive | `Archive` | Archive/hide lot |
| Check / Done | `CheckCircle2` | Completed states |
| Cancel / Close | `XCircle` | Cancelled states, close buttons |
| Warning | `AlertTriangle` | Warning alerts |
| Info | `Info` | Informational tooltips |
| Logout | `LogOut` | Sign out button |

### Icon Rules

- Icons in buttons must have an accessible `aria-label` if no visible text label is present.
- Use `aria-hidden="true"` on purely decorative icons.
- **Never** use two different icons to represent the same concept within the same context.
- Icon color should inherit from the parent text color class — do not hard-code icon colors separately.

---

## 6. Spacing & Layout System

Waste-IQ uses **Tailwind's 4px spacing scale** consistently.

### Core Spacing Values

| Scale | px | rem | Usage |
|-------|-----|-----|-------|
| `space-1` | 4px | 0.25rem | Tight internal padding (badge padding) |
| `space-2` | 8px | 0.5rem | Icon-to-label gap, compact list gaps |
| `space-3` | 12px | 0.75rem | Form element internal padding |
| `space-4` | 16px | 1rem | Standard component padding |
| `space-6` | 24px | 1.5rem | Card internal padding |
| `space-8` | 32px | 2rem | Section spacing inside pages |
| `space-12` | 48px | 3rem | Major section separators |
| `space-16` | 64px | 4rem | Page-level top/bottom padding |

### Container & Max Widths

| Name | Max Width | Tailwind | Usage |
|------|-----------|----------|-------|
| Content | 1280px | `max-w-7xl` | Main page content wrapper |
| Dashboard | 1536px | `max-w-screen-2xl` | Wide dashboard tables |
| Form | 640px | `max-w-xl` | Single-column forms |
| Prose | 65ch | `max-w-prose` | Readable paragraphs |
| Modal | 480px | `max-w-lg` | Standard dialog width |

### Card Layout

Standard card anatomy:

```
┌─────────────────────────────────────────┐
│  p-6 (24px padding)                     │
│  ┌───────────────────────────────────┐  │
│  │ Card Header (flex, items-center)  │  │
│  │  Title (text-lg font-semibold)    │  │
│  │  Optional Action Button           │  │
│  └───────────────────────────────────┘  │
│  mt-4 divider or separator              │
│  Card Body (space-y-4 or grid)          │
│  ┌───────────────────────────────────┐  │
│  │ Content                           │  │
│  └───────────────────────────────────┘  │
│  mt-4                                   │
│  Card Footer (if applicable)            │
└─────────────────────────────────────────┘
  border border-gray-200 rounded-xl
  bg-white shadow-sm
```

---

## 7. Responsive Design

### Breakpoint System

Waste-IQ uses Tailwind's default breakpoints:

| Breakpoint | Min Width | Tailwind Prefix | Layout Behavior |
|------------|-----------|----------------|----------------|
| **xs** (default) | 0px | *(none)* | Single column, stacked layout |
| **sm** | 640px | `sm:` | 2-column grids, compact navigation |
| **md** | 768px | `md:` | Sidebar becomes visible, wider forms |
| **lg** | 1024px | `lg:` | Full desktop layout, multi-column grids |
| **xl** | 1280px | `xl:` | Wider content areas, 3-4 column grids |
| **2xl** | 1536px | `2xl:` | Very large screens, expanded tables |

### Layout Patterns per Breakpoint

| Component | Mobile | Tablet (md) | Desktop (lg+) |
|-----------|--------|-------------|---------------|
| Dashboard sidebar | Hidden (bottom nav or hamburger) | Fixed sidebar 240px | Fixed sidebar 256px |
| Stats grid | 1 column | 2 columns | 4 columns |
| Pickup request list | Cards (full width) | 2-column cards | Table view |
| Form layout | Single column | Single column | Two-column where appropriate |
| Navigation | Bottom tab bar or hamburger | Side navigation | Full side navigation |

### Mobile-First Rule

Always write mobile styles first, then add `md:` / `lg:` overrides:

```tsx
// ✅ Correct — mobile first
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

// ❌ Incorrect — desktop first
<div className="grid grid-cols-4 gap-6 lg:grid-cols-4 md:grid-cols-2 grid-cols-1">
```

---

## 8. Component Standards

### Buttons

Use shadcn/ui `Button` component with these variant standards:

| Variant | Tailwind / Variant | Usage |
|---------|-------------------|-------|
| **Primary** | `variant="default"` (green) | Main CTA — "Submit Request", "Accept", "Purchase" |
| **Secondary** | `variant="outline"` | Secondary actions — "View Details", "Edit" |
| **Destructive** | `variant="destructive"` (red) | Irreversible actions — "Cancel Request", "Reject" |
| **Ghost** | `variant="ghost"` | Subtle actions — navigation items, icon buttons |
| **Link** | `variant="link"` | Inline text links |

**Button sizes:**

| Size | Class | Usage |
|------|-------|-------|
| Small | `size="sm"` | Compact table actions |
| Default | `size="default"` | Standard buttons |
| Large | `size="lg"` | Primary CTA on landing/auth pages |
| Icon | `size="icon"` | Square icon-only buttons |

**Rules:**
- Every button that triggers a network request must show a **loading spinner** while pending.
- Destructive actions must be preceded by a **confirmation dialog**.
- Disabled buttons must have `aria-disabled="true"` and a clear visual state.
- Loading buttons must be `disabled` and show an accessible spinner.

```tsx
// Loading button pattern
<Button disabled={isLoading}>
  {isLoading ? (
    <><Loader2 className="size-4 mr-2 animate-spin" /> Submitting...</>
  ) : (
    "Submit Request"
  )}
</Button>
```

---

### Form Fields

All form fields follow this anatomy:

```
Label (text-sm font-medium text-gray-700)
  ↕ gap-1.5
Input / Select / Textarea
  └─ border border-gray-300 rounded-md px-3 py-2
  └─ focus:ring-2 focus:ring-green-500 focus:border-transparent
  └─ placeholder:text-gray-400
  ↕ gap-1
Helper Text (text-xs text-gray-500) [optional]
Error Message (text-xs text-red-600 flex items-center gap-1)
  └─ <AlertCircle className="size-3" /> [error message text]
```

- Labels are always **above** inputs, never floating.
- Required fields are marked with a red asterisk: `<span className="text-red-500">*</span>`
- Form validation runs **on blur** for individual fields; full validation on submit.
- Error messages appear **below** the field, never as alerts.

---

### Status Badges

```tsx
// Standard status badge
<span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
  <CheckCircle2 className="size-3" />
  Completed
</span>
```

Always use the status color mapping from [Section 3](#3-status-color-mapping).

---

### Data Tables

| Aspect | Standard |
|--------|----------|
| Border | `border border-gray-200 rounded-xl overflow-hidden` |
| Header | `bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider` |
| Row | `bg-white hover:bg-gray-50 transition-colors` |
| Row divider | `divide-y divide-gray-200` |
| Cell padding | `px-6 py-4` |
| Sort indicator | Use `ArrowUpDown` / `ArrowUp` / `ArrowDown` Lucide icons |
| Empty state | Centered cell spanning all columns — use [Empty State](#empty-states) pattern |

---

### Empty States

Every list or table must have an empty state:

```
     [Icon - size-12 text-gray-300]
     [Title - text-lg font-medium text-gray-900]
     [Description - text-sm text-gray-500 max-w-sm mx-auto]
     [CTA Button - mt-4]
```

Example:
```tsx
<div className="text-center py-16">
  <Recycle className="size-12 mx-auto text-gray-300 mb-4" />
  <h3 className="text-lg font-medium text-gray-900">No pickup requests yet</h3>
  <p className="text-sm text-gray-500 mt-1 max-w-sm mx-auto">
    Schedule your first pickup and start contributing to a greener city.
  </p>
  <Button className="mt-4" onClick={onCreateNew}>
    <Plus className="size-4 mr-2" />
    New Pickup Request
  </Button>
</div>
```

---

### Skeleton Loaders

Use skeleton loaders (animated pulse placeholders) instead of spinners for **content areas**. Reserve spinners for **button loading states** only.

```tsx
// Skeleton card
<div className="animate-pulse space-y-4">
  <div className="h-4 bg-gray-200 rounded w-3/4" />
  <div className="h-4 bg-gray-200 rounded w-1/2" />
  <div className="h-10 bg-gray-200 rounded" />
</div>
```

---

### Toast Notifications

Use the shadcn/ui `Toast` / `Toaster` component with these conventions:

| Type | Variant | Title Pattern | Icon |
|------|---------|--------------|------|
| Success | `default` with green | "Request submitted", "Profile saved" | `CheckCircle2` |
| Error | `destructive` | "Something went wrong", "Action failed" | `XCircle` |
| Info | `default` | "Reservation expires in 2 hours" | `Info` |

- Toast duration: **4000ms** for success/info, **6000ms** for errors.
- Toast position: **bottom-right** on desktop, **bottom-center** on mobile.
- Maximum 3 toasts visible simultaneously.

---

### Confirmation Dialogs

Use the shadcn/ui `AlertDialog` for destructive actions:

```
  Title: "Cancel Pickup Request?"
  Description: "This action cannot be undone. Your request will be permanently cancelled."
  [Cancel Button - ghost]  [Confirm Button - destructive]
```

---

## 9. Accessibility Standards

Waste-IQ targets **WCAG 2.1 AA** compliance.

### Requirements

| Requirement | Standard | Implementation |
|-------------|----------|----------------|
| **Color Contrast** | 4.5:1 (normal text), 3:1 (large text) | Verified against primary palette |
| **Keyboard Navigation** | All interactive elements reachable by Tab | Use Radix UI primitives (inherently accessible) |
| **Focus Indicators** | Visible focus ring on all focusable elements | `focus-visible:ring-2 focus-visible:ring-green-500` |
| **Screen Reader Labels** | All interactive elements labeled | `aria-label`, `aria-labelledby`, or visible label |
| **Form Errors** | Errors programmatically linked to inputs | `aria-describedby` on invalid inputs |
| **Images** | All meaningful images have alt text | `alt=""` for decorative images |
| **Heading Hierarchy** | Single `<h1>`, logical nesting | Enforced per page template |
| **Live Regions** | Dynamic content announced to screen readers | `aria-live="polite"` on status updates |
| **Motion** | Animations respect `prefers-reduced-motion` | Framer Motion's `reducedMotion` prop |

### Focus Ring Standard

```tsx
// Apply to all interactive elements
className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-2"
```

### ARIA Patterns

```tsx
// Icon-only button
<Button size="icon" aria-label="Cancel pickup request">
  <XCircle className="size-5" aria-hidden="true" />
</Button>

// Status badge (decorative icon)
<span role="status" aria-label="Status: Completed">
  <CheckCircle2 className="size-3" aria-hidden="true" />
  Completed
</span>

// Loading state
<Button disabled aria-busy="true" aria-label="Submitting request">
  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
  Submitting...
</Button>
```

---

## 10. Page Templates

### Dashboard Page Layout

```
┌───────────────────────────────────────────────────────────┐
│  Sidebar (fixed, 256px)   │  Main Content                 │
│  ─────────────────────    │  ──────────────────────────── │
│  Logo                     │  Page Header                  │
│  ─────────────────────    │    h1 Title + optional CTA    │
│  Nav Items                │  ─────────────────────────── │
│    Dashboard (active)     │  Stats Grid (4-col on lg)     │
│    My Requests            │  ─────────────────────────── │
│    Profile                │  Content Section              │
│    Settings               │    Table / Card List          │
│  ─────────────────────    │  ─────────────────────────── │
│  User info + Logout       │  Pagination (if applicable)   │
└───────────────────────────────────────────────────────────┘
```

### List Page Layout

```
Page Header
  ├── h1 Title
  └── Create Button (top-right)

Filter Bar (bg-white border rounded-lg px-4 py-3)
  ├── Search Input
  ├── Status Filter Dropdown
  └── Date Range Picker (if applicable)

Content Area
  ├── Loading State → SkeletonTable
  ├── Empty State → EmptyState component
  └── Data Table / Card Grid

Pagination (bottom, centered)
```

### Detail Page Layout

```
Breadcrumb: Dashboard > My Requests > Request #42

Page Header (flex justify-between)
  ├── h1: "Pickup Request #42"
  └── Action Buttons (Cancel, Edit)

Content Grid (lg:grid-cols-3 gap-6)
  ├── Main Column (lg:col-span-2)
  │   ├── Details Card
  │   └── Image Card (if applicable)
  └── Sidebar Column (lg:col-span-1)
      ├── Status Card (status badge + timeline)
      └── Assignment Card (collector info)
```

### Form Page Layout

```
Page Header
  └── h1: "New Pickup Request"

Form Card (max-w-2xl mx-auto)
  └── Card body
      ├── Form Section 1: Waste Details
      │   ├── waste_type field
      │   └── image upload
      ├── Divider
      ├── Form Section 2: Location
      │   ├── address field
      │   └── latitude / longitude (hidden or map picker)
      └── Form Footer
          ├── Cancel Button (ghost)
          └── Submit Button (primary, full-width on mobile)
```

### Auth Page Layout

```
Full-height centered layout (min-h-screen flex items-center justify-center)

  Logo + App Name (centered, mb-8)

  Auth Card (w-full max-w-md)
    ├── Card Header: "Sign in to Waste-IQ"
    ├── Card Body: Form Fields
    └── Card Footer: Switch to Register / Forgot Password
```

---

## 11. Naming Conventions

### Files and Directories

| Type | Convention | Example |
|------|-----------|---------|
| React Components | `PascalCase.tsx` | `PickupRequestCard.tsx` |
| Page Components | `PascalCase + Page.tsx` | `DashboardOverviewPage.tsx` |
| Custom Hooks | `use + PascalCase.ts` | `usePickupRequests.ts` |
| Utility Functions | `camelCase.ts` | `formatCurrency.ts` |
| Type Definitions | `camelCase.types.ts` or `types.ts` | `pickup.types.ts` |
| API Functions | `camelCase.api.ts` | `pickupRequests.api.ts` |
| Context | `PascalCase + Context.tsx` | `AuthContext.tsx` |
| Constants | `SCREAMING_SNAKE_CASE` in file | `STATUS_COLORS`, `ROLES` |

### Component Props

```tsx
// Props interface: ComponentName + Props
interface PickupStatusBadgeProps {
  status: PickupStatus;
  className?: string;
}

// Use className for style overrides — never hardcode final styling in reusable components
```

### Test IDs

All interactive elements in reusable components must include a `data-testid` attribute:

```tsx
<Button data-testid="pickup-submit-btn">Submit Request</Button>
<input data-testid="pickup-waste-type-input" />
<div data-testid="pickup-status-badge" />
```

Convention: `<component>-<element>-<type>` in kebab-case.

### CSS Class Ordering

Follow Tailwind CSS class ordering:
1. Layout (`flex`, `grid`, `block`)
2. Position (`relative`, `absolute`)
3. Box Model (`w-`, `h-`, `p-`, `m-`)
4. Typography (`text-`, `font-`, `leading-`)
5. Visual (`bg-`, `border-`, `rounded-`, `shadow-`)
6. Interactive (`hover:`, `focus:`, `active:`)
7. Responsive (`sm:`, `md:`, `lg:`)

Use [prettier-plugin-tailwindcss](https://github.com/tailwindlabs/prettier-plugin-tailwindcss) to enforce this automatically.

---

## 12. Animation & Motion

Waste-IQ uses **Framer Motion** for component-level animations.

### Standard Animations

| Animation | Use Case | Duration |
|-----------|----------|----------|
| Fade in | Page transitions, modal open | 200ms |
| Slide up | Card entrance, drawer open | 300ms |
| Fade + scale | Status badge updates | 150ms |
| Stagger children | List item entrance | 50ms between items |
| Pulse (Tailwind) | Skeleton loaders | CSS animation |
| Spin (Tailwind) | Loading spinners | CSS animation |

### Animation Presets

```tsx
// Fade in (use for page content)
const fadeIn = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.2, ease: "easeOut" }
};

// Stagger children (use for lists)
const staggerContainer = {
  animate: { transition: { staggerChildren: 0.05 } }
};

const staggerItem = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 }
};
```

### Reduced Motion

**Always** respect `prefers-reduced-motion`:

```tsx
import { useReducedMotion } from "framer-motion";

const prefersReducedMotion = useReducedMotion();

<motion.div
  animate={{ opacity: 1, y: prefersReducedMotion ? 0 : undefined }}
/>
```

### Rules

- Avoid animations longer than **400ms** — they feel sluggish.
- Never animate **layout shifts** (width/height changes) — use opacity and transform only.
- Keep animations **purposeful** — they should communicate state changes, not just look nice.
- Avoid **looping animations** unless they convey real-time activity (e.g., a loading indicator).
