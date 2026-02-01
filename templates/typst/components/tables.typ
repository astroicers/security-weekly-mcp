// ============================================
// 表格元件
// ============================================

#import "theme.typ": theme, severity-color
#import "typography.typ": sizes, spacing, fonts
#import "badges.typ": severity-badge, cvss-badge, kev-badge, priority-badge, status-badge

// 基礎表格樣式
#let styled-table(
  columns: (),
  align: left,
  header: (),
  ..rows,
) = {
  set text(size: sizes.sm)

  table(
    columns: columns,
    align: align,
    stroke: 0.5pt + theme.border,
    inset: spacing.sm,

    // 表頭
    ..for h in header {
      (table.cell(
        fill: theme.bg-muted,
        text(weight: "bold", fill: theme.primary, h)
      ),)
    },

    // 資料列
    ..rows.pos().flatten()
  )
}

// 漏洞表格
#let vuln-table(vulnerabilities) = {
  set text(size: sizes.sm)

  table(
    columns: (auto, 1fr, auto, auto, auto),
    align: (left, left, center, center, center),
    stroke: 0.5pt + theme.border,
    inset: spacing.sm,

    // 表頭
    table.cell(fill: theme.bg-muted, text(weight: "bold", "CVE ID")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "產品")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "CVSS")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "狀態")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "優先級")),

    // 資料列
    ..for vuln in vulnerabilities {
      let cvss = if type(vuln.cvss) == float { vuln.cvss } else { 0.0 }
      let priority = if cvss >= 9.0 { "P1" }
                     else if cvss >= 7.0 { "P2" }
                     else { "P3" }

      (
        table.cell(
          text(font: fonts.mono, fill: theme.primary, vuln.cve_id)
        ),
        table.cell(vuln.product),
        table.cell(cvss-badge(cvss)),
        table.cell(
          if vuln.at("in_kev", default: false) {
            stack(dir: ltr, spacing: 2pt, kev-badge(), status-badge("exploited"))
          } else if vuln.at("status", default: none) != none {
            status-badge(vuln.status)
          } else {
            text(fill: theme.muted, "-")
          }
        ),
        table.cell(priority-badge(priority)),
      )
    }
  )
}

// 行動項目表格
#let action-table(actions) = {
  set text(size: sizes.sm)

  table(
    columns: (auto, 1fr, auto, auto),
    align: (center, left, left, left),
    stroke: 0.5pt + theme.border,
    inset: spacing.sm,

    // 表頭
    table.cell(fill: theme.bg-muted, text(weight: "bold", "優先級")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "行動項目")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "負責單位")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "期限")),

    // 資料列
    ..for action in actions {
      (
        table.cell(priority-badge(action.priority)),
        table.cell(action.action),
        table.cell(text(fill: theme.muted, action.at("owner", default: "-"))),
        table.cell(text(fill: theme.muted, action.at("deadline", default: "-"))),
      )
    }
  )
}

// 術語表格
#let term-table(terms) = {
  set text(size: sizes.sm)

  table(
    columns: (auto, 1fr),
    align: (left, left),
    stroke: 0.5pt + theme.border,
    inset: spacing.sm,

    // 表頭
    table.cell(fill: theme.bg-muted, text(weight: "bold", "術語")),
    table.cell(fill: theme.bg-muted, text(weight: "bold", "說明")),

    // 資料列
    ..for term in terms {
      (
        table.cell(
          if term.at("url", default: none) != none {
            link(term.url, text(weight: "medium", fill: theme.accent, term.term))
          } else {
            text(weight: "medium", fill: theme.primary, term.term)
          }
        ),
        table.cell(term.definition),
      )
    }
  )
}

// 摘要統計表格
#let summary-table(stats) = {
  set text(size: sizes.base)

  table(
    columns: (1fr, auto),
    align: (left, right),
    stroke: none,
    inset: spacing.sm,

    ..for (key, value) in stats {
      (
        text(fill: theme.secondary, key),
        text(weight: "bold", fill: theme.primary, str(value)),
      )
    }
  )
}

// 來源列表
#let reference-list(refs) = {
  set text(size: sizes.sm)

  for (i, ref) in refs.enumerate() {
    block(
      inset: (left: spacing.md, y: spacing.xs),
      grid(
        columns: (auto, 1fr),
        gutter: spacing.sm,
        text(fill: theme.muted, str(i + 1) + "."),
        if ref.at("url", default: none) != none {
          link(ref.url, text(fill: theme.accent, ref.title))
        } else {
          text(fill: theme.secondary, ref.title)
        }
      )
    )
  }
}
