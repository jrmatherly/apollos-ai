# Component Map Reference

Complete mapping of UI components, their Alpine.js stores, and styling patterns.

## Component Tree

```
index.html
├── sidebar/left-sidebar.html          → sidebar-store.js
│   ├── sidebar/top-section/
│   │   ├── header-icons.html          (toggle btn + logo)
│   │   ├── sidebar-top.html           (quick-actions bar)
│   │   └── quick-actions.html         (home/agents/history/settings/more)
│   ├── sidebar/org-team-switcher.html  (org/team context)
│   ├── sidebar/chats/chats-list.html  → chats-store.js
│   ├── sidebar/tasks/tasks-list.html  → tasks-store.js
│   └── sidebar/bottom/
│       ├── sidebar-bottom.html        → sidebar-bottom-store.js
│       └── preferences/
│           ├── preferences-panel.html (theme/dark/width/detail/speech/utils)
│           └── preferences-store.js
├── welcome/welcome-screen.html        → welcome-store.js
├── chat/
│   ├── input/chat-bar.html            → input-store.js (glass input section)
│   ├── top-section/chat-top.html      → chat-top-store.js
│   ├── speech/                        → speech-store.js
│   ├── navigation/                    → chat-navigation-store.js
│   ├── message-queue/                 → message-queue-store.js
│   └── attachments/                   → attachmentsStore.js
├── messages/
│   ├── process-group/                 (process-group-dom.js, process-group.css)
│   ├── action-buttons/               (simple-action-buttons.js)
│   └── resize/                        → message-resize-store.js
├── modals/
│   ├── file-browser/                  → file-browser-store.js
│   ├── file-editor/                   → file-editor-store.js
│   ├── history/                       → history-store.js
│   ├── memory/                        → memory-dashboard-store.js
│   ├── scheduler/                     → scheduler-store.js
│   ├── context/                       → context-store.js
│   ├── image-viewer/                  → image-viewer-store.js
│   ├── full-screen-input/             → full-screen-store.js
│   └── process-step-detail/           → step-detail-store.js
├── settings/
│   ├── settings.html                  → settings-store.js
│   ├── agent/                         (model config, memory, workdir)
│   ├── mcp/                           → mcp-servers-store.js, mcp-services-store.js
│   ├── backup/                        → backup-store.js
│   ├── developer/                     → websocket-*-store.js
│   ├── skills/                        → skills-*-store.js
│   ├── speech/                        → microphone-setting-store.js
│   └── tunnel/                        → tunnel-store.js
├── notifications/                     → notification-store.js
├── projects/                          → projects-store.js
├── sync/sync-status.html              → sync-store.js
├── admin/                             → admin-store.js
└── tooltips/                          → tooltip-store.js
```

## Sidebar Architecture

### Hover-Expand System

The sidebar has two states controlled by `sidebar-store.js`:

- **Expanded** (`sidebar-expanded` class): 280px width, all labels visible
- **Collapsed** (`sidebar-collapsed` class): 72px width, icon-only, text hidden

State is determined by: `isExpanded = _isHovered || _isPinned`

- Pin button (pushpin icon) toggles `_isPinned`, persisted in `localStorage("sidebarPinned")`
- Mouse enter/leave toggles `_isHovered` (desktop only)
- Focus handlers provide keyboard accessibility
- Mobile: always shows full sidebar (no collapsed mode), pin button hidden

### Collapsed State CSS Rules

When collapsed, the sidebar hides text elements via `#left-panel.sidebar-collapsed .chat-name { display: none; }` pattern. Quick actions go vertical. Tooltips appear on hover via `::after` pseudo-elements.

### Section Collapse

Sidebar sections (Tasks, Preferences) use Bootstrap `Collapse` driven by Alpine `x-effect`:

```html
<h3 @click="$store.sidebar.toggleSection('tasks')">Tasks</h3>
<div class="collapse"
     x-effect="(() => {
       const c = bootstrap.Collapse.getOrCreateInstance($el, { toggle: false });
       $store.sidebar.isSectionOpen('tasks') ? c.show() : c.hide();
     })()">
```

States persisted in `localStorage("sidebarSections")` as JSON.

## Welcome Screen Components

### Dashboard Header
- Logo: `splash.svg` at 5rem, no filter in dark mode, `invert(100%) grayscale(100%)` in light
- Clock: Serif font (`--font-family-serif`), 2.5rem, updated every second
- Date: Gold accent color (`--color-highlight`), uppercase, letter-spaced

### Action Cards
- 4-column CSS grid, glass background with `backdrop-filter: blur(20px)`
- Shine-on-hover: `::before` pseudo-element with 45deg gold gradient, `translateX` animation
- Hover: gold border + box-shadow glow

### System Status Bar
- Glass panel with connection, agent, and chat count
- Live data from `sync-store.js` (connection), `chat-top-store.js` (agent), `chats-store.js` (count)
- Status colors: `.status-healthy` (#4CAF50), `.status-degraded` (#FF9800), `.status-disconnected` (#F44336)

### Background Watermark
- `darkSymbol.svg` as `::before` pseudo on `.welcome-container`
- Dark mode: `invert(0.85)`, opacity 0.08
- Light mode: `invert(0.55)`, opacity 0.06

## Chat Input Section

Glass morphism applied to the chat bar:
```css
#input-section {
  background: var(--color-glass-bg, var(--color-panel));
  border-top: 1px solid var(--color-glass-border, var(--color-border));
  backdrop-filter: blur(20px);
}
```

## Message Styling

Messages use glass effects for user messages:
```css
.message-user {
  background: var(--color-glass-bg, transparent);
  border: 1px solid var(--color-glass-border, transparent);
}
```

Model messages use standard `--color-message-bg`.

## Glass Effect Usage Map

| Component | Element | CSS Class/Selector |
|-----------|---------|-------------------|
| Sidebar | `#left-panel` | `.glass-sidebar` |
| Welcome cards | `.welcome-action-card` | Inline `backdrop-filter` |
| System status | `.system-status` | Inline `backdrop-filter` |
| Chat input | `#input-section` | Inline `backdrop-filter` |
| User messages | `.message-user` | Via glass tokens |
| Modals | Modal content | Via glass tokens |

## Font Loading

Fonts are self-hosted in `webui/public/fonts/`:
- Inter (main sans-serif)
- Playfair Display (serif, used for clock)
- Work Sans (display headings)
- JetBrains Mono (code)
- Rubik (classic theme fallback, also upstream default)
- Roboto Mono (classic code font)

Font-face declarations are in `webui/index.css` (`@font-face` rules near the top of the file).

## Responsive Patterns

### 768px (Tablet/Mobile)
- Sidebar: Fixed overlay, 250px, no collapsed mode
- Welcome: Smaller logo (3.5rem), smaller clock (1.8rem)
- Status bar: Wraps, centered
- Pin button: Hidden

### 520px (Small Mobile)
- Action cards: Single column, horizontal layout (icon + text side by side)
- Status bar: Vertical stack, left-aligned

### 600px height
- Chats section takes full height
- Sidebar top becomes scrollable

## CSS Variable Precedence (Theme Resolution)

```
1. Runtime JS (branding-store.js sets --color-highlight-dark)
   ↓
2. [data-theme="classic"].light-mode (highest CSS specificity for theme+mode)
   ↓
3. [data-theme="classic"] (theme-specific overrides)
   ↓
4. .light-mode (mode overrides)
   ↓
5. :root (default dark-mode executive values)
```

## Key Gotchas

1. **Token resolution**: `var(--color-highlight-dark)` in `:root` resolves immediately. Override shorthand `--color-highlight`, not the `-dark` suffix.
2. **Logo filters**: Never use `invert()` in dark mode — the SVG is designed for dark backgrounds.
3. **Glass fallbacks**: Always provide fallback values: `var(--color-glass-bg, var(--color-panel))`.
4. **Bootstrap Collapse**: Driven programmatically via `x-effect`, not Bootstrap data attributes.
5. **No build step**: All JS is native ES modules. Paths are absolute from webroot (e.g., `/js/AlpineStore.js`).
6. **Component loading**: `<x-component path="...">` loads HTML fragments. The `path` is relative to `webui/components/`.
