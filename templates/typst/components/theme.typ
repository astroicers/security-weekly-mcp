// ============================================
// 主題配色 - 簡約現代風格
// ============================================

// 主色調
#let theme = (
  // 文字色彩
  primary: rgb("#1f2937"),       // 深灰 - 標題
  secondary: rgb("#4b5563"),     // 中灰 - 正文
  muted: rgb("#9ca3af"),         // 淺灰 - 次要文字

  // 強調色
  accent: rgb("#2563eb"),        // 藍色 - 連結、強調

  // 嚴重程度
  critical: rgb("#dc2626"),      // 危急 - 紅色
  high: rgb("#ea580c"),          // 高 - 橙色
  medium: rgb("#ca8a04"),        // 中 - 黃色
  low: rgb("#16a34a"),           // 低 - 綠色
  info: rgb("#0891b2"),          // 資訊 - 青色

  // 背景與邊框
  bg-subtle: rgb("#f9fafb"),     // 淺灰背景
  bg-muted: rgb("#f3f4f6"),      // 稍深背景
  border: rgb("#e5e7eb"),        // 邊框
  border-strong: rgb("#d1d5db"), // 強調邊框

  // 純色
  white: rgb("#ffffff"),
  black: rgb("#000000"),
)

// 嚴重程度對應函數
#let severity-color(level) = {
  if level == "critical" { theme.critical }
  else if level == "high" { theme.high }
  else if level == "medium" { theme.medium }
  else if level == "low" { theme.low }
  else { theme.info }
}

// 嚴重程度中文
#let severity-label(level) = {
  if level == "critical" { "危急" }
  else if level == "high" { "高" }
  else if level == "medium" { "中" }
  else if level == "low" { "低" }
  else { "資訊" }
}

// 優先級對應
#let priority-color(level) = {
  if level == "P1" { theme.critical }
  else if level == "P2" { theme.high }
  else if level == "P3" { theme.medium }
  else { theme.low }
}

#let priority-label(level) = {
  if level == "P1" { "立即" }
  else if level == "P2" { "緊急" }
  else if level == "P3" { "優先" }
  else { "一般" }
}
