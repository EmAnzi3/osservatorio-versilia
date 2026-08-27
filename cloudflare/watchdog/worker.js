const DEFAULTS = {
  owner: "EmAnzi3",
  repo: "osservatorio-versilia",
  ref: "main",
  dailyWorkflow: "opportunity-radar-daily.yml",
  monthlyWorkflow: "monthly-data-refresh.yml",
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function config(env) {
  return {
    owner: env.GITHUB_OWNER || DEFAULTS.owner,
    repo: env.GITHUB_REPO || DEFAULTS.repo,
    ref: env.GITHUB_REF || DEFAULTS.ref,
    dailyWorkflow: DEFAULTS.dailyWorkflow,
    monthlyWorkflow: DEFAULTS.monthlyWorkflow,
  };
}

function githubHeaders(env) {
  const headers = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "osservatorio-versilia-cloudflare-watchdog",
  };

  if (env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${env.GITHUB_TOKEN}`;
  }

  return headers;
}

function isAuthorized(request, env) {
  if (!env.WATCHDOG_KEY) return false;

  return request.headers.get("authorization") === `Bearer ${env.WATCHDOG_KEY}`;
}

function utcDateParts(now = new Date()) {
  const iso = now.toISOString();

  return {
    date: iso.slice(0, 10),
    month: iso.slice(0, 7),
    day: Number(iso.slice(8, 10)),
  };
}

async function listWorkflowRuns(env, workflow) {
  const cfg = config(env);
  const url =
    `https://api.github.com/repos/${cfg.owner}/${cfg.repo}/actions/workflows/` +
    `${encodeURIComponent(workflow)}/runs?per_page=20`;

  const response = await fetch(url, {
    headers: githubHeaders(env),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`GitHub runs API ${response.status}: ${await response.text()}`);
  }

  const payload = await response.json();
  return payload.workflow_runs || [];
}

async function dispatchWorkflow(env, workflow, inputs = undefined) {
  if (!env.GITHUB_TOKEN) {
    throw new Error("GITHUB_TOKEN non configurato: dispatch impossibile");
  }

  const cfg = config(env);
  const body = { ref: cfg.ref };

  if (inputs && Object.keys(inputs).length) {
    body.inputs = inputs;
  }

  const response = await fetch(
    `https://api.github.com/repos/${cfg.owner}/${cfg.repo}/actions/workflows/` +
      `${encodeURIComponent(workflow)}/dispatches`,
    {
      method: "POST",
      headers: {
        ...githubHeaders(env),
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );

  if (!response.ok) {
    throw new Error(`GitHub dispatch ${response.status}: ${await response.text()}`);
  }

  let responseBody = null;
  const text = await response.text();

  if (text) {
    try {
      responseBody = JSON.parse(text);
    } catch {
      responseBody = text;
    }
  }

  return {
    status: response.status,
    response: responseBody,
  };
}

async function checkDaily(env, doDispatch) {
  const cfg = config(env);
  const { date } = utcDateParts();
  const snapshotUrl =
    `https://raw.githubusercontent.com/${cfg.owner}/${cfg.repo}/${cfg.ref}/` +
    `data/opportunity-daily-public.json?watchdog=${Date.now()}`;

  const response = await fetch(snapshotUrl, {
    headers: {
      "User-Agent": "osservatorio-versilia-cloudflare-watchdog",
      "Cache-Control": "no-cache",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    return {
      target: "daily",
      status: "error",
      expectedDate: date,
      error: `snapshot HTTP ${response.status}`,
      dispatched: false,
    };
  }

  const snapshot = await response.json();
  const referenceDate = snapshot.referenceDate || null;

  if (referenceDate === date) {
    return {
      target: "daily",
      status: "current",
      expectedDate: date,
      referenceDate,
      dispatched: false,
    };
  }

  const runs = await listWorkflowRuns(env, cfg.dailyWorkflow);
  const activeToday = runs.find(
    (run) => run.created_at?.slice(0, 10) === date && run.status !== "completed",
  );

  if (activeToday) {
    return {
      target: "daily",
      status: "running",
      expectedDate: date,
      referenceDate,
      runId: activeToday.id,
      runUrl: activeToday.html_url,
      dispatched: false,
    };
  }

  if (!doDispatch) {
    return {
      target: "daily",
      status: "stale",
      expectedDate: date,
      referenceDate,
      wouldDispatch: true,
      dispatched: false,
    };
  }

  const dispatch = await dispatchWorkflow(env, cfg.dailyWorkflow);

  return {
    target: "daily",
    status: "dispatched",
    expectedDate: date,
    referenceDate,
    workflow: cfg.dailyWorkflow,
    dispatch,
    dispatched: true,
  };
}

async function checkMonthly(env, doDispatch) {
  const cfg = config(env);
  const { month, day } = utcDateParts();

  if (day < 5) {
    return {
      target: "monthly",
      status: "not_due",
      month,
      dueFromDay: 5,
      dispatched: false,
    };
  }

  const runs = await listWorkflowRuns(env, cfg.monthlyWorkflow);
  const relevant = runs.filter(
    (run) =>
      run.created_at?.slice(0, 7) === month &&
      (run.event === "schedule" || run.event === "workflow_dispatch"),
  );

  const completed = relevant.find(
    (run) => run.status === "completed" && run.conclusion === "success",
  );

  if (completed) {
    return {
      target: "monthly",
      status: "completed",
      month,
      conclusion: completed.conclusion,
      runId: completed.id,
      runUrl: completed.html_url,
      dispatched: false,
    };
  }

  const active = relevant.find((run) => run.status !== "completed");

  if (active) {
    return {
      target: "monthly",
      status: "running",
      month,
      runId: active.id,
      runUrl: active.html_url,
      dispatched: false,
    };
  }

  if (!doDispatch) {
    return {
      target: "monthly",
      status: "missing",
      month,
      wouldDispatch: true,
      dispatched: false,
    };
  }

  const dispatch = await dispatchWorkflow(env, cfg.monthlyWorkflow);

  return {
    target: "monthly",
    status: "dispatched",
    month,
    workflow: cfg.monthlyWorkflow,
    dispatch,
    dispatched: true,
  };
}

async function runChecks(env, target, doDispatch) {
  const results = [];

  if (target === "daily" || target === "all") {
    results.push(await checkDaily(env, doDispatch));
  }

  if (target === "monthly" || target === "all") {
    results.push(await checkMonthly(env, doDispatch));
  }

  return results;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return json({
        ok: true,
        service: "osservatorio-versilia-watchdog",
        mode: "manual-poc",
        cronEnabled: false,
      });
    }

    if (url.pathname !== "/check") {
      return json({ error: "not_found", endpoints: ["/health", "/check"] }, 404);
    }

    const target = url.searchParams.get("target") || "all";

    if (!new Set(["daily", "monthly", "all"]).has(target)) {
      return json(
        {
          error: "invalid_target",
          allowed: ["daily", "monthly", "all"],
        },
        400,
      );
    }

    const doDispatch = url.searchParams.get("dispatch") === "1";

    if (doDispatch && !isAuthorized(request, env)) {
      return json({ error: "unauthorized" }, 401);
    }

    try {
      const results = await runChecks(env, target, doDispatch);

      return json({
        ok: true,
        mode: doDispatch ? "dispatch" : "dry-run",
        checkedAt: new Date().toISOString(),
        results,
      });
    } catch (error) {
      return json(
        {
          ok: false,
          mode: doDispatch ? "dispatch" : "dry-run",
          checkedAt: new Date().toISOString(),
          error: error instanceof Error ? error.message : String(error),
        },
        502,
      );
    }
  },
};
