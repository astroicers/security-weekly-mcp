#!/usr/bin/env node
/**
 * Weekly Security Report Generator using Claude Agent SDK
 *
 * Uses Anthropic API key to generate weekly security reports.
 * Requires ANTHROPIC_API_KEY environment variable.
 *
 * Usage:
 *   node claude-weekly-report.mjs              # current week
 *   node claude-weekly-report.mjs --week 2026-10  # specific week (historical mode)
 */

import { query } from '@anthropic-ai/claude-agent-sdk';

const SYSTEM_PROMPT = `你是資安週報產生助手，使用繁體中文（台灣）。

任務：用 MCP tools 收集資安新聞與漏洞，整理成結構化 JSON 週報並儲存。

術語規則：
- extract_terms 提取已有術語 → 放入 terms 欄位
- 遇到術語庫未收錄的重要專有名詞（APT 組織、惡意程式家族、新攻擊技術）：
  用 create_pending_term 建立，立即接 approve_pending_term（每次最多 5 個）
- brief_definition ≤ 30 字；id 格式：小寫字母、數字、底線（如 salt_typhoon）`;

function parseWeekArg(arg) {
  // Parse --week YYYY-WW and return { year, week, start, end, reportId }
  const match = arg.match(/^(\d{4})-(\d{1,2})$/);
  if (!match) {
    console.error(`Error: --week format must be YYYY-WW (e.g. 2026-10), got: ${arg}`);
    process.exit(1);
  }
  const year = parseInt(match[1]);
  const week = parseInt(match[2]);
  // ISO week: Monday of that week (UTC to avoid timezone offset issues)
  const jan4Ms = Date.UTC(year, 0, 4); // Jan 4 is always in ISO week 1
  const jan4Dow = new Date(jan4Ms).getUTCDay(); // 0=Sun,1=Mon,...
  const week1MonMs = jan4Ms - ((jan4Dow + 6) % 7) * 86400000;
  const mondayMs = week1MonMs + (week - 1) * 7 * 86400000;
  const sundayMs = mondayMs + 6 * 86400000;
  const fmt = (ms) => new Date(ms).toISOString().slice(0, 10);
  return {
    year,
    week,
    start: fmt(mondayMs),
    end: fmt(sundayMs),
    reportId: `SEC-WEEKLY-${year}-${String(week).padStart(2, '0')}`,
  };
}

function buildPrompt(weekInfo) {
  if (!weekInfo) {
    // Current week — use RSS
    return `請產生本週資安週報。

## 輸出 JSON 格式（嚴格遵守欄位名稱）

\`\`\`json
{
  "title": "資安週報 YYYY/MM/DD - YYYY/MM/DD",
  "report_id": "SEC-WEEKLY-YYYY-WW",
  "period": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "publish_date": "YYYY-MM-DD",
  "summary": { "total_events": 0, "total_vulnerabilities": 0, "threat_level": "normal|elevated|high|critical" },
  "events": [{ "title": "", "severity": "critical|high|medium|low", "event_type": "", "summary": "", "source": "", "url": "", "date": "" }],
  "vulnerabilities": [{ "cve_id": "", "title": "", "cvss": 0.0, "severity": "", "vendor": "", "product": "", "description": "" }],
  "threat_trends": {},
  "action_items": [{ "priority": "high|medium|low", "action": "" }],
  "terms": [],
  "references": []
}
\`\`\`

## 執行步驟

1. fetch_security_news（days=7）
2. fetch_vulnerabilities（min_cvss=7.0, include_kev=true）
3. 挑選最重要 10-15 個事件，整理漏洞並標註 KEV
4. extract_terms 提取已有術語 → 填入 terms
5. 新術語入庫：create_pending_term → 立即 approve_pending_term（最多 5 個）
6. generate_report_draft 產生草稿
7. Write tool 儲存到 output/reports/SEC-WEEKLY-YYYY-WW.json（WW 兩位數，如 08）

請開始執行。`;
  }

  // Historical week — use WebSearch instead of RSS
  const { start, end, reportId, week, year } = weekInfo;
  const startDisp = start.replace(/-/g, '/');
  const endDisp = end.replace(/-/g, '/');
  return `請產生 ${startDisp} ~ ${endDisp}（第 ${week} 週）的資安週報。

## 報告識別資訊（固定填入，不要修改）

- report_id: "${reportId}"
- period.start: "${start}"
- period.end: "${end}"
- publish_date: "${end}"
- title: "資安週報 ${startDisp} - ${endDisp}"

## 輸出 JSON 格式（嚴格遵守欄位名稱）

\`\`\`json
{
  "title": "資安週報 ${startDisp} - ${endDisp}",
  "report_id": "${reportId}",
  "period": { "start": "${start}", "end": "${end}" },
  "publish_date": "${end}",
  "summary": { "total_events": 0, "total_vulnerabilities": 0, "threat_level": "normal|elevated|high|critical" },
  "events": [{ "title": "", "severity": "critical|high|medium|low", "event_type": "", "summary": "", "source": "", "url": "", "date": "" }],
  "vulnerabilities": [{ "cve_id": "", "title": "", "cvss": 0.0, "severity": "", "vendor": "", "product": "", "description": "" }],
  "threat_trends": {},
  "action_items": [{ "priority": "high|medium|low", "action": "" }],
  "terms": [],
  "references": []
}
\`\`\`

## 執行步驟（歷史模式：RSS 已過期，改用 WebSearch）

1. WebSearch 搜尋以下查詢（加入時間範圍 after:${start} before:${end}）：
   - "cybersecurity news ${start.slice(0, 7)}"
   - "CVE critical vulnerability ${start.slice(0, 7)}"
   - "APT ransomware attack ${start.slice(0, 7)}"
   - "台灣 資安 ${year}年${parseInt(start.slice(5, 7))}月"
   - "site:twcert.org.tw"
2. fetch_vulnerabilities（min_cvss=7.0, days=7, include_kev=true）— 可能無歷史資料，盡力而為
3. 挑選最重要 10-15 個事件，整理漏洞並標註 KEV
4. extract_terms 提取已有術語 → 填入 terms
5. 新術語入庫：create_pending_term → 立即 approve_pending_term（最多 5 個）
6. generate_report_draft 產生草稿
7. Write tool 儲存到 output/reports/${reportId}.json

請開始執行。`;
}

async function main() {
  const startTime = Date.now();

  // Check for Anthropic API key
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('Error: ANTHROPIC_API_KEY environment variable is required');
    console.error('Set the ANTHROPIC_API_KEY secret in GitHub repository settings');
    process.exit(1);
  }

  // Parse --week argument
  const weekArgIdx = process.argv.indexOf('--week');
  const weekInfo = weekArgIdx !== -1 ? parseWeekArg(process.argv[weekArgIdx + 1]) : null;
  const prompt = buildPrompt(weekInfo);

  const options = {
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-6',
    cwd: process.cwd(),
    maxTurns: 35,
    permissionMode: 'bypassPermissions',
    allowDangerouslySkipPermissions: true,
    persistSession: false,
    extraArgs: {
      'system-prompt': SYSTEM_PROMPT,
    },
    mcpServers: {
      'security-weekly-tw': {
        type: 'stdio',
        command: 'uv',
        args: [
          'run',
          '--directory', process.cwd(),
          '--package', 'security-weekly-mcp-server',
          'python', '-m', 'security_weekly_mcp.server',
        ],
      },
    },
  };

  console.log('='.repeat(60));
  console.log('Weekly Security Report Generator');
  console.log('Using Claude Agent SDK with MCP Server');
  console.log('='.repeat(60));
  console.log(`Model: ${options.model}`);
  console.log(`Working directory: ${options.cwd}`);
  if (weekInfo) {
    console.log(`Mode: HISTORICAL — ${weekInfo.start} ~ ${weekInfo.end} (${weekInfo.reportId})`);
  } else {
    console.log('Mode: CURRENT WEEK');
  }
  console.log(`Started at: ${new Date().toISOString()}`);
  console.log('='.repeat(60));
  console.log('');

  try {
    for await (const message of query({ prompt, options })) {
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
