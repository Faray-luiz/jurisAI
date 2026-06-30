# AI Governance Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a comprehensive AI Governance and Token Analytics Dashboard in the admin panel, accessible to Sócios and Compliance officers, displaying token consumption, cost metrics, process-specific AI usage, and ethical wall events.

**Architecture:** Add a new admin sub-tab `governanca` in `Sidebar.tsx` and `page.tsx`. Implement a backend endpoint `GET /api/v1/admin/governance/stats` in `backend/app/main.py` that aggregates SQL audit log metrics. Create a clean corporate prestige dashboard layout in `page.tsx` with KPI cards, process usage tables, SVG charts, and compliance warning logs.

**Tech Stack:** React (Next.js/TSX), Tailwind CSS / Vanilla CSS, Python (FastAPI/SQLAlchemy).

---

### Task 1: Backend Governance Stats API

**Files:**
- Modify: `backend/app/main.py`

**Step 1: Write dynamic metrics query endpoint in `main.py`**

Define `GET /api/v1/admin/governance/stats` right after the `/api/v1/admin/audits` endpoint.

```python
@app.get("/api/v1/admin/governance/stats")
def get_governance_stats(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Compliance", "Sócio"]:
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito ao painel de governança."
        )
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBAuditLog, DBProcess
    db = SessionLocal()
    try:
        audits = db.query(DBAuditLog).all()
        processes = db.query(DBProcess).all()
        
        proc_map = {p.id: p for p in processes}
        
        # 1. Total Metrics
        total_cost = sum(a.cost_usd for a in audits)
        total_requests = len(audits)
        ethical_wall_blocks = sum(1 for a in audits if a.status == "Bloqueado")
        
        # 2. Model Distribution
        model_counts = {"openai": 0, "anthropic": 0, "google": 0}
        for a in audits:
            m_lower = a.model.lower()
            if "gpt" in m_lower or "openai" in m_lower:
                model_counts["openai"] += 1
            elif "claude" in m_lower or "anthropic" in m_lower:
                model_counts["anthropic"] += 1
            else:
                model_counts["google"] += 1
                
        total_classified = sum(model_counts.values()) or 1
        model_dist = {
            "openai": round((model_counts["openai"] / total_classified) * 100, 1),
            "anthropic": round((model_counts["anthropic"] / total_classified) * 100, 1),
            "google": round((model_counts["google"] / total_classified) * 100, 1)
        }
        
        # 3. Usage by Process
        process_stats = {}
        for a in audits:
            pid = a.process_id
            if not pid or pid == "N/A":
                continue
            if pid not in process_stats:
                proc_info = proc_map.get(pid)
                process_stats[pid] = {
                    "process_id": pid,
                    "number": proc_info.number if proc_info else pid,
                    "client": proc_info.client if proc_info else "Cliente Externo",
                    "cumulative_cost": 0.0,
                    "actions": set(),
                    "status": "Conforme"
                }
            
            p_stat = process_stats[pid]
            p_stat["cumulative_cost"] += a.cost_usd
            if a.action:
                p_stat["actions"].add(a.action)
            if a.grounding_status == "Não Verificado":
                p_stat["status"] = "Em Revisão"
                
        process_list = []
        for p_stat in process_stats.values():
            p_stat["actions"] = list(p_stat["actions"])
            process_list.append(p_stat)
            
        process_list.sort(key=lambda x: x["cumulative_cost"], reverse=True)
        
        # 4. Recent Governance Events
        recent_events = []
        # Get 10 most recent logs
        sorted_audits = sorted(audits, key=lambda x: x.timestamp, reverse=True)
        for a in sorted_audits[:10]:
            recent_events.append({
                "timestamp": a.timestamp,
                "user_email": a.user_email,
                "action": a.action,
                "process_id": a.process_id,
                "model": a.model,
                "cost_usd": a.cost_usd,
                "status": a.status,
                "grounding_status": a.grounding_status
            })
            
        return {
            "total_cost": round(total_cost, 4),
            "total_requests": total_requests,
            "ethical_wall_blocks": ethical_wall_blocks,
            "model_distribution": model_dist,
            "process_usage": process_list,
            "recent_events": recent_events
        }
    finally:
        db.close()
```

**Step 2: Commit backend API changes**

```bash
git add backend/app/main.py
git commit -m "feat: add backend endpoint for AI governance stats"
```

---

### Task 2: Frontend Navigation & Sub-tab Setup

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/app/page.tsx`

**Step 1: Add governanca to AdminSubTab in `Sidebar.tsx`**

* Update the `AdminSubTab` type to include `"governanca"`.
* Add the new sub-tab in `GOV_ITEMS`:
  ```typescript
  { key: "governanca", label: "Painel Governança", icon: <Shield size={14} /> }
  ```

**Step 2: Update `adminSubTab` type in `page.tsx`**

* Add `"governanca"` to the useState typing of `adminSubTab` on line 161.

---

### Task 3: Governance Dashboard UI Implementation

**Files:**
- Modify: `frontend/src/app/page.tsx`

**Step 1: Render the Governance Dashboard in `page.tsx`**

* Under `{adminSubTab === "missoes" && ...}`, add the TSX component rendering and governance UI panels.
* Implement chart hooks and UI blocks displaying Process Engagement, model distributions, and compliance blocks.

**Step 2: Run build to verify Next.js compilations**

```bash
npm run build
```

**Step 3: Commit frontend changes**

```bash
git add frontend/src/components/Sidebar.tsx frontend/src/app/page.tsx
git commit -m "feat: implement AI Governance & Analytics Dashboard frontend"
```
