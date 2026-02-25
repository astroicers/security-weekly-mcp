#!/usr/bin/env node
/**
 * Weekly Security Report Generator using Claude Agent SDK
 *
 * Uses Claude Max subscription via OAuth token to generate weekly security reports.
 * Requires CLAUDE_CODE_OAUTH_TOKEN environment variable.
 */

import { query } from '@anthropic-ai/claude-agent-sdk';

const SYSTEM_PROMPT = `你是資安週報產生助手。你的任務是：
1. 使用 MCP tools 收集本週資安新聞和漏洞
2. 分析並整理成結構化週報
3. 輸出 JSON 到指定目錄

請使用繁體中文撰寫。週報應包含：
- 本週重要資安事件摘要
- 高風險漏洞列表 (CVSS >= 7.0)
- 行動建議

## 重要：JSON 輸出格式規範

輸出 JSON **必須** 包含以下頂層欄位，缺一不可：

\`\`\`json
{
  "title": "資安週報 YYYY/MM/DD - YYYY/MM/DD",
  "report_id": "SEC-WEEKLY-YYYY-WW",
  "period": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "publish_date": "YYYY-MM-DD",
  "summary": {
    "total_events": number,
    "total_vulnerabilities": number,
    "threat_level": "normal" | "elevated" | "high" | "critical"
  },
  "events": [...],
  "vulnerabilities": [...],
  "threat_trends": {...},
  "action_items": [...],
  "terms": [],
  "references": [...]
}
\`\`\`

### events 內部欄位
- title (string): 事件標題
- severity (string): "critical" | "high" | "medium" | "low"
- event_type (string): 事件類型
- summary (string): 事件摘要（注意：欄位名稱是 summary，不是 description）
- source (string): 來源
- url (string): 來源網址
- date (string): "YYYY-MM-DD"

### vulnerabilities 內部欄位
- cve_id (string): CVE 編號（注意：欄位名稱是 cve_id，不是 cve）
- title (string): 漏洞標題
- cvss (number): CVSS 分數（注意：欄位名稱是 cvss，不是 cvss_score）
- severity (string): "critical" | "high" | "medium" | "low"
- vendor (string): 廠商
- product (string): 產品
- description (string): 漏洞描述

### action_items 內部欄位
- priority (string): "high" | "medium" | "low"
- action (string): 行動描述（注意：欄位名稱是 action，不是 title 或 description）

**嚴格遵守以上欄位名稱，不要使用別名或替代欄位名。**`;

const WEEKLY_PROMPT = `請產生本週的資安週報：

1. 先用 fetch_security_news 收集最近 7 天的新聞
2. 用 fetch_vulnerabilities 收集高風險漏洞 (min_cvss=7.0, include_kev=true)
3. 分析這些資料，挑選最重要的 10-15 個事件
4. 整理漏洞資訊，標註 KEV 中的漏洞
5. 用 generate_report_draft 產生週報草稿

**重要**：產生的 JSON 必須包含所有必填頂層欄位：
   - report_id: "SEC-WEEKLY-YYYY-WW"（WW 為兩位數週數）
   - period: { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }
   - publish_date: "YYYY-MM-DD"
   - summary 必須包含 total_events, total_vulnerabilities, threat_level
   - events 中用 summary（非 description）、source、url
   - vulnerabilities 中用 cve_id（非 cve）、cvss（非 cvss_score）
   - action_items 中用 action（非 title/description）、priority 只用 high/medium/low
   - 必須包含 terms: [] 和 references: []

6. 將產生的 JSON 用 Write tool 儲存到 output/reports/SEC-WEEKLY-YYYY-WW.json
   （WW 為兩位數週數，如 08、09，不要加 W 前綴）

請開始執行。`;

async function main() {
  const startTime = Date.now();

  // Check for OAuth token
  if (!process.env.CLAUDE_CODE_OAUTH_TOKEN) {
    console.error('Error: CLAUDE_CODE_OAUTH_TOKEN environment variable is required');
    console.error('Run "claude setup-token" to generate one');
    process.exit(1);
  }

  const options = {
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    cwd: process.cwd(),
    maxTurns: 50, // Allow enough turns for data collection + analysis
    permissionMode: 'bypassPermissions',
    allowDangerouslySkipPermissions: true,
    persistSession: false,
    extraArgs: {
      'system-prompt': SYSTEM_PROMPT,
    },
  };

  console.log('='.repeat(60));
  console.log('Weekly Security Report Generator');
  console.log('Using Claude Agent SDK with MCP Server');
  console.log('='.repeat(60));
  console.log(`Model: ${options.model}`);
  console.log(`Working directory: ${options.cwd}`);
  console.log(`Started at: ${new Date().toISOString()}`);
  console.log('='.repeat(60));
  console.log('');

  try {
    for await (const message of query({ prompt: WEEKLY_PROMPT, options })) {
      switch (message.type) {
        case 'assistant':
          // Handle complete assistant message
          for (const block of message.message.content) {
            if (block.type === 'text') {
              process.stdout.write(block.text);
            } else if (block.type === 'tool_use') {
              console.log(`\n[Tool] ${block.name}`);
            }
          }
          break;

        case 'result':
          // Final result with token usage
          const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
          console.log('\n');
          console.log('='.repeat(60));
          console.log('Execution Complete');
          console.log('='.repeat(60));
          console.log(`Status: ${message.subtype}`);
          console.log(`Input tokens: ${message.usage.input_tokens.toLocaleString()}`);
          console.log(`Output tokens: ${message.usage.output_tokens.toLocaleString()}`);
          console.log(`Cost: $${message.total_cost_usd.toFixed(4)}`);
          console.log(`Elapsed time: ${elapsed}s`);
          console.log('='.repeat(60));

          if (message.subtype !== 'success') {
            console.error(`\nError: Query ended with status "${message.subtype}"`);
            process.exit(1);
          }
          break;

        case 'system':
          // System messages (session info, etc.)
          if (process.env.DEBUG) {
            console.log('[System]', JSON.stringify(message, null, 2));
          }
          break;

        default:
          // Other message types
          break;
      }
    }
  } catch (error) {
    console.error('\nFatal error:', error.message);
    process.exit(1);
  }

  console.log('\nDone!');
}

main();
