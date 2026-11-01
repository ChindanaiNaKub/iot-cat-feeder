# Design

## Theme

Warm paper, dark ink, one green for action, one amber for "happening now", one red for "empty or lost".
The page reads like a label on a kitchen appliance: quiet surface, loud only where state changes.

Light theme only. The device is read in a bright kitchen at arm's length; dark mode would fight the daylight.

## Color

Strategy: restrained. Accent colors carry state, never decoration.

| Token | Value | Use |
|---|---|---|
| `--paper` | `#f4efe6` | page canvas |
| `--surface` | `#fffcf7` | panels, list rows |
| `--ink` | `#221d18` | headings, values |
| `--muted` | `#6e6459` | labels, secondary (5.0:1 on paper) |
| `--line` | `rgba(34,29,24,.14)` | hairlines |
| `--green` | `#1d5c43` | primary action, healthy level |
| `--amber` | `#a85400` | flap open, cat nearby, low food |
| `--red` | `#9b2c2c` | hopper empty, sensor unreadable, offline |

Level tone is semantic, chosen by percentage: green above 40, amber 15 to 40, red below 15.

## Typography

One family, system Thai stack: `"Noto Sans Thai", "Sarabun", system-ui, sans-serif`.
No web font request; the board may sit on a LAN with no internet.
Scale: 11, 12.5, 14, 16, 22, 34px. Numerals use `font-variant-numeric: tabular-nums` so the clock does not jitter.

## Layout

Mobile first, single column, `max-width: 480px`.
Above 620px the gauge and the log sit side by side, the rest stays in one column.
Sections in order: identity and clock, flap state, hopper gauge and cat presence, schedule, feed log, primary action, link quality.

## Components

- **State pill.** Dot plus label. Amber with a slow pulse while the flap is open, green when shut.
- **Gauge.** CSS conic-gradient ring with `@property --p` so the fill animates, masked to a ring. Center holds the percentage.
- **Cat panel.** Distance in cm, concentric rings that pulse only when the cat is near.
- **Schedule chips.** Three times; the next one gets a filled background and a countdown.
- **Log rows.** Time, source badge, newest first, five entries.
- **Primary button.** Full width, 56px tall, green, `:active` presses down, disabled while a feed is in flight, announces the result in a toast.

Every interactive element defines default, hover, focus-visible, active, disabled and loading.

## Motion

150 to 220ms, ease-out-quart. Only state changes move: gauge fill, flap pulse, button press, toast.
`@media (prefers-reduced-motion: reduce)` removes pulse, gauge transition and toast slide.
