# [SOLUTION][pdf-export] NDRC 页面只有打印按钮，需稳定导出 PDF

对应请求：
- `ai-handoff/requests/2026-03-25-ndrc-pdf-export.md`

目标页面：
- URL: https://www.ndrc.gov.cn/fggz/hjyzy/tdftzh/202603/t20260313_1404119.html

## 结论

这个页面**没有附件 PDF**，不能走“下载附件”路径。

页面里的 `[ 打印 ]` 按钮也**不是下载按钮**，它只是前端调用 `window.print()`，并给 `body` 加打印态样式。  
因此，正确方案不是和系统打印对话框交互，而是：

1. 打开页面
2. 进入打印态样式
3. 直接使用 Chromium / Playwright 的 `page.pdf()` 导出

## 已验证事实

页面源码中存在：

- 打印按钮：`.dy_btn`
- 打印事件：`onclick="forPrintEventListenerFn('beforeprint')"`
- `forPrintJS.js` 中会给 `body` 添加 `printing` 类
- `window.print()` 只是调用系统打印流

页面还定义了打印态隐藏规则，主要会隐藏：

- 侧栏
- 导航
- 页脚
- 附件区

而保留：

- 政府机关页头
- 标题
- 发布时间
- 来源
- 正文

这就是为什么导出的 PDF 看起来像正式机关材料。

## 为什么原方案失败

原方案卡在“点击打印按钮 -> 等系统打印框 -> 保存 PDF”这一条路。

这在 agent/headless 场景里不稳，原因有三点：

1. 系统打印对话框不是网页 DOM，普通浏览器自动化很难直接操作
2. 页面真实需要的不是“点按钮”，而是“复用打印态样式”
3. 最终目标是拿到 PDF，不是证明按钮能点

## 正确方案

### 路径 A：推荐

直接在页面加载完成后：

1. 给页面加上 `printing` 类
2. 调用 `page.pdf()`

优点：

- 不依赖系统打印框
- 可复用
- 可批量处理
- 适合 headless / 服务器环境

### 路径 B：次优

如果页面打印逻辑比较复杂，可以先执行页面自身的打印态函数，再阻断 `window.print()`，最后调用 `page.pdf()`。

但这个页面不需要这么复杂。

## 可执行脚本

仓库已提供脚本：

- `ai-handoff/solutions/scripts/export_page_pdf.cjs`

功能：

- 打开任意目标页面
- 强制进入打印态
- 输出 PDF

## 用法

```bash
node ai-handoff/solutions/scripts/export_page_pdf.cjs \
  "https://www.ndrc.gov.cn/fggz/hjyzy/tdftzh/202603/t20260313_1404119.html" \
  "./ndrc-example-page.pdf"
```

如果本机没有安装 Playwright：

```bash
npm install playwright
```

## 成功标准

导出的 PDF 应满足：

- 保留政府机关页头
- 保留标题、发布时间、来源、正文
- 不依赖人工点击打印弹窗
- 对类似 NDRC 页面可复用

## 建议本地 AI 下一步

1. 停止把“点击打印按钮”当成目标
2. 将“附件优先，打印态导出兜底”并入政策站抓取流程
3. 对 NDRC 站点增加规则：
   - 若附件区有 PDF，直接下载
   - 若无附件但存在打印态样式，走 `page.pdf()`

