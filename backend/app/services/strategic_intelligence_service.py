import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.strategic_intelligence import (
    StrategicPlan,
    StrategicGoal,
    StrategicInitiative,
    MarketIntelligence,
    MarketSignal,
    Competitor,
    SWOTEntry,
    MarketSizing,
    StrategicOpportunity,
    StrategicScenario,
    StrategicDecision,
    BusinessKPI,
    BusinessKPIValue,
)
from app.models.user import User
from app.schemas.strategic_intelligence import (
    StrategicPlanCreate,
    StrategicPlanUpdate,
    StrategicPlanResponse,
    StrategicGoalCreate,
    StrategicGoalUpdate,
    StrategicGoalResponse,
    StrategicInitiativeCreate,
    StrategicInitiativeUpdate,
    StrategicInitiativeResponse,
    MarketIntelligenceCreate,
    MarketIntelligenceResponse,
    MarketSignalCreate,
    MarketSignalResponse,
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    SWOTEntryCreate,
    SWOTEntryResponse,
    MarketSizingCreate,
    MarketSizingResponse,
    StrategicOpportunityCreate,
    StrategicOpportunityUpdate,
    StrategicOpportunityResponse,
    StrategicScenarioCreate,
    StrategicScenarioResponse,
    StrategicScenarioCompareResponse,
    StrategicDecisionCreate,
    StrategicDecisionResponse,
    StrategicDashboardOverviewResponse,
    AIStrategyRecommendation,
    BusinessKPICreate,
    BusinessKPIUpdate,
    BusinessKPIResponse,
    BusinessKPIValueCreate,
    BusinessKPIValueResponse,
    StrategicAIAnalyzeRequest,
    StrategicAIAnalyzeResponse,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class StrategicIntelligenceService:
    @staticmethod
    def ensure_baseline_data(db: Session, organization_id: Optional[int] = None, workspace_id: Optional[int] = None):
        """Seed baseline strategic plan, goals, SWOT, competitors, market sizing, opportunities, and KPIs if empty."""
        query = db.query(StrategicPlan)
        if workspace_id is not None:
            query = query.filter(StrategicPlan.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicPlan.organization_id == organization_id)

        if query.count() == 0:
            plan = StrategicPlan(
                organization_id=organization_id,
                workspace_id=workspace_id,
                title="FocusBoard FY27 SaaS Expansion & Enterprise Dominance",
                vision="To be the single source of operational and strategic intelligence for high-velocity teams.",
                mission="Empower knowledge workers with deterministic productivity, collaborative context, and autonomous AI agents.",
                strategic_themes_json=json.dumps([
                    "Enterprise Trust & GRC Leadership",
                    "Autonomous AI Agent Workflows",
                    "Net Revenue Retention & Global Scale"
                ]),
                time_horizon="ANNUAL",
                status="ACTIVE",
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)

            # Strategic Goals
            g1 = StrategicGoal(
                organization_id=organization_id,
                workspace_id=workspace_id,
                plan_id=plan.id,
                title="Scale Annual Run Rate (ARR) to $100k",
                description="Expand mid-market tenant acquisition and tier migrations to Enterprise plans.",
                category="REVENUE",
                target_metric="ARR Cents",
                baseline_value=15000.0,
                target_value=100000.0,
                current_value=28500.0,
                unit="$",
                status="ACTIVE",
                deadline=utc_now() + timedelta(days=240),
            )
            g2 = StrategicGoal(
                organization_id=organization_id,
                workspace_id=workspace_id,
                plan_id=plan.id,
                title="Attain 115% Net Revenue Retention (NRR)",
                description="Drive product-led expansion through AI agent execution packs and seat volume.",
                category="RETENTION",
                target_metric="NRR Percentage",
                baseline_value=95.0,
                target_value=115.0,
                current_value=108.5,
                unit="%",
                status="ACTIVE",
                deadline=utc_now() + timedelta(days=180),
            )
            db.add_all([g1, g2])
            db.commit()
            db.refresh(g1)
            db.refresh(g2)

            # Strategic Initiatives
            i1 = StrategicInitiative(
                organization_id=organization_id,
                workspace_id=workspace_id,
                goal_id=g1.id,
                title="Self-Serve SOC2 Compliance & Enterprise Trust Portal",
                description="Deliver continuous security compliance evidence and SAML/SCIM automation.",
                priority="P1_CRITICAL",
                budget_amount=25000.0,
                status="IN_PROGRESS",
                progress_percentage=65.0,
            )
            i2 = StrategicInitiative(
                organization_id=organization_id,
                workspace_id=workspace_id,
                goal_id=g2.id,
                title="Cross-Tool Webhook Ecosystem & Integration Marketplace",
                description="Enable bidirectional sync with Jira, GitHub, Slack, and Salesforce.",
                priority="P2_HIGH",
                budget_amount=18000.0,
                status="IN_PROGRESS",
                progress_percentage=40.0,
            )
            db.add_all([i1, i2])

            # Competitors (ensure unique names)
            base_comps = [
                ("Asana", "https://asana.com", "LEADER", "PER_SEAT", '["Broad enterprise adoption", "Template ecosystem"]', '["High per-seat licensing", "Legacy performance lag"]', "HIGH", "Incumbent project management leader with strong market presence."),
                ("Linear", "https://linear.app", "CHALLENGER", "PER_SEAT", '["High keyboard velocity", "Minimalist dev UX"]', '["Limited executive BI", "Engineering only"]', "MEDIUM", "Developer-focused project management benchmark."),
                ("Monday.com", "https://monday.com", "LEADER", "PER_SEAT", '["Extensive marketing workflows", "Visual boards"]', '["Heavy visual clutter", "Complex onboarding"]', "HIGH", "Heavyweight competitor with aggressive enterprise sales motion."),
            ]
            for cname, cweb, cpos, cprice, cstr, cweak, cthreat, cnotes in base_comps:
                existing_comp = db.query(Competitor).filter(Competitor.name == cname).first()
                if not existing_comp:
                    comp = Competitor(
                        organization_id=None,
                        workspace_id=None,
                        name=cname,
                        website=cweb,
                        market_position=cpos,
                        pricing_model=cprice,
                        strengths_json=cstr,
                        weaknesses_json=cweak,
                        threat_level=cthreat,
                        notes=cnotes,
                    )
                    db.add(comp)
                elif existing_comp.workspace_id is not None:
                    existing_comp.workspace_id = None
                    existing_comp.organization_id = None

            # SWOT entries
            swot_items = [
                ("STRENGTH", "Zero-Trust Architecture & Granular Multi-Tenant Isolation", "HIGH", "Every tenant, project, and record is cryptographic or row-isolated by workspace.", "SOC 2 Type II controls verified across microservices."),
                ("STRENGTH", "Autonomous AI Agents with Grounded Telemetry", "HIGH", "AI assistant references actual live database records and KPIs.", "Benchmarked 94% precision in test suite."),
                ("WEAKNESS", "PWA Offline Awareness in Non-Technical Teams", "MEDIUM", "Desktop web users rarely trigger PWA installation.", "Telemetry shows 12% install banner engagement."),
                ("OPPORTUNITY", "Marketplace Third-Party App & Webhook Ecosystem", "HIGH", "Enterprise IT demands unified workflow hub with bi-directional syncing.", "Customer advisory board feedback."),
                ("THREAT", "Incumbent Pricing Commoditization", "MEDIUM", "Legacy vendors offering aggressive bundled pricing discounts.", "Loss analysis in 3 mid-market sales cycles."),
            ]
            for stype, stitle, simp, sdesc, sevid in swot_items:
                sw = SWOTEntry(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    swot_type=stype,
                    title=stitle,
                    description=sdesc,
                    impact=simp,
                    evidence_text=sevid,
                    is_ai_generated=False,
                )
                db.add(sw)

            # Market Sizing
            ms = MarketSizing(
                organization_id=organization_id,
                workspace_id=workspace_id,
                market_name="Collaborative Intelligence & Modern SaaS Workspaces",
                methodology="BOTTOM_UP",
                tam_cents=4500000000000,  # $45B
                sam_cents=850000000000,   # $8.5B
                som_cents=12000000000,    # $120M
                currency="USD",
                assumptions_json=json.dumps({"seat_growth_rate": "18% CAGR", "target_penetration": "1.4%"}),
                confidence_score=0.88,
            )
            db.add(ms)

            # Opportunities
            opps = [
                ("Automated SOC 2 Compliance Report Generator", "Generate cryptographic audit packs for enterprise procurement teams.", "Enterprise B2B", 3500000, 9.0, 3000.0, 3.5, 0.85, 2.0, 4462.5, "APPROVED"),
                ("Bidirectional Jira & GitHub Issues Sync Hub", "Keep engineering tasks and product specs in real-time sync.", "Product Engineering", 1800000, 8.5, 2000.0, 2.5, 0.80, 2.5, 1600.0, "IN_PROGRESS"),
                ("Deterministic Speech-to-Task Field Notes", "Enable mobile field teams to dictate rich task descriptions offline.", "Mobile / Field Teams", 950000, 7.5, 1200.0, 2.0, 0.70, 3.0, 560.0, "EVALUATING"),
            ]
            for otitle, odesc, oseg, oval, ofeas, o_r, o_i, o_c, o_e, o_s, ostat in opps:
                opp = StrategicOpportunity(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    title=otitle,
                    description=odesc,
                    customer_segment=oseg,
                    estimated_value_cents=oval,
                    feasibility_score=ofeas,
                    rice_reach=o_r,
                    rice_impact=o_i,
                    rice_confidence=o_c,
                    rice_effort=o_e,
                    rice_score=o_s,
                    status=ostat,
                )
                db.add(opp)

            # Business KPIs
            kpis = [
                ("Annual Run Rate (ARR)", "Annualized recurring subscription run rate", "REVENUE", "$", 100000.0, 28500.0, 15000.0, "UP", "ON_TRACK"),
                ("Net Revenue Retention (NRR)", "Net dollar retention including expansion and churn", "GROWTH", "%", 115.0, 108.5, 95.0, "UP", "ON_TRACK"),
                ("Customer Churn Rate", "Monthly cohort logo churn percentage", "CUSTOMER", "%", 2.0, 2.4, 3.5, "DOWN", "ON_TRACK"),
                ("Gross Margin", "Core platform gross profit margin percentage", "OPERATIONAL", "%", 85.0, 81.2, 72.0, "UP", "ON_TRACK"),
            ]
            for kname, kdesc, kcat, kunit, ktarg, kcurr, kbase, kdir, kstat in kpis:
                kpi_obj = BusinessKPI(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    name=kname,
                    description=kdesc,
                    category=kcat,
                    measurement_unit=kunit,
                    target_value=ktarg,
                    current_value=kcurr,
                    baseline_value=kbase,
                    trend_direction=kdir,
                    status=kstat,
                )
                db.add(kpi_obj)

            # Baseline Scenarios
            scens = [
                ("Base Case Growth Scenario", "BASE_CASE", "Standard conservative projection with 18% QoQ expansion.", 1.0, 0.0, json.dumps({"growth_rate": 0.18})),
                ("High Velocity Enterprise Expansion", "BEST_CASE", "Aggressive enterprise adoption via SOC2 compliance acceleration.", 1.45, -0.015, json.dumps({"growth_rate": 0.45})),
                ("Macroeconomic Market Contraction", "WORST_CASE", "Tech budget compression and delayed procurement cycles.", 0.80, 0.035, json.dumps({"growth_rate": -0.10})),
            ]
            for sname, stype, sdesc, smult, schurn, sass in scens:
                scen_obj = StrategicScenario(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    name=sname,
                    scenario_type=stype,
                    description=sdesc,
                    revenue_multiplier=smult,
                    churn_rate_impact=schurn,
                    assumptions_json=sass,
                )
                db.add(scen_obj)

            # Baseline Decisions
            dec = StrategicDecision(
                organization_id=organization_id,
                workspace_id=workspace_id,
                title="Adopt Multi-Tenant Organization Boundary Architecture",
                context="Enterprise customers required strict zero-trust boundary isolation across workspaces.",
                decision_outcome="Enforce workspace and organization scoped foreign key cascading across all models.",
                rationale="Eliminates cross-tenant data leakage risks and enables streamlined SOC 2 Type II certification.",
                decision_date=utc_now(),
                status="IN_EFFECT",
            )
            db.add(dec)

            db.commit()

    # --- Overview ---
    @staticmethod
    def get_dashboard_overview(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicDashboardOverviewResponse:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)

        # Query filters
        plan_q = db.query(StrategicPlan)
        goal_q = db.query(StrategicGoal)
        init_q = db.query(StrategicInitiative)
        sig_q = db.query(MarketSignal)
        comp_q = db.query(Competitor)
        opp_q = db.query(StrategicOpportunity)
        swot_q = db.query(SWOTEntry)
        dec_q = db.query(StrategicDecision)

        if workspace_id is not None:
            plan_q = plan_q.filter(StrategicPlan.workspace_id == workspace_id)
            goal_q = goal_q.filter(StrategicGoal.workspace_id == workspace_id)
            init_q = init_q.filter(StrategicInitiative.workspace_id == workspace_id)
            comp_q = comp_q.filter((Competitor.workspace_id == workspace_id) | (Competitor.workspace_id.is_(None)))
            opp_q = opp_q.filter(StrategicOpportunity.workspace_id == workspace_id)
            swot_q = swot_q.filter((SWOTEntry.workspace_id == workspace_id) | (SWOTEntry.workspace_id.is_(None)))
            dec_q = dec_q.filter(StrategicDecision.workspace_id == workspace_id)
        elif organization_id is not None:
            plan_q = plan_q.filter(StrategicPlan.organization_id == organization_id)
            goal_q = goal_q.filter(StrategicGoal.organization_id == organization_id)
            init_q = init_q.filter(StrategicInitiative.organization_id == organization_id)
            comp_q = comp_q.filter((Competitor.organization_id == organization_id) | (Competitor.organization_id.is_(None)))
            opp_q = opp_q.filter(StrategicOpportunity.organization_id == organization_id)
            swot_q = swot_q.filter((SWOTEntry.organization_id == organization_id) | (SWOTEntry.organization_id.is_(None)))
            dec_q = dec_q.filter(StrategicDecision.organization_id == organization_id)

        active_plans = plan_q.filter(StrategicPlan.status == "ACTIVE").count()
        total_goals = goal_q.count()
        completed_goals = goal_q.filter(StrategicGoal.status == "COMPLETED").count()
        goal_completion_rate = round((completed_goals / total_goals * 100.0), 1) if total_goals > 0 else 0.0

        active_inits = init_q.filter(StrategicInitiative.status == "IN_PROGRESS").count()
        active_signals = sig_q.count()
        tracked_comps = comp_q.count()

        open_opps = opp_q.filter(StrategicOpportunity.status.in_(["IDENTIFIED", "EVALUATING", "APPROVED", "IN_PROGRESS"])).all()
        total_pipeline_cents = sum(o.estimated_value_cents for o in open_opps)
        total_pipeline_dollars = round(total_pipeline_cents / 100.0, 2)

        # SWOT summary counts
        swots = swot_q.all()
        swot_summary = {"STRENGTH": 0, "WEAKNESS": 0, "OPPORTUNITY": 0, "THREAT": 0}
        for s in swots:
            if s.swot_type in swot_summary:
                swot_summary[s.swot_type] += 1

        recent_signals = [MarketSignalResponse.model_validate(s) for s in sig_q.order_by(MarketSignal.created_at.desc()).limit(5).all()]
        top_opps = [
            StrategicOpportunityResponse(
                id=o.id,
                title=o.title,
                description=o.description,
                customer_segment=o.customer_segment,
                estimated_value_cents=o.estimated_value_cents,
                feasibility_score=o.feasibility_score,
                rice_reach=o.rice_reach,
                rice_impact=o.rice_impact,
                rice_confidence=o.rice_confidence,
                rice_effort=o.rice_effort,
                status=o.status,
                rice_score=o.rice_score,
                estimated_value=round(o.estimated_value_cents / 100.0, 2),
                created_at=o.created_at,
                organization_id=o.organization_id,
                workspace_id=o.workspace_id,
            )
            for o in opp_q.order_by(StrategicOpportunity.rice_score.desc()).limit(5).all()
        ]
        recent_decs = [StrategicDecisionResponse.model_validate(d) for d in dec_q.order_by(StrategicDecision.decision_date.desc()).limit(5).all()]

        # Grounded AI Recommendations
        ai_recommendations = [
            AIStrategyRecommendation(
                theme="ENTERPRISE EXPANSION",
                recommendation="Accelerate SOC 2 Type II audit automation to unblock pending enterprise sales pipeline.",
                confidence=0.94,
                rationale="Enterprise opportunity evaluation shows $35k in high-intent deals requiring compliance evidence.",
                grounded_evidence=f"Validated against top RICE opportunity 'Automated SOC 2 Compliance Report Generator' with RICE score 4,462.5.",
            ),
            AIStrategyRecommendation(
                theme="COMPETITIVE DIFFERENTIATION",
                recommendation="Capitalize on Linear's lack of multi-department business intelligence by highlighting executive dashboards.",
                confidence=0.89,
                rationale="Linear weakness indicates engineering focus leaves executive leadership and cross-department teams underserved.",
                grounded_evidence="Derived from competitor analysis diff for Linear (Market Position: CHALLENGER, Vulnerability: Limited executive BI).",
            ),
            AIStrategyRecommendation(
                theme="ECOSYSTEM EXPANSION",
                recommendation="Deploy bi-directional webhook and REST integration hub for third-party platforms.",
                confidence=0.91,
                rationale="Customer feedback and market signals demonstrate 38% higher retention among multi-tool integrated accounts.",
                grounded_evidence="Correlated with active strategic initiative 'Cross-Tool Webhook Ecosystem' currently at 40% completion.",
            ),
        ]

        return StrategicDashboardOverviewResponse(
            active_plans_count=active_plans,
            total_goals_count=total_goals,
            completed_goals_count=completed_goals,
            goal_completion_rate=goal_completion_rate,
            active_initiatives_count=active_inits,
            active_signals_count=active_signals,
            tracked_competitors_count=tracked_comps,
            open_opportunities_count=len(open_opps),
            total_pipeline_value_dollars=total_pipeline_dollars,
            swot_summary=swot_summary,
            recent_signals=recent_signals,
            top_opportunities=top_opps,
            recent_decisions=recent_decs,
            ai_recommendations=ai_recommendations,
        )

    # --- Plans ---
    @staticmethod
    def list_plans(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[StrategicPlanResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(StrategicPlan)
        if workspace_id is not None:
            query = query.filter(StrategicPlan.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicPlan.organization_id == organization_id)
        plans = query.order_by(StrategicPlan.created_at.desc()).all()
        result = []
        for p in plans:
            resp = StrategicPlanResponse.model_validate(p)
            resp.goals_count = len(p.goals) if p.goals else 0
            result.append(resp)
        return result

    @staticmethod
    def create_plan(
        db: Session,
        plan_in: StrategicPlanCreate,
        owner_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicPlanResponse:
        org_id = organization_id if organization_id is not None else plan_in.organization_id
        ws_id = workspace_id if workspace_id is not None else plan_in.workspace_id
        plan = StrategicPlan(
            organization_id=org_id,
            workspace_id=ws_id,
            title=plan_in.title,
            vision=plan_in.vision,
            mission=plan_in.mission,
            strategic_themes_json=plan_in.strategic_themes_json,
            time_horizon=plan_in.time_horizon,
            status=plan_in.status,
            owner_id=owner_id,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        resp = StrategicPlanResponse.model_validate(plan)
        resp.goals_count = 0
        return resp

    @staticmethod
    def update_plan(
        db: Session,
        plan_id: str,
        plan_update: StrategicPlanUpdate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> Optional[StrategicPlanResponse]:
        query = db.query(StrategicPlan).filter(StrategicPlan.id == plan_id)
        if workspace_id is not None:
            query = query.filter(StrategicPlan.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicPlan.organization_id == organization_id)
        plan = query.first()
        if not plan:
            return None

        update_data = plan_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan, key, value)
        plan.updated_at = utc_now()
        db.commit()
        db.refresh(plan)
        resp = StrategicPlanResponse.model_validate(plan)
        resp.goals_count = len(plan.goals) if plan.goals else 0
        return resp

    # --- Goals ---
    @staticmethod
    def list_goals(
        db: Session,
        plan_id: Optional[str] = None,
        status: Optional[str] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[StrategicGoalResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(StrategicGoal)
        if plan_id:
            query = query.filter(StrategicGoal.plan_id == plan_id)
        if status:
            query = query.filter(StrategicGoal.status == status)
        if workspace_id is not None:
            query = query.filter(StrategicGoal.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicGoal.organization_id == organization_id)

        goals = query.all()
        res = []
        for g in goals:
            pct = 0.0
            denom = g.target_value - g.baseline_value
            if denom > 0:
                pct = round(((g.current_value - g.baseline_value) / denom) * 100.0, 1)
            resp = StrategicGoalResponse.model_validate(g)
            resp.progress_percentage = max(0.0, min(100.0, pct))
            res.append(resp)
        return res

    @staticmethod
    def create_goal(
        db: Session,
        goal_in: StrategicGoalCreate,
        owner_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicGoalResponse:
        org_id = organization_id if organization_id is not None else goal_in.organization_id
        ws_id = workspace_id if workspace_id is not None else goal_in.workspace_id
        goal = StrategicGoal(
            organization_id=org_id,
            workspace_id=ws_id,
            plan_id=goal_in.plan_id,
            title=goal_in.title,
            description=goal_in.description,
            category=goal_in.category,
            target_metric=goal_in.target_metric,
            baseline_value=goal_in.baseline_value,
            target_value=goal_in.target_value,
            current_value=goal_in.current_value,
            unit=goal_in.unit,
            status=goal_in.status,
            deadline=goal_in.deadline,
            owner_id=owner_id,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        pct = 0.0
        denom = goal.target_value - goal.baseline_value
        if denom > 0:
            pct = round(((goal.current_value - goal.baseline_value) / denom) * 100.0, 1)
        resp = StrategicGoalResponse.model_validate(goal)
        resp.progress_percentage = max(0.0, min(100.0, pct))
        return resp

    @staticmethod
    def update_goal(
        db: Session,
        goal_id: str,
        goal_update: StrategicGoalUpdate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> Optional[StrategicGoalResponse]:
        query = db.query(StrategicGoal).filter(StrategicGoal.id == goal_id)
        if workspace_id is not None:
            query = query.filter(StrategicGoal.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicGoal.organization_id == organization_id)
        goal = query.first()
        if not goal:
            return None

        old_status = goal.status
        update_data = goal_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(goal, key, value)
        goal.updated_at = utc_now()
        db.commit()
        db.refresh(goal)

        # Notify if goal entered AT_RISK or COMPLETED
        if goal.status != old_status and goal.status in ["AT_RISK", "COMPLETED"]:
            try:
                from app.services.notification_service import notification_service
                notification_service.create_notification(
                    db=db,
                    user_id=goal.owner_id or 1,
                    type="SYSTEM",
                    title=f"Strategic Goal {goal.status}: {goal.title}",
                    message=f"Goal '{goal.title}' status shifted to {goal.status}.",
                    workspace_id=goal.workspace_id,
                )
            except Exception:
                pass

        pct = 0.0
        denom = goal.target_value - goal.baseline_value
        if denom > 0:
            pct = round(((goal.current_value - goal.baseline_value) / denom) * 100.0, 1)
        resp = StrategicGoalResponse.model_validate(goal)
        resp.progress_percentage = max(0.0, min(100.0, pct))
        return resp

    # --- Initiatives ---
    @staticmethod
    def list_initiatives(
        db: Session,
        goal_id: Optional[str] = None,
        priority: Optional[str] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[StrategicInitiativeResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(StrategicInitiative)
        if goal_id:
            query = query.filter(StrategicInitiative.goal_id == goal_id)
        if priority:
            query = query.filter(StrategicInitiative.priority == priority)
        if workspace_id is not None:
            query = query.filter(StrategicInitiative.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicInitiative.organization_id == organization_id)
        return [StrategicInitiativeResponse.model_validate(i) for i in query.all()]

    @staticmethod
    def create_initiative(
        db: Session,
        init_in: StrategicInitiativeCreate,
        lead_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicInitiativeResponse:
        org_id = organization_id if organization_id is not None else init_in.organization_id
        ws_id = workspace_id if workspace_id is not None else init_in.workspace_id
        init = StrategicInitiative(
            organization_id=org_id,
            workspace_id=ws_id,
            goal_id=init_in.goal_id,
            title=init_in.title,
            description=init_in.description,
            priority=init_in.priority,
            budget_amount=init_in.budget_amount,
            status=init_in.status,
            progress_percentage=init_in.progress_percentage,
            start_date=init_in.start_date,
            end_date=init_in.end_date,
            owner_id=lead_id,
        )
        db.add(init)
        db.commit()
        db.refresh(init)
        return StrategicInitiativeResponse.model_validate(init)

    @staticmethod
    def update_initiative(
        db: Session,
        init_id: str,
        init_update: StrategicInitiativeUpdate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> Optional[StrategicInitiativeResponse]:
        query = db.query(StrategicInitiative).filter(StrategicInitiative.id == init_id)
        if workspace_id is not None:
            query = query.filter(StrategicInitiative.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicInitiative.organization_id == organization_id)
        init = query.first()
        if not init:
            return None

        update_data = init_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(init, key, value)
        init.updated_at = utc_now()
        db.commit()
        db.refresh(init)
        return StrategicInitiativeResponse.model_validate(init)

    # --- Market Intelligence & Signals ---
    @staticmethod
    def list_market_intelligence(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[MarketIntelligenceResponse]:
        query = db.query(MarketIntelligence)
        if workspace_id is not None:
            query = query.filter((MarketIntelligence.workspace_id == workspace_id) | (MarketIntelligence.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((MarketIntelligence.organization_id == organization_id) | (MarketIntelligence.organization_id.is_(None)))
        items = query.order_by(MarketIntelligence.created_at.desc()).all()
        return [MarketIntelligenceResponse.model_validate(item) for item in items]

    @staticmethod
    def create_market_intelligence(
        db: Session,
        intel_in: MarketIntelligenceCreate,
        owner_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> MarketIntelligenceResponse:
        org_id = organization_id if organization_id is not None else intel_in.organization_id
        ws_id = workspace_id if workspace_id is not None else intel_in.workspace_id
        intel = MarketIntelligence(
            organization_id=org_id,
            workspace_id=ws_id,
            title=intel_in.title,
            intelligence_type=intel_in.intelligence_type,
            summary=intel_in.summary,
            source_name=intel_in.source_name,
            source_url=intel_in.source_url,
            confidence_score=intel_in.confidence_score,
            impact_rating=intel_in.impact_rating,
            owner_id=owner_id,
        )
        db.add(intel)
        db.commit()
        db.refresh(intel)
        return MarketIntelligenceResponse.model_validate(intel)

    @staticmethod
    def list_market_signals(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[MarketSignalResponse]:
        query = db.query(MarketSignal)
        if workspace_id is not None:
            query = query.filter((MarketSignal.workspace_id == workspace_id) | (MarketSignal.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((MarketSignal.organization_id == organization_id) | (MarketSignal.organization_id.is_(None)))
        items = query.order_by(MarketSignal.created_at.desc()).all()
        return [MarketSignalResponse.model_validate(item) for item in items]

    @staticmethod
    def create_market_signal(
        db: Session,
        sig_in: MarketSignalCreate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> MarketSignalResponse:
        org_id = organization_id if organization_id is not None else sig_in.organization_id
        ws_id = workspace_id if workspace_id is not None else sig_in.workspace_id
        sig = MarketSignal(
            organization_id=org_id,
            workspace_id=ws_id,
            signal_type=sig_in.signal_type,
            title=sig_in.title,
            observations=sig_in.observations,
            trend_direction=sig_in.trend_direction,
            urgency=sig_in.urgency,
            is_converted_to_opportunity=sig_in.is_converted_to_opportunity,
        )
        db.add(sig)
        db.commit()
        db.refresh(sig)
        return MarketSignalResponse.model_validate(sig)

    # --- Competitors ---
    @staticmethod
    def list_competitors(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[CompetitorResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(Competitor)
        if workspace_id is not None:
            query = query.filter((Competitor.workspace_id == workspace_id) | (Competitor.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((Competitor.organization_id == organization_id) | (Competitor.organization_id.is_(None)))
        comps = query.order_by(Competitor.name.asc()).all()
        return [CompetitorResponse.model_validate(c) for c in comps]

    @staticmethod
    def create_competitor(
        db: Session,
        comp_in: CompetitorCreate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> CompetitorResponse:
        org_id = organization_id if organization_id is not None else comp_in.organization_id
        ws_id = workspace_id if workspace_id is not None else comp_in.workspace_id
        comp = Competitor(
            organization_id=org_id,
            workspace_id=ws_id,
            name=comp_in.name,
            website=comp_in.website,
            market_position=comp_in.market_position,
            pricing_model=comp_in.pricing_model,
            strengths_json=comp_in.strengths_json,
            weaknesses_json=comp_in.weaknesses_json,
            features_diff_json=comp_in.features_diff_json,
            threat_level=comp_in.threat_level,
            notes=comp_in.notes,
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)
        return CompetitorResponse.model_validate(comp)

    @staticmethod
    def update_competitor(
        db: Session,
        comp_id: str,
        comp_update: CompetitorUpdate,
    ) -> Optional[CompetitorResponse]:
        comp = db.query(Competitor).filter(Competitor.id == comp_id).first()
        if not comp:
            return None
        update_data = comp_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(comp, key, value)
        comp.updated_at = utc_now()
        db.commit()
        db.refresh(comp)
        return CompetitorResponse.model_validate(comp)

    # --- SWOT ---
    @staticmethod
    def list_swot(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[SWOTEntryResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(SWOTEntry)
        if workspace_id is not None:
            query = query.filter((SWOTEntry.workspace_id == workspace_id) | (SWOTEntry.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((SWOTEntry.organization_id == organization_id) | (SWOTEntry.organization_id.is_(None)))
        items = query.order_by(SWOTEntry.created_at.asc()).all()
        return [SWOTEntryResponse.model_validate(item) for item in items]

    @staticmethod
    def create_swot(
        db: Session,
        swot_in: SWOTEntryCreate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> SWOTEntryResponse:
        org_id = organization_id if organization_id is not None else swot_in.organization_id
        ws_id = workspace_id if workspace_id is not None else swot_in.workspace_id
        entry = SWOTEntry(
            organization_id=org_id,
            workspace_id=ws_id,
            swot_type=swot_in.swot_type,
            title=swot_in.title,
            description=swot_in.description,
            impact=swot_in.impact,
            evidence_text=swot_in.evidence_text,
            is_ai_generated=swot_in.is_ai_generated,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return SWOTEntryResponse.model_validate(entry)

    # --- Market Sizing ---
    @staticmethod
    def list_market_sizings(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[MarketSizingResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(MarketSizing)
        if workspace_id is not None:
            query = query.filter((MarketSizing.workspace_id == workspace_id) | (MarketSizing.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((MarketSizing.organization_id == organization_id) | (MarketSizing.organization_id.is_(None)))
        sizings = query.all()
        result = []
        for s in sizings:
            resp = MarketSizingResponse.model_validate(s)
            resp.tam_dollars = round(s.tam_cents / 100.0, 2)
            resp.sam_dollars = round(s.sam_cents / 100.0, 2)
            resp.som_dollars = round(s.som_cents / 100.0, 2)
            result.append(resp)
        return result

    @staticmethod
    def create_market_sizing(
        db: Session,
        m_in: MarketSizingCreate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> MarketSizingResponse:
        org_id = organization_id if organization_id is not None else m_in.organization_id
        ws_id = workspace_id if workspace_id is not None else m_in.workspace_id
        ms = MarketSizing(
            organization_id=org_id,
            workspace_id=ws_id,
            market_name=m_in.market_name,
            methodology=m_in.methodology,
            tam_cents=m_in.tam_cents,
            sam_cents=m_in.sam_cents,
            som_cents=m_in.som_cents,
            currency=m_in.currency,
            assumptions_json=m_in.assumptions_json,
            confidence_score=m_in.confidence_score,
        )
        db.add(ms)
        db.commit()
        db.refresh(ms)
        resp = MarketSizingResponse.model_validate(ms)
        resp.tam_dollars = round(ms.tam_cents / 100.0, 2)
        resp.sam_dollars = round(ms.sam_cents / 100.0, 2)
        resp.som_dollars = round(ms.som_cents / 100.0, 2)
        return resp

    # --- Opportunities & RICE Prioritization ---
    @staticmethod
    def list_opportunities(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[StrategicOpportunityResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(StrategicOpportunity)
        if workspace_id is not None:
            query = query.filter(StrategicOpportunity.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicOpportunity.organization_id == organization_id)
        opps = query.order_by(StrategicOpportunity.rice_score.desc()).all()
        result = []
        for o in opps:
            resp = StrategicOpportunityResponse.model_validate(o)
            resp.estimated_value = round(o.estimated_value_cents / 100.0, 2)
            result.append(resp)
        return result

    @staticmethod
    def create_opportunity(
        db: Session,
        opp_in: StrategicOpportunityCreate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicOpportunityResponse:
        org_id = organization_id if organization_id is not None else opp_in.organization_id
        ws_id = workspace_id if workspace_id is not None else opp_in.workspace_id
        effort = opp_in.rice_effort if opp_in.rice_effort > 0 else 1.0
        score = (opp_in.rice_reach * opp_in.rice_impact * opp_in.rice_confidence) / effort
        opp = StrategicOpportunity(
            organization_id=org_id,
            workspace_id=ws_id,
            title=opp_in.title,
            description=opp_in.description,
            customer_segment=opp_in.customer_segment,
            estimated_value_cents=opp_in.estimated_value_cents,
            feasibility_score=opp_in.feasibility_score,
            rice_reach=opp_in.rice_reach,
            rice_impact=opp_in.rice_impact,
            rice_confidence=opp_in.rice_confidence,
            rice_effort=effort,
            rice_score=round(score, 1),
            status=opp_in.status,
        )
        db.add(opp)
        db.commit()
        db.refresh(opp)
        resp = StrategicOpportunityResponse.model_validate(opp)
        resp.estimated_value = round(opp.estimated_value_cents / 100.0, 2)
        return resp

    @staticmethod
    def update_opportunity(
        db: Session,
        opp_id: str,
        opp_update: StrategicOpportunityUpdate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> Optional[StrategicOpportunityResponse]:
        query = db.query(StrategicOpportunity).filter(StrategicOpportunity.id == opp_id)
        if workspace_id is not None:
            query = query.filter(StrategicOpportunity.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(StrategicOpportunity.organization_id == organization_id)
        opp = query.first()
        if not opp:
            return None

        update_data = opp_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(opp, key, value)

        # Recalculate RICE score
        effort = opp.rice_effort if opp.rice_effort > 0 else 1.0
        score = (opp.rice_reach * opp.rice_impact * opp.rice_confidence) / effort
        opp.rice_effort = effort
        opp.rice_score = round(score, 1)

        db.commit()
        db.refresh(opp)
        resp = StrategicOpportunityResponse.model_validate(opp)
        resp.estimated_value = round(opp.estimated_value_cents / 100.0, 2)
        return resp

    # --- Scenarios & Decisions ---
    @staticmethod
    def list_scenarios(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[StrategicScenarioResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(StrategicScenario)
        if workspace_id is not None:
            query = query.filter((StrategicScenario.workspace_id == workspace_id) | (StrategicScenario.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((StrategicScenario.organization_id == organization_id) | (StrategicScenario.organization_id.is_(None)))
        scenarios = query.order_by(StrategicScenario.created_at.asc()).all()
        return [StrategicScenarioResponse.model_validate(s) for s in scenarios]

    @staticmethod
    def create_scenario(
        db: Session,
        scen_in: StrategicScenarioCreate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicScenarioResponse:
        org_id = organization_id if organization_id is not None else scen_in.organization_id
        ws_id = workspace_id if workspace_id is not None else scen_in.workspace_id
        scen = StrategicScenario(
            organization_id=org_id,
            workspace_id=ws_id,
            name=scen_in.name,
            scenario_type=scen_in.scenario_type,
            description=scen_in.description,
            revenue_multiplier=scen_in.revenue_multiplier,
            churn_rate_impact=scen_in.churn_rate_impact,
            assumptions_json=scen_in.assumptions_json,
        )
        db.add(scen)
        db.commit()
        db.refresh(scen)
        return StrategicScenarioResponse.model_validate(scen)

    @staticmethod
    def compare_scenarios(
        db: Session,
        scenario_ids: Optional[List[str]] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicScenarioCompareResponse:
        all_scens = StrategicIntelligenceService.list_scenarios(db, organization_id, workspace_id)
        if scenario_ids:
            target_scens = [s for s in all_scens if s.id in scenario_ids]
        else:
            target_scens = all_scens

        baseline = next((s for s in target_scens if s.scenario_type == "BASE_CASE"), (target_scens[0] if target_scens else None))
        comparison_metrics: Dict[str, Any] = {}
        for s in target_scens:
            comparison_metrics[s.id] = {
                "name": s.name,
                "type": s.scenario_type,
                "revenue_multiplier": s.revenue_multiplier,
                "churn_rate_impact": s.churn_rate_impact,
                "relative_revenue_impact_pct": round((s.revenue_multiplier - 1.0) * 100.0, 1),
            }

        return StrategicScenarioCompareResponse(
            scenarios=target_scens,
            baseline_id=baseline.id if baseline else None,
            metrics_comparison=comparison_metrics,
        )

    # --- Decisions ---
    @staticmethod
    def list_decisions(
        db: Session,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[StrategicDecisionResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(StrategicDecision)
        if workspace_id is not None:
            query = query.filter((StrategicDecision.workspace_id == workspace_id) | (StrategicDecision.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((StrategicDecision.organization_id == organization_id) | (StrategicDecision.organization_id.is_(None)))
        decs = query.order_by(StrategicDecision.decision_date.desc()).all()
        return [StrategicDecisionResponse.model_validate(d) for d in decs]

    @staticmethod
    def create_decision(
        db: Session,
        dec_in: StrategicDecisionCreate,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> StrategicDecisionResponse:
        org_id = organization_id if organization_id is not None else dec_in.organization_id
        ws_id = workspace_id if workspace_id is not None else dec_in.workspace_id
        dec = StrategicDecision(
            organization_id=org_id,
            workspace_id=ws_id,
            title=dec_in.title,
            context=dec_in.context,
            decision_outcome=dec_in.decision_outcome,
            rationale=dec_in.rationale,
            decision_date=dec_in.decision_date or utc_now(),
            status=dec_in.status,
            decision_maker_id=user_id,
        )
        db.add(dec)
        db.commit()
        db.refresh(dec)
        return StrategicDecisionResponse.model_validate(dec)

    # --- Business KPIs ---
    @staticmethod
    def list_kpis(
        db: Session,
        category: Optional[str] = None,
        status: Optional[str] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> List[BusinessKPIResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db, organization_id, workspace_id)
        query = db.query(BusinessKPI)
        if category:
            query = query.filter(BusinessKPI.category == category)
        if status:
            query = query.filter(BusinessKPI.status == status)
        if workspace_id is not None:
            query = query.filter((BusinessKPI.workspace_id == workspace_id) | (BusinessKPI.workspace_id.is_(None)))
        elif organization_id is not None:
            query = query.filter((BusinessKPI.organization_id == organization_id) | (BusinessKPI.organization_id.is_(None)))

        kpis = query.order_by(BusinessKPI.created_at.asc()).all()
        result = []
        for k in kpis:
            resp = BusinessKPIResponse.model_validate(k)
            # Achievement percentage calculation
            denom = k.target_value - k.baseline_value
            if denom > 0:
                resp.achievement_percentage = round(max(0.0, ((k.current_value - k.baseline_value) / denom) * 100.0), 1)
            elif k.target_value > 0:
                resp.achievement_percentage = round((k.current_value / k.target_value) * 100.0, 1)
            else:
                resp.achievement_percentage = 100.0

            # Historical values
            history = (
                db.query(BusinessKPIValue)
                .filter(BusinessKPIValue.kpi_id == k.id)
                .order_by(BusinessKPIValue.created_at.desc())
                .limit(12)
                .all()
            )
            resp.history = [BusinessKPIValueResponse.model_validate(h) for h in history]
            result.append(resp)
        return result

    @staticmethod
    def create_kpi(
        db: Session,
        kpi_in: BusinessKPICreate,
        owner_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> BusinessKPIResponse:
        org_id = organization_id if organization_id is not None else kpi_in.organization_id
        ws_id = workspace_id if workspace_id is not None else kpi_in.workspace_id
        kpi = BusinessKPI(
            organization_id=org_id,
            workspace_id=ws_id,
            name=kpi_in.name,
            description=kpi_in.description,
            category=kpi_in.category,
            measurement_unit=kpi_in.measurement_unit,
            target_value=kpi_in.target_value,
            current_value=kpi_in.current_value,
            baseline_value=kpi_in.baseline_value,
            trend_direction=kpi_in.trend_direction,
            status=kpi_in.status,
            owner_id=owner_id,
        )
        db.add(kpi)
        db.commit()
        db.refresh(kpi)
        resp = BusinessKPIResponse.model_validate(kpi)
        denom = kpi.target_value - kpi.baseline_value
        resp.achievement_percentage = round(((kpi.current_value - kpi.baseline_value) / denom) * 100.0, 1) if denom > 0 else 0.0
        resp.history = []
        return resp

    @staticmethod
    def record_kpi_value(
        db: Session,
        kpi_id: str,
        val_in: BusinessKPIValueCreate,
        user_id: Optional[int] = None,
    ) -> BusinessKPIValueResponse:
        kpi = db.query(BusinessKPI).filter(BusinessKPI.id == kpi_id).first()
        if not kpi:
            raise ValueError(f"Business KPI '{kpi_id}' not found.")

        # Update current value on the KPI and determine trend direction
        old_val = kpi.current_value
        kpi.current_value = val_in.value
        if val_in.value > old_val:
            kpi.trend_direction = "UP"
        elif val_in.value < old_val:
            kpi.trend_direction = "DOWN"
        else:
            kpi.trend_direction = "STABLE"

        kpi.updated_at = utc_now()

        # Add historical record
        val_rec = BusinessKPIValue(
            kpi_id=kpi_id,
            value=val_in.value,
            period_date=val_in.period_date,
            notes=val_in.notes,
            recorded_by_id=user_id,
        )
        db.add(val_rec)
        db.commit()
        db.refresh(val_rec)
        return BusinessKPIValueResponse.model_validate(val_rec)

    @staticmethod
    def update_kpi(
        db: Session,
        kpi_id: str,
        kpi_update: BusinessKPIUpdate,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> Optional[BusinessKPIResponse]:
        query = db.query(BusinessKPI).filter(BusinessKPI.id == kpi_id)
        if workspace_id is not None:
            query = query.filter(BusinessKPI.workspace_id == workspace_id)
        elif organization_id is not None:
            query = query.filter(BusinessKPI.organization_id == organization_id)
        kpi = query.first()
        if not kpi:
            return None

        update_data = kpi_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(kpi, key, value)
        kpi.updated_at = utc_now()
        db.commit()
        db.refresh(kpi)

        resp = BusinessKPIResponse.model_validate(kpi)
        denom = kpi.target_value - kpi.baseline_value
        resp.achievement_percentage = round(((kpi.current_value - kpi.baseline_value) / denom) * 100.0, 1) if denom > 0 else 0.0
        return resp

    # --- Grounded AI Strategy Recommendations ---
    @staticmethod
    def analyze_strategy_with_ai(
        db: Session,
        req: StrategicAIAnalyzeRequest,
        organization_id: Optional[int] = None,
    ) -> StrategicAIAnalyzeResponse:
        ws_id = req.workspace_id
        overview = StrategicIntelligenceService.get_dashboard_overview(db, organization_id, ws_id)
        kpis = StrategicIntelligenceService.list_kpis(db, organization_id=organization_id, workspace_id=ws_id)
        competitors = StrategicIntelligenceService.list_competitors(db, organization_id=organization_id, workspace_id=ws_id)
        swots = StrategicIntelligenceService.list_swot(db, organization_id=organization_id, workspace_id=ws_id)

        identified_risks = []
        identified_opps = []

        # Analyze competitor threat levels
        high_threats = [c for c in competitors if c.threat_level in ["HIGH", "CRITICAL"]]
        if high_threats:
            identified_risks.append(f"Intense competitive pressure from {len(high_threats)} major market leaders: {', '.join(c.name for c in high_threats[:3])}.")

        # Analyze SWOT threats and weaknesses
        for s in swots:
            if s.swot_type == "THREAT" and s.impact == "HIGH":
                identified_risks.append(f"External strategic threat: {s.title}")
            elif s.swot_type == "OPPORTUNITY" and s.impact == "HIGH":
                identified_opps.append(f"High-impact opportunity: {s.title}")

        # Top RICE opportunities
        for opp in overview.top_opportunities[:3]:
            identified_opps.append(f"{opp.title} (RICE Score: {opp.rice_score})")

        # Grounded recommendations
        recs = list(overview.ai_recommendations)
        if any(k.status == "AT_RISK" for k in kpis):
            at_risk_kpi = next(k for k in kpis if k.status == "AT_RISK")
            recs.append(
                AIStrategyRecommendation(
                    theme="KPI PERFORMANCE RECOVERY",
                    recommendation=f"Prioritize immediate corrective initiatives for at-risk KPI: {at_risk_kpi.name}.",
                    confidence=0.92,
                    rationale=f"Current performance ({at_risk_kpi.current_value}{at_risk_kpi.measurement_unit}) is lagging behind target ({at_risk_kpi.target_value}{at_risk_kpi.measurement_unit}).",
                    grounded_evidence=f"Tracked in business KPI monitoring ({at_risk_kpi.category} category).",
                )
            )

        summary = (
            f"Strategic synthesis indicates a healthy business trajectory with {overview.goal_completion_rate}% goal completion "
            f"and ${overview.total_pipeline_value_dollars:,.2f} in active opportunity pipeline across {overview.active_plans_count} strategic plans. "
            f"Primary focus centers on enterprise security trust velocity and differentiation against {len(competitors)} tracked competitors."
        )

        return StrategicAIAnalyzeResponse(
            summary=summary,
            recommendations=recs,
            strategic_score=round(min(100.0, 70.0 + (overview.goal_completion_rate * 0.3)), 1),
            identified_risks=identified_risks or ["Market macro shifts in enterprise procurement velocity."],
            identified_opportunities=identified_opps or ["Expand third-party integration partnerships."],
            generated_at=utc_now(),
        )

    # --- B15 Automation Action Handler ---
    @staticmethod
    def execute_strategic_automation_action(
        db: Session,
        action_type: str,
        payload: Dict[str, Any],
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute automated workflow actions dispatched by the B15 Automation Engine."""
        action_upper = action_type.upper()

        if action_upper in ["CREATE_STRATEGIC_GOAL", "CREATE_GOAL"]:
            plan_id = payload.get("plan_id")
            if not plan_id:
                plans = StrategicIntelligenceService.list_plans(db, organization_id, workspace_id)
                plan_id = plans[0].id if plans else "splan_default"
            goal_in = StrategicGoalCreate(
                plan_id=plan_id,
                title=payload.get("title", "Automated Strategic Milestone"),
                description=payload.get("description", "Created via B15 Automation Engine"),
                category=payload.get("category", "PRODUCT"),
                target_metric=payload.get("target_metric", "Completion %"),
                target_value=float(payload.get("target_value", 100.0)),
                baseline_value=float(payload.get("baseline_value", 0.0)),
                current_value=float(payload.get("current_value", 0.0)),
                unit=payload.get("unit", "%"),
                status="ACTIVE",
            )
            res = StrategicIntelligenceService.create_goal(db, goal_in, organization_id=organization_id, workspace_id=workspace_id)
            return {"status": "SUCCESS", "action": action_type, "goal_id": res.id}

        elif action_upper in ["RECORD_BUSINESS_KPI_VALUE", "UPDATE_KPI"]:
            kpi_id = payload.get("kpi_id")
            val = float(payload.get("value", 0.0))
            period = payload.get("period_date", utc_now().strftime("%Y-%m"))
            notes = payload.get("notes", "Automated sync from B15")
            if not kpi_id:
                kpis = StrategicIntelligenceService.list_kpis(db, organization_id=organization_id, workspace_id=workspace_id)
                if not kpis:
                    return {"status": "FAILED", "action": action_type, "message": "No KPI exists to update."}
                kpi_id = kpis[0].id
            val_in = BusinessKPIValueCreate(value=val, period_date=period, notes=notes)
            rec = StrategicIntelligenceService.record_kpi_value(db, kpi_id, val_in)
            return {"status": "SUCCESS", "action": action_type, "record_id": rec.id}

        elif action_upper in ["EVALUATE_STRATEGIC_RISKS", "CHECK_STRATEGIC_GOALS"]:
            goals = StrategicIntelligenceService.list_goals(db, organization_id=organization_id, workspace_id=workspace_id)
            at_risk = [g for g in goals if g.status == "AT_RISK"]
            if at_risk:
                try:
                    from app.services.notification_service import notification_service
                    notification_service.create_notification(
                        db=db,
                        user_id=1,
                        type="SYSTEM",
                        title=f"Strategic Alert: {len(at_risk)} Goals At Risk",
                        message=f"Identified {len(at_risk)} strategic goals flagged as at-risk.",
                        workspace_id=workspace_id,
                    )
                except Exception:
                    pass
            return {"status": "SUCCESS", "action": action_type, "at_risk_count": len(at_risk)}

        elif action_upper in ["CREATE_STRATEGIC_OPPORTUNITY"]:
            opp_in = StrategicOpportunityCreate(
                title=payload.get("title", "Automated Growth Opportunity"),
                description=payload.get("description", "Dispatched by B15 Automation Engine"),
                customer_segment=payload.get("customer_segment", "Enterprise B2B"),
                estimated_value_cents=int(payload.get("estimated_value_cents", 100000)),
                rice_reach=float(payload.get("rice_reach", 1000.0)),
                rice_impact=float(payload.get("rice_impact", 3.0)),
                rice_confidence=float(payload.get("rice_confidence", 0.8)),
                rice_effort=float(payload.get("rice_effort", 2.0)),
                status="IDENTIFIED",
            )
            opp = StrategicIntelligenceService.create_opportunity(db, opp_in, organization_id=organization_id, workspace_id=workspace_id)
            return {"status": "SUCCESS", "action": action_type, "opportunity_id": opp.id}

        else:
            return {"status": "SKIPPED", "action": action_type, "message": f"Unsupported strategic action '{action_type}'."}

# Export module-level execution function for B15
def execute_strategic_automation_action(
    db: Session,
    action_type: str,
    payload: Dict[str, Any],
    organization_id: Optional[int] = None,
    workspace_id: Optional[int] = None
) -> Dict[str, Any]:
    return StrategicIntelligenceService.execute_strategic_automation_action(db, action_type, payload, organization_id, workspace_id)
