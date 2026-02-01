// ============================================
// 徽章元件 - 用於標示狀態、嚴重程度等
// ============================================

#import "theme.typ": theme, severity-color, severity-label, priority-color, priority-label
#import "typography.typ": sizes, spacing

// 基礎徽章
#let badge(
  content,
  bg-color: theme.bg-muted,
  text-color: theme.secondary,
  border-color: none,
) = {
  box(
    fill: bg-color,
    stroke: if border-color != none { 0.5pt + border-color } else { none },
    radius: 3pt,
    inset: (x: 6pt, y: 2pt),
    text(
      size: sizes.xs,
      weight: "medium",
      fill: text-color,
      content
    )
  )
}

// 嚴重程度徽章
#let severity-badge(level) = {
  let color = severity-color(level)
  let label = severity-label(level)

  box(
    fill: color.lighten(85%),
    stroke: 0.5pt + color.lighten(50%),
    radius: 3pt,
    inset: (x: 6pt, y: 2pt),
    text(
      size: sizes.xs,
      weight: "bold",
      fill: color,
      label
    )
  )
}

// 優先級徽章
#let priority-badge(level) = {
  let color = priority-color(level)
  let label = priority-label(level)

  box(
    fill: color.lighten(85%),
    stroke: 0.5pt + color.lighten(50%),
    radius: 3pt,
    inset: (x: 6pt, y: 2pt),
    text(
      size: sizes.xs,
      weight: "bold",
      fill: color,
      level + " " + label
    )
  )
}

// CVSS 分數徽章
#let cvss-badge(score) = {
  let color = if score >= 9.0 { theme.critical }
              else if score >= 7.0 { theme.high }
              else if score >= 4.0 { theme.medium }
              else { theme.low }

  box(
    fill: color.lighten(85%),
    stroke: 0.5pt + color.lighten(50%),
    radius: 3pt,
    inset: (x: 6pt, y: 2pt),
    text(
      size: sizes.xs,
      weight: "bold",
      fill: color,
      "CVSS " + str(score)
    )
  )
}

// KEV 標記徽章
#let kev-badge() = {
  box(
    fill: theme.critical.lighten(90%),
    stroke: 0.5pt + theme.critical.lighten(60%),
    radius: 3pt,
    inset: (x: 6pt, y: 2pt),
    text(
      size: sizes.xs,
      weight: "bold",
      fill: theme.critical,
      "KEV"
    )
  )
}

// 狀態徽章
#let status-badge(status) = {
  let (color, label) = if status == "exploited" {
    (theme.critical, "已遭利用")
  } else if status == "patched" {
    (theme.low, "已修補")
  } else if status == "poc" {
    (theme.high, "有 PoC")
  } else {
    (theme.info, status)
  }

  badge(label, bg-color: color.lighten(85%), text-color: color, border-color: color.lighten(50%))
}

// 標籤
#let tag(content) = {
  box(
    fill: theme.bg-subtle,
    stroke: 0.5pt + theme.border,
    radius: 2pt,
    inset: (x: 4pt, y: 1pt),
    text(
      size: sizes.xs,
      fill: theme.muted,
      content
    )
  )
}
