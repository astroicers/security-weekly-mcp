// ============================================
// 卡片元件 - 用於事件、漏洞等區塊展示
// ============================================

#import "theme.typ": theme, severity-color
#import "typography.typ": sizes, spacing, fonts
#import "badges.typ": severity-badge, cvss-badge, kev-badge, priority-badge

// 基礎卡片（左側色條）
#let card(
  accent-color: theme.border,
  body,
) = {
  block(
    width: 100%,
    above: spacing.md,
    below: spacing.md,
    stack(
      dir: ltr,
      spacing: 0pt,
      // 左側色條
      rect(
        width: 3pt,
        height: auto,
        fill: accent-color,
        radius: (left: 2pt),
      ),
      // 內容區
      block(
        width: 100% - 3pt,
        fill: theme.bg-subtle,
        stroke: (
          right: 0.5pt + theme.border,
          top: 0.5pt + theme.border,
          bottom: 0.5pt + theme.border,
        ),
        radius: (right: 4pt),
        inset: spacing.md,
        body
      )
    )
  )
}

// 事件卡片
#let event-card(
  title: "",
  severity: "medium",
  event-type: "",
  summary: "",
  affected: (),
  recommendations: (),
) = {
  let color = severity-color(severity)

  card(accent-color: color)[
    // 標題列
    #grid(
      columns: (1fr, auto),
      gutter: spacing.sm,
      text(weight: "bold", size: sizes.lg, fill: theme.primary, title),
      severity-badge(severity),
    )

    // 事件類型
    #if event-type != "" {
      v(spacing.xs)
      text(size: sizes.sm, fill: theme.muted, event-type)
    }

    // 摘要
    #if summary != "" {
      v(spacing.sm)
      text(size: sizes.base, fill: theme.secondary, summary)
    }

    // 受影響產業
    #if affected.len() > 0 {
      v(spacing.sm)
      text(size: sizes.sm, weight: "medium", fill: theme.primary, "受影響產業：")
      text(size: sizes.sm, fill: theme.secondary, affected.join("、"))
    }

    // 建議行動
    #if recommendations.len() > 0 {
      v(spacing.sm)
      text(size: sizes.sm, weight: "medium", fill: theme.primary, "建議行動：")
      v(spacing.xs)
      for rec in recommendations {
        block(
          inset: (left: spacing.md),
          text(size: sizes.sm, fill: theme.secondary, "• " + rec)
        )
      }
    }
  ]
}

// 漏洞卡片
#let vuln-card(
  cve-id: "",
  product: "",
  cvss: 0.0,
  description: "",
  in-kev: false,
  status: none,
) = {
  let color = if cvss >= 9.0 { theme.critical }
              else if cvss >= 7.0 { theme.high }
              else if cvss >= 4.0 { theme.medium }
              else { theme.low }

  card(accent-color: color)[
    // 標題列
    #grid(
      columns: (auto, 1fr, auto),
      gutter: spacing.sm,
      align: (left, left, right),
      text(
        font: fonts.mono,
        weight: "bold",
        size: sizes.base,
        fill: theme.primary,
        cve-id
      ),
      text(size: sizes.sm, fill: theme.muted, product),
      stack(
        dir: ltr,
        spacing: spacing.xs,
        cvss-badge(cvss),
        if in-kev { kev-badge() },
      ),
    )

    // 描述
    #if description != "" {
      v(spacing.sm)
      text(size: sizes.sm, fill: theme.secondary, description)
    }
  ]
}

// 行動項目卡片
#let action-card(
  priority: "P3",
  action: "",
  owner: "",
  deadline: "",
) = {
  let color = if priority == "P1" { theme.critical }
              else if priority == "P2" { theme.high }
              else { theme.medium }

  card(accent-color: color)[
    #grid(
      columns: (auto, 1fr, auto, auto),
      gutter: spacing.md,
      align: (left, left, left, left),
      priority-badge(priority),
      text(size: sizes.base, fill: theme.secondary, action),
      text(size: sizes.sm, fill: theme.muted, owner),
      text(size: sizes.sm, fill: theme.muted, deadline),
    )
  ]
}

// 術語卡片
#let term-card(
  term: "",
  definition: "",
  url: none,
) = {
  card(accent-color: theme.accent)[
    #grid(
      columns: (auto, 1fr),
      gutter: spacing.md,
      if url != none {
        link(url, text(weight: "bold", size: sizes.base, fill: theme.accent, term))
      } else {
        text(weight: "bold", size: sizes.base, fill: theme.primary, term)
      },
      text(size: sizes.sm, fill: theme.secondary, definition),
    )
  ]
}

// 引用區塊
#let quote-block(body) = {
  card(accent-color: theme.muted)[
    #text(style: "italic", fill: theme.secondary, body)
  ]
}

// 提示區塊
#let tip-block(body) = {
  card(accent-color: theme.info)[
    #body
  ]
}

// 警告區塊
#let warning-block(body) = {
  card(accent-color: theme.high)[
    #body
  ]
}
