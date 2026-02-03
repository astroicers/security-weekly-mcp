// ============================================
// Security Weekly Report - 資安週報主模板
// 簡約現代風格
// ============================================

#import "components/theme.typ": theme, severity-color, severity-label
#import "components/typography.typ": fonts, sizes, spacing, page-setup, leading
#import "components/badges.typ": severity-badge, cvss-badge, kev-badge, priority-badge
#import "components/cards.typ": event-card, vuln-card, action-card, term-card, card
#import "components/tables.typ": vuln-table, action-table, term-table, summary-table, reference-list

// 主模板函數
#let weekly-report(
  data: (:),
  doc,
) = {
  // 頁面設定
  set page(
    paper: page-setup.paper,
    margin: page-setup.margin,
    header: context {
      if counter(page).get().first() > 1 {
        grid(
          columns: (1fr, 1fr),
          align: (left, right),
          text(size: sizes.xs, fill: theme.muted, data.at("title", default: "資安週報")),
          text(size: sizes.xs, fill: theme.muted, data.at("report_id", default: "")),
        )
        line(length: 100%, stroke: 0.5pt + theme.border)
      }
    },
    footer: context {
      line(length: 100%, stroke: 0.5pt + theme.border)
      v(spacing.xs)
      grid(
        columns: (1fr, 1fr, 1fr),
        align: (left, center, right),
        text(size: sizes.xs, fill: theme.muted, "機密等級：內部使用"),
        text(size: sizes.xs, fill: theme.muted, "第 " + str(counter(page).get().first()) + " 頁"),
        text(size: sizes.xs, fill: theme.muted, "發布日期：" + data.at("publish_date", default: "")),
      )
    },
  )

  // 字體設定
  set text(
    font: fonts.sans,
    size: sizes.base,
    fill: theme.secondary,
    lang: "zh",
    region: "TW",
  )

  // 段落設定
  set par(
    justify: true,
    leading: leading.normal * 1em,
  )

  // 標題樣式
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(spacing.xl)
    text(
      size: sizes.at("3xl"),
      weight: "bold",
      fill: theme.primary,
      it.body
    )
    v(spacing.lg)
  }

  show heading.where(level: 2): it => {
    v(spacing.xl)
    text(
      size: sizes.at("2xl"),
      weight: "bold",
      fill: theme.primary,
      it.body
    )
    v(spacing.md)
  }

  show heading.where(level: 3): it => {
    v(spacing.lg)
    text(
      size: sizes.xl,
      weight: "semibold",
      fill: theme.primary,
      it.body
    )
    v(spacing.sm)
  }

  // 連結樣式
  show link: it => {
    text(fill: theme.accent, it)
  }

  // 程式碼樣式
  show raw: it => {
    text(font: fonts.mono, size: sizes.sm, it)
  }

  // ========== 封面 ==========
  {
    v(3cm)

    // 標題
    align(center)[
      #text(
        size: sizes.at("4xl"),
        weight: "bold",
        fill: theme.primary,
        data.at("title", default: "資安週報")
      )
    ]

    v(1cm)

    // 報告編號
    align(center)[
      #text(
        size: sizes.xl,
        fill: theme.muted,
        data.at("report_id", default: "")
      )
    ]

    v(2cm)

    // 報告期間
    {
      let period = data.at("period", default: (:))
      align(center)[
        #text(
          size: sizes.lg,
          fill: theme.secondary,
          "報告期間：" + period.at("start", default: "") + " ~ " + period.at("end", default: "")
        )
      ]
    }

    v(0.5cm)

    // 發布日期
    align(center)[
      #text(
        size: sizes.base,
        fill: theme.muted,
        "發布日期：" + data.at("publish_date", default: "")
      )
    ]

    v(3cm)

    // 摘要區塊
    {
      let summary = data.at("summary", default: (:))
      let level = summary.at("threat_level", default: "normal")
      let threat-color = if level == "elevated" { theme.high } else { theme.low }
      let threat-label = if level == "elevated" { "升高" } else { "正常" }

      align(center)[
        #box(
          width: 60%,
          fill: theme.bg-subtle,
          stroke: 0.5pt + theme.border,
          radius: 4pt,
          inset: spacing.lg,
        )[
          #grid(
            columns: (1fr, 1fr, 1fr),
            gutter: spacing.lg,
            align: center,
            [
              #text(size: sizes.at("2xl"), weight: "bold", fill: theme.primary, str(summary.at("total_events", default: 0)))
              #v(spacing.xs)
              #text(size: sizes.sm, fill: theme.muted, "重大事件")
            ],
            [
              #text(size: sizes.at("2xl"), weight: "bold", fill: theme.primary, str(summary.at("total_vulnerabilities", default: 0)))
              #v(spacing.xs)
              #text(size: sizes.sm, fill: theme.muted, "高風險漏洞")
            ],
            [
              #text(size: sizes.at("2xl"), weight: "bold", fill: threat-color, threat-label)
              #v(spacing.xs)
              #text(size: sizes.sm, fill: theme.muted, "威脅等級")
            ],
          )
        ]
      ]
    }
  }

  // ========== 目錄 ==========
  pagebreak()
  heading(level: 1, outlined: false)[目錄]
  outline(
    title: none,
    indent: spacing.lg,
    depth: 2,
  )

  // ========== 正文 ==========
  doc
}

// ========== 區段渲染函數 ==========

// 渲染事件區段
#let render-events(events) = {
  heading(level: 1)[重大資安事件]

  if events.len() == 0 {
    text(fill: theme.muted, "本期無重大資安事件。")
  } else {
    for event in events {
      event-card(
        title: event.at("title", default: ""),
        severity: event.at("severity", default: "medium"),
        event-type: event.at("event_type", default: ""),
        summary: event.at("summary", default: ""),
        affected: event.at("affected_industries", default: ()),
        recommendations: event.at("recommendations", default: ()),
      )
    }
  }
}

// 渲染漏洞區段
#let render-vulnerabilities(vulnerabilities) = {
  heading(level: 1)[關鍵漏洞通報]

  if vulnerabilities.len() == 0 {
    text(fill: theme.muted, "本期無高風險漏洞通報。")
  } else {
    vuln-table(vulnerabilities)
  }
}

// 渲染威脅趨勢區段
#let render-threat-trends(trends) = {
  heading(level: 1)[威脅趨勢]

  if trends.at("summary", default: "") != "" {
    text(trends.summary)
    v(spacing.md)
  }

  // 活躍威脅行為者
  let actors = trends.at("active_actors", default: ())
  if actors.len() > 0 {
    heading(level: 2)[本週活躍威脅行為者]
    for actor in actors {
      block(
        inset: (left: spacing.md, y: spacing.xs),
        grid(
          columns: (auto, 1fr),
          gutter: spacing.sm,
          text(weight: "bold", fill: theme.primary, "• " + actor.at("name", default: "")),
          text(fill: theme.secondary, actor.at("activity", default: "")),
        )
      )
    }
  }

  // 攻擊手法
  let techniques = trends.at("attack_techniques", default: ())
  if techniques.len() > 0 {
    heading(level: 2)[熱門攻擊手法]
    for tech in techniques {
      block(
        inset: (left: spacing.md, y: spacing.xs),
        text(fill: theme.secondary, "• " + tech)
      )
    }
  }
}

// 渲染行動項目區段
#let render-action-items(actions) = {
  heading(level: 1)[本週行動項目]

  if actions.len() == 0 {
    text(fill: theme.muted, "本期無特定行動項目。")
  } else {
    action-table(actions)
  }
}

// 渲染術語區段
#let render-terms(terms) = {
  heading(level: 1)[本期術語]

  if terms.len() == 0 {
    text(fill: theme.muted, "本期無新術語。")
  } else {
    term-table(terms)
  }
}

// 渲染參考資料區段
#let render-references(refs) = {
  heading(level: 1)[參考資料]

  if refs.len() == 0 {
    text(fill: theme.muted, "無參考資料。")
  } else {
    reference-list(refs)
  }
}

// ========== 完整報告渲染 ==========

#let render-full-report(data) = {
  show: weekly-report.with(data: data)

  // 事件
  let events = data.at("events", default: ())
  if events.len() > 0 {
    render-events(events)
  }

  // 漏洞
  let vulns = data.at("vulnerabilities", default: ())
  if vulns.len() > 0 {
    render-vulnerabilities(vulns)
  }

  // 威脅趨勢
  let trends = data.at("threat_trends", default: (:))
  if type(trends) == dictionary and trends.keys().len() > 0 {
    render-threat-trends(trends)
  }

  // 行動項目
  let actions = data.at("action_items", default: ())
  if actions.len() > 0 {
    render-action-items(actions)
  }

  // 術語
  let terms = data.at("terms", default: ())
  if terms.len() > 0 {
    render-terms(terms)
  }

  // 參考資料
  let refs = data.at("references", default: ())
  if refs.len() > 0 {
    render-references(refs)
  }
}
