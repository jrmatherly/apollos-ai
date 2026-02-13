# Design Tokens Reference

Complete catalog of CSS custom properties defined in `webui/css/tokens.css`.

## Token Architecture

Tokens follow a two-layer system. See SKILL.md "Token Resolution" section for the full explanation and code example.

1. **Suffixed tokens** (`:root`): Raw values with `-dark` suffix
2. **Shorthand tokens** (`index.css`): Map suffixed to usable vars
3. **Theme overrides**: Override SHORTHAND vars in `[data-theme]` selectors

## Executive Theme — Dark Mode (Default)

Source: `:root` in `tokens.css`

### Backgrounds
| Token | Value | Usage |
|-------|-------|-------|
| `--color-background-dark` | `#0A0B0D` | Page/app background |
| `--color-chat-background-dark` | `#0F1115` | Chat area background |
| `--color-panel-dark` | `#121418` | Sidebar, settings panels |
| `--color-message-bg-dark` | `#1A1D23` | Message bubbles |
| `--color-input-dark` | `#0A0B0D` | Input fields |
| `--color-input-focus-dark` | `#080910` | Focused input fields |

### Accent (Gold Palette)
| Token | Value | Usage |
|-------|-------|-------|
| `--color-highlight-dark` | `#D4AF37` | Primary gold accent |
| `--color-highlight-dim` | `#B8860B` | Subdued gold (borders, subtle) |
| `--color-highlight-bright` | `#FFBF00` | Bright gold (active states) |
| `--color-primary-dark` | `#94A3B8` | Primary text actions |

### Text
| Token | Value | Usage |
|-------|-------|-------|
| `--color-text-dark` | `#E2E8F0` | Primary text |
| `--color-text-muted-dark` | `#94A3B8` | Secondary/muted text |
| `--color-message-text-dark` | `#CBD5E1` | Chat message text |

### Borders
| Token | Value | Usage |
|-------|-------|-------|
| `--color-border-dark` | `rgba(255, 255, 255, 0.08)` | Subtle borders |

### Status Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--color-accent-dark` | `#cf6679` | Accent/destructive |
| `--color-error-text-dark` | `#e72323` | Error text |
| `--color-warning-text-dark` | `#e79c23` | Warning text |
| `--color-secondary-dark` | `#475569` | Secondary elements |
| `--color-table-row-dark` | `#141720` | Alternating table rows |

### Glass Effect Tokens
| Token | Value | Usage |
|-------|-------|-------|
| `--color-glass-bg` | `rgba(20, 21, 23, 0.6)` | Glass panel backgrounds |
| `--color-glass-border` | `rgba(212, 175, 55, 0.15)` | Gold-tinted glass borders |
| `--color-glass-sidebar` | `rgba(10, 11, 13, 0.8)` | Sidebar glass (higher opacity) |

### Typography
| Token | Value | Usage |
|-------|-------|-------|
| `--font-family-main` | `"Inter", "Rubik", Arial, Helvetica, sans-serif` | Body text |
| `--font-family-serif` | `"Playfair Display", Georgia, serif` | Clock, headings |
| `--font-family-display` | `"Work Sans", "Inter", sans-serif` | Display/header text |
| `--font-family-code` | `"JetBrains Mono", "Roboto Mono", monospace` | Code blocks |

## Executive Theme — Light Mode

Source: `.light-mode` in `tokens.css`

| Token | Value | Notes |
|-------|-------|-------|
| `--color-background` | `#FAFAF8` | Warm off-white |
| `--color-chat-background` | `#FAFAF8` | |
| `--color-panel` | `#F0F0EE` | |
| `--color-message-bg` | `#FFFFFF` | |
| `--color-input` | `#E8E8E4` | |
| `--color-input-focus` | `#DDDDD8` | |
| `--color-highlight` | `#6B5A1B` | WCAG AA compliant dark gold |
| `--color-primary` | `#4A5568` | |
| `--color-text` | `#1A202C` | |
| `--color-text-muted` | `#4A5568` | |
| `--color-message-text` | `#2D3748` | |
| `--color-border` | `rgba(0, 0, 0, 0.12)` | |
| `--color-glass-bg` | `rgba(255, 255, 255, 0.7)` | |
| `--color-glass-border` | `rgba(107, 90, 27, 0.15)` | |

## Classic Theme — Dark Mode

Source: `[data-theme="classic"]` in `tokens.css`

| Token | Value | Notes |
|-------|-------|-------|
| `--color-background` | `#131313` | Original upstream dark |
| `--color-chat-background` | `#212121` | |
| `--color-panel` | `#1a1a1a` | |
| `--color-message-bg` | `#2d2d2d` | |
| `--color-input` | `#131313` | |
| `--color-input-focus` | `#101010` | |
| `--color-highlight` | `#2b5ab9` | Blue accent |
| `--color-primary` | `#737a81` | |
| `--color-text` | `#ffffff` | |
| `--color-text-muted` | `#d4d4d4e4` | |
| `--color-message-text` | `#e0e0e0` | |
| `--color-border` | `#444444a8` | |
| `--color-glass-bg` | `transparent` | No glass effects |
| `--color-glass-border` | `transparent` | |
| `--color-glass-sidebar` | `transparent` | |
| `--color-highlight-dim` | `#1e40af` | |
| `--color-highlight-bright` | `#3b82f6` | |
| `--font-family-main` | `"Rubik", Arial, Helvetica, sans-serif` | No serif/display fonts |
| `--font-family-serif` | `"Rubik", Arial, Helvetica, sans-serif` | Falls back to main |
| `--font-family-code` | `"Roboto Mono", monospace` | |

## Classic Theme — Light Mode

Source: `[data-theme="classic"].light-mode` in `tokens.css`

| Token | Value | Notes |
|-------|-------|-------|
| `--color-background` | `#fafafa` | |
| `--color-highlight` | `#2563eb` | Brighter blue for light bg |
| `--color-text` | `#333333` | |
| `--color-border` | `#bdbdbdcf` | |
| `--color-error-text` | `#920000` | Darker for light contrast |
| `--color-warning-text` | `#936214` | |

## Branding Integration

The `branding-store.js` dynamically overrides `--color-highlight-dark` at runtime via:

```javascript
document.documentElement.style.setProperty("--color-highlight-dark", this.accent_color);
```

This allows server-side branding to customize the gold accent. Default: `#D4AF37`.

## Accessibility Notes

- Executive light-mode gold (`#6B5A1B`) meets WCAG AA contrast ratio on white
- Classic light-mode blue (`#2563eb`) meets WCAG AA on white
- `prefers-reduced-motion` disables all `backdrop-filter` effects globally
- Status colors (green/yellow/red) use high-contrast values that work on both backgrounds
