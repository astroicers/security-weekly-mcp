// ============================================
// 字體排版設定
// ============================================

#import "theme.typ": theme

// 字體設定
#let fonts = (
  // 主要字體（優先使用 Noto 系列）
  serif: ("Noto Serif CJK TC", "Noto Serif TC", "Source Han Serif TC", "serif"),
  sans: ("Noto Sans CJK TC", "Noto Sans TC", "Source Han Sans TC", "sans-serif"),
  mono: ("JetBrains Mono", "Fira Code", "Noto Sans Mono CJK TC", "monospace"),
)

// 字體大小
#let sizes = (
  xs: 8pt,
  sm: 9pt,
  base: 10pt,
  lg: 11pt,
  xl: 13pt,
  "2xl": 16pt,
  "3xl": 20pt,
  "4xl": 24pt,
)

// 行高
#let leading = (
  tight: 1.2,
  normal: 1.5,
  relaxed: 1.75,
)

// 間距
#let spacing = (
  xs: 4pt,
  sm: 8pt,
  md: 12pt,
  lg: 16pt,
  xl: 24pt,
  "2xl": 32pt,
)

// 頁面設定
#let page-setup = (
  paper: "a4",
  margin: (
    top: 2.5cm,
    bottom: 2.5cm,
    left: 2.5cm,
    right: 2.5cm,
  ),
)

// 標題樣式
#let heading-style(level, body) = {
  let size = if level == 1 { sizes.at("3xl") }
             else if level == 2 { sizes.at("2xl") }
             else if level == 3 { sizes.xl }
             else { sizes.lg }

  let weight = if level <= 2 { "bold" } else { "semibold" }
  let color = theme.primary
  let above = if level == 1 { spacing.at("2xl") }
              else if level == 2 { spacing.xl }
              else { spacing.lg }
  let below = if level == 1 { spacing.lg }
              else { spacing.md }

  block(
    above: above,
    below: below,
    text(
      size: size,
      weight: weight,
      fill: color,
      body
    )
  )
}

// 段落樣式
#let paragraph-style(body) = {
  set par(
    justify: true,
    leading: leading.normal * 1em,
    first-line-indent: 0pt,
  )
  body
}

// 程式碼樣式
#let code-style(body) = {
  set text(
    font: fonts.mono,
    size: sizes.sm,
  )
  body
}
