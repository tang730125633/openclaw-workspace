const path = require("node:path");
const { chromium } = require("playwright");

async function main() {
  const url = process.argv[2];
  const outputArg = process.argv[3];

  if (!url) {
    console.error("Usage: node export_page_pdf.cjs <url> [output.pdf]");
    process.exit(1);
  }

  const outputPath = path.resolve(
    outputArg || path.join(process.cwd(), "exported-page.pdf"),
  );

  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 2200 },
    });

    await page.goto(url, {
      waitUntil: "networkidle",
      timeout: 60000,
    });

    // Many government pages rely on a print-mode class instead of exposing a real PDF.
    await page.addStyleTag({
      content: `
        body.printing .article_r,
        body.printing .nav,
        body.printing .search,
        body.printing .top,
        body.printing .attachment,
        body.printing .footer,
        body.printing .rightfloat,
        body.printing .header,
        body.printing .path {
          visibility: hidden !important;
          display: none !important;
        }

        body.printing .article,
        body.printing .article_l {
          width: auto !important;
          margin: 0 auto !important;
          float: none !important;
        }

        body.printing .article_con {
          width: auto !important;
          max-width: 1000px !important;
          box-sizing: border-box !important;
          margin: 0 auto !important;
          padding: 0 20px !important;
          line-height: 1.6 !important;
        }
      `,
    });

    await page.evaluate(() => {
      document.body.classList.add("printing");
    });

    await page.pdf({
      path: outputPath,
      format: "A4",
      printBackground: true,
      margin: {
        top: "15mm",
        right: "12mm",
        bottom: "15mm",
        left: "12mm",
      },
    });

    console.log(outputPath);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
