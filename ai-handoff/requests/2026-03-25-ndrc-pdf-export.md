# [HELP][pdf-export] NDRC 页面只有打印按钮，需稳定导出 PDF

## 任务类型
- pdf-export / browser-automation

## 当前目标
- 将国家发改委文章页通过点击页面打印按钮稳定导出为 PDF

## 目标对象
- URL: https://www.ndrc.gov.cn/fggz/hjyzy/tdftzh/202603/t20260313_1404119.html
- 页面标题: 我国建成全球最大的可再生能源体系 每用10度电就有近4度是绿电
- 相关站点: ndrc.gov.cn

## 已确认事实
- 页面附件区为空，没有现成 PDF 附件
- 页面存在打印按钮，class=`dy_btn`，文本="[ 打印 ]"
- 打印按钮走前端打印流程，不是直接下载 PDF
- 点击打印按钮后页面内容简化，可能进入打印预览态

## 已尝试步骤
1. agent-browser open 打开目标页面
2. agent-browser eval 查找打印按钮元素（找到 class=dy_btn）
3. agent-browser eval 执行 document.querySelector('.dy_btn').click()
4. agent-browser eval 执行 window.print() 直接调用
5. agent-browser wait 等待页面变化

## 当前失败点
- 失败现象: 点击打印按钮后无 PDF 生成，无法闭环
- 报错信息: 无报错，但无预期输出
- 卡住位置: 页面调用打印流程后，现有 agent 无法与系统打印对话框交互

## 怀疑根因
- 根因猜测 1: 打印按钮调用 window.print() 触发系统打印对话框，headless 环境无法处理
- 根因猜测 2: 页面可能有打印态 CSS（@media print），但当前未复用
- 根因猜测 3: 需要改用浏览器原生 PDF 导出能力，而非模拟打印按钮点击

## 复现步骤
1. agent-browser open https://www.ndrc.gov.cn/fggz/hjyzy/tdftzh/202603/t20260313_1404119.html
2. agent-browser eval "document.querySelector('.dy_btn').click()"
3. 观察页面变化，但无 PDF 生成

## 成功标准
- 成功生成 PDF 文件
- PDF 保留政府机关页头、标题、发布时间、来源、正文
- 不依赖人工点击系统打印弹窗
- 流程可复用到其他 NDRC 文章页

## 相关文件
- 脚本: /Users/mf/.openclaw/workspace/tools/policy-site-monitor/scripts/run_policy_site_monitor.sh
- 配置: /Users/mf/.openclaw/workspace/tools/policy-site-monitor/config/sites.yaml
- 输出目录: /Users/mf/.openclaw/workspace/knowledge-base/审核池/

## 附件与证据
- 截图: 待补充（当前环境无图形界面）
- 日志: agent-browser 执行记录已保存
- HTML 快照: 页面可通过 agent-browser snapshot 获取

## 建议外部 AI 优先做什么
1. 检查页面打印按钮的具体实现（是否 window.print()）
2. 检查是否存在 @media print CSS 样式可直接复用
3. 优先尝试 Playwright/Chromium 原生 PDF 导出（page.pdf()）
4. 如果必须点击打印按钮，探索 CDP 拦截打印请求的方案
5. 最终回传可复用的脚本或配置变更

## 处理状态
- 状态: ANSWERED
- 解决文件: `ai-handoff/solutions/2026-03-25-ndrc-pdf-export-solution.md`
- 可执行脚本: `ai-handoff/solutions/scripts/export_page_pdf.cjs`
- 核心结论: 该页面无附件 PDF，正确路径是复用打印态样式后直接调用浏览器 `page.pdf()`，而不是和系统打印框交互
