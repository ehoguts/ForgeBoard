const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
// Optional local QA tooling lives outside the application dependency tree.
const { chromium } = require(
  process.env.PLAYWRIGHT_MODULE ||
    path.resolve(".local/browser-tools/node_modules/playwright"),
);

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.BROWSER_PATH || undefined,
    headless: true,
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1050 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const suffix = Date.now();
  const password = "Local demo passphrase 2026!";
  async function signup(p, email) {
    await p.goto("http://localhost:5173/register");
    await p.getByLabel("Email", { exact: true }).fill(email);
    await p.getByLabel("Password", { exact: true }).fill(password);
    await p.getByRole("button", { name: "Create account" }).click();
    await p.waitForURL("**/login?registered=1");
    await p.getByLabel("Email", { exact: true }).fill(email);
    await p.getByLabel("Password", { exact: true }).fill(password);
    await p.getByRole("button", { name: "Sign in" }).click();
    await p.getByRole("heading", { name: "Make room for progress." }).waitFor();
  }
  async function api(p, path, method = "GET", body, csrf = true) {
    return p.evaluate(
      async ({ path, method, body, csrf }) => {
        const headers = { "Content-Type": "application/json" };
        if (method !== "GET" && csrf) {
          const token = await fetch("/api/v1/auth/csrf").then((r) => r.json());
          headers["X-CSRF-Token"] = token.csrf_token;
        }
        const response = await fetch("/api/v1" + path, {
          method,
          headers,
          body: body === undefined ? undefined : JSON.stringify(body),
        });
        return {
          status: response.status,
          data: response.status === 204 ? null : await response.json(),
        };
      },
      { path, method, body, csrf },
    );
  }
  try {
    await signup(page, `maker-${suffix}@example.com`);
    console.log("PASS register -> login in browser");
    await page
      .getByRole("link", { name: "Projects", exact: false })
      .first()
      .click();
    await page.getByRole("button", { name: "New project" }).click();
    await page.getByLabel("Project name").fill("Portfolio launch");
    await page
      .getByLabel("Description")
      .fill("A focused workspace for shipping the first public release.");
    await page
      .getByRole("button", { name: "Create project", exact: true })
      .click();
    await page
      .getByRole("link")
      .filter({ has: page.getByRole("heading", { name: "Portfolio launch" }) })
      .click();
    await page
      .getByRole("heading", { name: "Portfolio launch", exact: true })
      .waitFor();
    const projectId = page.url().split("/projects/")[1].split("?")[0];
    await page.getByRole("button", { name: "New issue" }).click();
    const editor = page
      .locator("form")
      .filter({ has: page.getByRole("heading", { name: "Create an issue" }) });
    await editor
      .getByLabel("Title", { exact: true })
      .fill("Ship the working MVP");
    await editor
      .getByLabel("Description")
      .fill(
        "Verify registration, account isolation, filters, and the dashboard.",
      );
    await editor
      .getByRole("combobox", { name: /Priority/ })
      .selectOption("high");
    await editor.getByLabel("Due date").fill("2026-12-15");
    await editor
      .getByRole("button", { name: "Create issue", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Ship the working MVP", exact: true })
      .waitFor();
    const issueId = (await api(page, `/projects/${projectId}/issues`)).data
      .items[0].id;
    await page
      .getByLabel("Status for Ship the working MVP")
      .selectOption("done");
    await page.getByText("Status updated.", { exact: true }).waitFor();
    const filters = page.getByRole("search", { name: "Filter issues" });
    await filters
      .getByRole("combobox", { name: /Status/ })
      .selectOption("done");
    await filters
      .getByRole("combobox", { name: /Priority/ })
      .selectOption("high");
    await filters.getByLabel("Search issues").fill("Ship");
    await page
      .getByRole("button", { name: "Ship the working MVP", exact: true })
      .waitFor();
    assert(
      page.url().includes("status=done") &&
        page.url().includes("priority=high") &&
        page.url().includes("search=Ship"),
    );
    await page.reload();
    await page
      .getByRole("button", { name: "Ship the working MVP", exact: true })
      .waitFor();
    fs.mkdirSync("docs/screenshots", { recursive: true });
    await page.screenshot({
      path: "docs/screenshots/project-desktop.png",
      fullPage: true,
    });
    console.log(
      "PASS project/issue creation, status change, combined URL filters and reload",
    );
    await filters.getByLabel("Search issues").fill("no matching issue");
    await page
      .getByText("No issues match these filters.", { exact: true })
      .waitFor();
    await page.getByRole("link", { name: "Overview", exact: false }).click();
    await page
      .getByRole("heading", { name: "Make room for progress." })
      .waitFor();
    const summary = await api(page, "/dashboard/summary");
    assert.deepEqual(summary.data, {
      project_count: 1,
      total_issues: 1,
      todo: 0,
      in_progress: 0,
      done: 1,
    });
    await page
      .locator(".stat strong")
      .first()
      .filter({ hasText: "1" })
      .waitFor();
    await page.screenshot({
      path: "docs/screenshots/dashboard-desktop.png",
      fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({
      path: "docs/screenshots/dashboard-mobile.png",
      fullPage: true,
    });
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      "Mobile page must not overflow horizontally",
    );
    console.log("PASS dashboard totals and mobile width");
    const second = await browser.newContext();
    const b = await second.newPage();
    await signup(b, `reviewer-${suffix}@example.com`);
    assert.equal((await api(b, "/projects")).data.total, 0);
    assert.equal((await api(b, "/dashboard/summary")).data.total_issues, 0);
    for (const path of [`/projects/${projectId}`, `/issues/${issueId}`]) {
      assert.equal((await api(b, path)).status, 404);
      assert.equal(
        (
          await api(
            b,
            path,
            "PATCH",
            path.includes("/issues/")
              ? { title: "Forbidden" }
              : { name: "Forbidden" },
          )
        ).status,
        404,
      );
      assert.equal((await api(b, path, "DELETE")).status, 404);
    }
    assert.equal((await api(b, `/projects/${projectId}/issues`)).status, 404);
    assert.equal(
      (
        await api(b, `/projects/${projectId}/issues`, "POST", {
          title: "Forbidden",
        })
      ).status,
      404,
    );
    assert.equal(
      (await api(page, "/projects", "POST", { name: "Missing CSRF" }, false))
        .status,
      403,
    );
    console.log(
      "PASS two-account GET/PATCH/DELETE/nested isolation and CSRF403",
    );
    await page.goto(`http://localhost:5173/projects/${projectId}`);
    await page
      .getByRole("button", { name: "Edit project", exact: true })
      .click();
    await page.getByLabel("Project name").fill("Portfolio launch — verified");
    await page
      .getByRole("button", { name: "Save project", exact: true })
      .click();
    await page
      .getByRole("heading", { name: "Portfolio launch — verified" })
      .waitFor();
    await page
      .getByRole("button", { name: "Edit Ship the working MVP", exact: true })
      .click();
    await page
      .getByLabel("Title", { exact: true })
      .fill("Ship the verified MVP");
    await page.getByRole("button", { name: "Save issue", exact: true }).click();
    await page
      .getByRole("button", { name: "Ship the verified MVP", exact: true })
      .waitFor();
    page.once("dialog", (d) => d.accept());
    await page
      .getByRole("button", {
        name: "Delete Ship the verified MVP",
        exact: true,
      })
      .click();
    await page.getByText("Issue deleted.", { exact: true }).waitFor();
    await page
      .getByRole("button", { name: "Edit project", exact: true })
      .click();
    page.once("dialog", (d) => d.accept());
    await page
      .getByRole("button", { name: "Delete project", exact: true })
      .click();
    await page.waitForURL("**/projects");
    console.log("PASS project/issue editing and confirmed deletion");
    await page.getByRole("button", { name: "Sign out" }).click();
    await page.getByRole("heading", { name: "Welcome back." }).waitFor();
    assert.equal((await api(page, "/auth/me")).status, 401);
    assert.deepEqual(errors, []);
    console.log("PASS logout revocation; zero uncaught browser errors");
  } catch (error) {
    await page
      .screenshot({ path: ".local/smoke-failure.png", fullPage: true })
      .catch(() => {});
    console.error("Browser URL:", page.url());
    throw error;
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
