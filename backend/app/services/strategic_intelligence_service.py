import json
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
    StrategicDecisionCreate,
    StrategicDecisionResponse,
    StrategicDashboardOverviewResponse,
    AIStrategyRecommendation,
)

class StrategicIntelligenceService:
    @staticmethod
    def ensure_baseline_data(db: Session):
        """Seed baseline strategic plan, goals, SWOT, competitors, and market sizing if database is empty."""
        if db.query(StrategicPlan).count() == 0:
            plan = StrategicPlan(
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
                deadline=datetime.now(timezone.utc) + timedelta(days=240),
            )
            g2 = StrategicGoal(
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
                deadline=datetime.now(timezone.utc) + timedelta(days=180),
            )
            db.add_all([g1, g2])
            db.commit()

            # Initiatives
            init1 = StrategicInitiative(
                goal_id=g1.id,
                title="Self-Serve Enterprise SSO & Domain Verification",
                description="Frictionless SAML/OIDC and domain capture for automated multi-seat conversion.",
                priority="P1_CRITICAL",
                budget_amount=8500.0,
                status="IN_PROGRESS",
                progress_percentage=65.0,
            )
            init2 = StrategicInitiative(
                goal_id=g2.id,
                title="Autonomous Task Scheduling & Calendar Rebalancing Copilot",
                description="Deliver sticky daily proactive re-planning that drives weekly active retention.",
                priority="P2_HIGH",
                budget_amount=6000.0,
                status="IN_PROGRESS",
                progress_percentage=80.0,
            )
            db.add_all([init1, init2])
            db.commit()

        if db.query(Competitor).count() == 0:
            comps = [
                Competitor(
                    name="Linear",
                    website="https://linear.app",
                    market_position="LEADER",
                    pricing_model="PER_SEAT",
                    strengths_json=json.dumps(["Keyboard speed", "Design minimalism", "Dev tool integration"]),
                    weaknesses_json=json.dumps(["Lack of native business intelligence", "No AI agent autonomy"]),
                    features_diff_json=json.dumps({"has_ai_agents": False, "has_grc": False, "has_finops": False}),
                    threat_level="HIGH",
                    notes="Benchmark for UX responsiveness and keyboard accessibility.",
                ),
                Competitor(
                    name="Monday.com",
                    website="https://monday.com",
                    market_position="LEADER",
                    pricing_model="PER_SEAT",
                    strengths_json=json.dumps(["Broad ecosystem", "Visual customization", "Sales CRM suite"]),
                    weaknesses_json=json.dumps(["High complexity", "Slow load times", "Expensive enterprise tier"]),
                    features_diff_json=json.dumps({"has_ai_agents": False, "has_grc": True, "has_finops": False}),
                    threat_level="MEDIUM",
                    notes="Dominant in traditional non-technical enterprise workflows.",
                ),
            ]
            for c in comps:
                db.add(c)
            db.commit()

        if db.query(SWOTEntry).count() == 0:
            swot_items = [
                SWOTEntry(
                    swot_type="STRENGTH",
                    title="Unified Multi-Disciplinary Architecture",
                    description="Tight coupling of Task Management, AI Agents, Enterprise GRC, and FinOps into one zero-latency portal.",
                    impact="HIGH",
                    evidence_text="Single FastAPI + PostgreSQL database schema without external microservice fragmentation.",
                ),
                SWOTEntry(
                    swot_type="WEAKNESS",
                    title="Early Brand Awareness vs Legacy Incumbents",
                    description="Competing against established brand marketing in mid-market procurement cycles.",
                    impact="MEDIUM",
                    evidence_text="Customer interview feedback noting reliance on organic word of mouth.",
                ),
                SWOTEntry(
                    swot_type="OPPORTUNITY",
                    title="AI-Native Autonomous Productivity Shift",
                    description="Organizations seeking verifiable, policy-governed agent execution rather than conversational chat widgets.",
                    impact="HIGH",
                    evidence_text="Enterprise demand for human-in-the-loop task approval gates.",
                ),
                SWOTEntry(
                    swot_type="THREAT",
                    title="Aggressive Incumbent AI Feature Rollouts",
                    description="Established platforms bundling LLM wrappers into standard tiers.",
                    impact="MEDIUM",
                    evidence_text="Market signals tracking copilot feature launches across competitors.",
                ),
            ]
            for s in swot_items:
                db.add(s)
            db.commit()

        if db.query(MarketSizing).count() == 0:
            msize = MarketSizing(
                market_name="Collaborative SaaS Work Management & Strategic Productivity",
                methodology="BOTTOM_UP",
                tam_cents=3500000000000,  # $35B TAM
                sam_cents=420000000000,   # $4.2B SAM
                som_cents=6500000000,     # $65M SOM (3-year target capture)
                assumptions_json=json.dumps({
                    "target_companies": 140000,
                    "avg_seats_per_org": 25,
                    "arpu_per_seat_annual": 240,
                    "estimated_market_penetration": "1.5%"
                }),
                confidence_score=0.88,
            )
            db.add(msize)
            db.commit()

        if db.query(StrategicOpportunity).count() == 0:
            opps = [
                StrategicOpportunity(
                    title="Enterprise FinOps & AI Token Cost Attribution Pack",
                    description="Real-time attribution of LLM and cloud costs to specific departments and project portfolios.",
                    customer_segment="Enterprise CTOs & CFOs",
                    estimated_value_cents=4500000,  # $45k ARR potential
                    feasibility_score=9.0,
                    rice_reach=1200.0,
                    rice_impact=3.0,
                    rice_confidence=0.85,
                    rice_effort=2.0,
                    rice_score=(1200.0 * 3.0 * 0.85) / 2.0,  # 1530.0
                    status="APPROVED",
                ),
                StrategicOpportunity(
                    title="SOC 2 & ISO Continuous Compliance Auditor Portal",
                    description="One-click auditor seat access with read-only cryptographic evidence inspection.",
                    customer_segment="Regulated SaaS & Fintech",
                    estimated_value_cents=3000000,  # $30k ARR potential
                    feasibility_score=8.5,
                    rice_reach=800.0,
                    rice_impact=3.0,
                    rice_confidence=0.80,
                    rice_effort=1.5,
                    rice_score=(800.0 * 3.0 * 0.80) / 1.5,  # 1280.0
                    status="EVALUATING",
                ),
            ]
            for opp in opps:
                db.add(opp)
            db.commit()

        if db.query(MarketSignal).count() == 0:
            signals = [
                MarketSignal(
                    signal_type="PRICING_SHIFT",
                    title="Incumbent Enterprise Seat Price Increases",
                    observations="Top legacy work management competitors increased per-user monthly tiers by 18-24%, opening mid-market window.",
                    trend_direction="ACCELERATING",
                    urgency="IMMEDIATE",
                    is_converted_to_opportunity=True,
                ),
                MarketSignal(
                    signal_type="CUSTOMER_DEMAND",
                    title="Surge in Zero-Retention AI Data Governance Demands",
                    observations="Security questionnaires systematically requiring proof that task prompts are not used for public model training.",
                    trend_direction="ACCELERATING",
                    urgency="NEAR_TERM",
                    is_converted_to_opportunity=False,
                ),
            ]
            for sig in signals:
                db.add(sig)
            db.commit()

        if db.query(StrategicDecision).count() == 0:
            dec = StrategicDecision(
                title="Adopt PostgreSQL Aurora Multi-AZ as Core Ledger",
                context="Evaluated distributed NoSQL vs Relational. Decided on PostgreSQL with Alembic versioning.",
                decision_outcome="Zero cross-tenant data leakage and ACID compliance for financial and GRC audits.",
                rationale="Enterprise compliance and financial reconciliation require strict transactional integrity.",
                decision_date=datetime.now(timezone.utc) - timedelta(days=30),
                status="IN_EFFECT",
            )
            db.add(dec)
            db.commit()

    @staticmethod
    def get_dashboard_overview(db: Session) -> StrategicDashboardOverviewResponse:
        StrategicIntelligenceService.ensure_baseline_data(db)

        plans_count = db.query(StrategicPlan).filter(StrategicPlan.status == "ACTIVE").count()
        goals = db.query(StrategicGoal).all()
        total_goals = len(goals)
        completed_goals = sum(1 for g in goals if g.status == "COMPLETED")
        completion_rate = round((completed_goals / total_goals * 100.0), 1) if total_goals > 0 else 0.0

        initiatives_count = db.query(StrategicInitiative).filter(
            StrategicInitiative.status.in_(["IN_PROGRESS", "APPROVED"])
        ).count()

        signals = db.query(MarketSignal).order_by(MarketSignal.created_at.desc()).all()
        competitors_count = db.query(Competitor).count()

        opportunities = db.query(StrategicOpportunity).order_by(StrategicOpportunity.rice_score.desc()).all()
        open_opps = [o for o in opportunities if o.status in ["IDENTIFIED", "EVALUATING", "APPROVED", "IN_PROGRESS"]]
        pipeline_dollars = sum(o.estimated_value_cents for o in open_opps) / 100.0

        # SWOT summary
        swot_entries = db.query(SWOTEntry).all()
        swot_summary = {
            "STRENGTH": sum(1 for s in swot_entries if s.swot_type == "STRENGTH"),
            "WEAKNESS": sum(1 for s in swot_entries if s.swot_type == "WEAKNESS"),
            "OPPORTUNITY": sum(1 for s in swot_entries if s.swot_type == "OPPORTUNITY"),
            "THREAT": sum(1 for s in swot_entries if s.swot_type == "THREAT"),
        }

        decisions = db.query(StrategicDecision).order_by(StrategicDecision.decision_date.desc()).all()

        # Deterministic Grounded AI Strategy Recommendations
        ai_recs = [
            AIStrategyRecommendation(
                theme="Competitive Differentiation",
                recommendation="Accelerate FinOps Cost Attribution Pack into Q1 release.",
                confidence=0.92,
                rationale="RICE score of 1530.0 with $45k pipeline potential addresses incumbent weakness where neither Linear nor Monday.com provide direct AI token cost allocation.",
                grounded_evidence="Competitor diff matrix and open StrategicOpportunity record #sopp_...",
            ),
            AIStrategyRecommendation(
                theme="Market Expansion",
                recommendation="Capitalize on legacy seat price inflation by offering 30-day competitive migration credits.",
                confidence=0.88,
                rationale="MarketSignal indicates 18-24% price increases across incumbent tiers, providing prime transition timing.",
                grounded_evidence="MarketSignal: Incumbent Enterprise Seat Price Increases (Urgency: IMMEDIATE).",
            ),
        ]

        # Format responses
        recent_sig_resps = [MarketSignalResponse.model_validate(s) for s in signals[:5]]
        top_opp_resps = []
        for o in opportunities[:5]:
            resp = StrategicOpportunityResponse.model_validate(o)
            resp.estimated_value = round(o.estimated_value_cents / 100.0, 2)
            top_opp_resps.append(resp)
        recent_dec_resps = [StrategicDecisionResponse.model_validate(d) for d in decisions[:5]]

        return StrategicDashboardOverviewResponse(
            active_plans_count=plans_count,
            total_goals_count=total_goals,
            completed_goals_count=completed_goals,
            goal_completion_rate=completion_rate,
            active_initiatives_count=initiatives_count,
            active_signals_count=len(signals),
            tracked_competitors_count=competitors_count,
            open_opportunities_count=len(open_opps),
            total_pipeline_value_dollars=round(pipeline_dollars, 2),
            swot_summary=swot_summary,
            recent_signals=recent_sig_resps,
            top_opportunities=top_opp_resps,
            recent_decisions=recent_dec_resps,
            ai_recommendations=ai_recs,
        )

    # --- Plans ---
    @staticmethod
    def list_plans(db: Session) -> List[StrategicPlanResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db)
        plans = db.query(StrategicPlan).all()
        result = []
        for p in plans:
            g_count = db.query(StrategicGoal).filter(StrategicGoal.plan_id == p.id).count()
            resp = StrategicPlanResponse.model_validate(p)
            resp.goals_count = g_count
            result.append(resp)
        return result

    @staticmethod
    def create_plan(db: Session, plan_in: StrategicPlanCreate, owner_id: Optional[int] = None) -> StrategicPlan:
        plan = StrategicPlan(
            title=plan_in.title,
            vision=plan_in.vision,
            mission=plan_in.mission,
            strategic_themes_json=plan_in.strategic_themes_json,
            time_horizon=plan_in.time_horizon,
            status=plan_in.status,
            organization_id=plan_in.organization_id,
            owner_id=owner_id,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    # --- Goals ---
    @staticmethod
    def list_goals(db: Session, plan_id: Optional[str] = None) -> List[StrategicGoalResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db)
        query = db.query(StrategicGoal)
        if plan_id:
            query = query.filter(StrategicGoal.plan_id == plan_id)
        goals = query.all()
        result = []
        for g in goals:
            diff = g.target_value - g.baseline_value
            curr = g.current_value - g.baseline_value
            pct = round((curr / diff * 100.0), 1) if diff != 0 else 0.0
            resp = StrategicGoalResponse.model_validate(g)
            resp.progress_percentage = max(0.0, min(100.0, pct))
            result.append(resp)
        return result

    @staticmethod
    def create_goal(db: Session, goal_in: StrategicGoalCreate, owner_id: Optional[int] = None) -> StrategicGoalResponse:
        goal = StrategicGoal(
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

    # --- Initiatives ---
    @staticmethod
    def list_initiatives(db: Session, goal_id: Optional[str] = None) -> List[StrategicInitiativeResponse]:
        query = db.query(StrategicInitiative)
        if goal_id:
            query = query.filter(StrategicInitiative.goal_id == goal_id)
        return [StrategicInitiativeResponse.model_validate(i) for i in query.all()]

    @staticmethod
    def create_initiative(db: Session, init_in: StrategicInitiativeCreate, owner_id: Optional[int] = None) -> StrategicInitiative:
        init = StrategicInitiative(
            goal_id=init_in.goal_id,
            title=init_in.title,
            description=init_in.description,
            priority=init_in.priority,
            budget_amount=init_in.budget_amount,
            status=init_in.status,
            progress_percentage=init_in.progress_percentage,
            start_date=init_in.start_date,
            end_date=init_in.end_date,
            owner_id=owner_id,
        )
        db.add(init)
        db.commit()
        db.refresh(init)
        return init

    # --- Market Intelligence & Signals ---
    @staticmethod
    def list_market_intelligence(db: Session) -> List[MarketIntelligence]:
        return db.query(MarketIntelligence).order_by(MarketIntelligence.created_at.desc()).all()

    @staticmethod
    def create_market_intelligence(db: Session, intel_in: MarketIntelligenceCreate, owner_id: Optional[int] = None) -> MarketIntelligence:
        intel = MarketIntelligence(
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
        return intel

    @staticmethod
    def list_market_signals(db: Session) -> List[MarketSignal]:
        return db.query(MarketSignal).order_by(MarketSignal.created_at.desc()).all()

    @staticmethod
    def create_market_signal(db: Session, sig_in: MarketSignalCreate) -> MarketSignal:
        sig = MarketSignal(
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
        return sig

    # --- Competitors ---
    @staticmethod
    def list_competitors(db: Session) -> List[Competitor]:
        StrategicIntelligenceService.ensure_baseline_data(db)
        return db.query(Competitor).order_by(Competitor.name.asc()).all()

    @staticmethod
    def create_competitor(db: Session, comp_in: CompetitorCreate) -> Competitor:
        comp = Competitor(
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
        return comp

    # --- SWOT ---
    @staticmethod
    def list_swot(db: Session) -> List[SWOTEntry]:
        StrategicIntelligenceService.ensure_baseline_data(db)
        return db.query(SWOTEntry).order_by(SWOTEntry.created_at.asc()).all()

    @staticmethod
    def create_swot(db: Session, swot_in: SWOTEntryCreate) -> SWOTEntry:
        entry = SWOTEntry(
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
        return entry

    # --- Market Sizing ---
    @staticmethod
    def list_market_sizings(db: Session) -> List[MarketSizingResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db)
        sizings = db.query(MarketSizing).all()
        result = []
        for s in sizings:
            resp = MarketSizingResponse.model_validate(s)
            resp.tam_dollars = round(s.tam_cents / 100.0, 2)
            resp.sam_dollars = round(s.sam_cents / 100.0, 2)
            resp.som_dollars = round(s.som_cents / 100.0, 2)
            result.append(resp)
        return result

    @staticmethod
    def create_market_sizing(db: Session, m_in: MarketSizingCreate) -> MarketSizing:
        ms = MarketSizing(
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
        return ms

    # --- Opportunities & RICE Prioritization ---
    @staticmethod
    def list_opportunities(db: Session) -> List[StrategicOpportunityResponse]:
        StrategicIntelligenceService.ensure_baseline_data(db)
        opps = db.query(StrategicOpportunity).order_by(StrategicOpportunity.rice_score.desc()).all()
        result = []
        for o in opps:
            resp = StrategicOpportunityResponse.model_validate(o)
            resp.estimated_value = round(o.estimated_value_cents / 100.0, 2)
            result.append(resp)
        return result

    @staticmethod
    def create_opportunity(db: Session, opp_in: StrategicOpportunityCreate) -> StrategicOpportunity:
        effort = opp_in.rice_effort if opp_in.rice_effort > 0 else 1.0
        score = (opp_in.rice_reach * opp_in.rice_impact * opp_in.rice_confidence) / effort
        opp = StrategicOpportunity(
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
        return opp

    # --- Decisions ---
    @staticmethod
    def list_decisions(db: Session) -> List[StrategicDecision]:
        StrategicIntelligenceService.ensure_baseline_data(db)
        return db.query(StrategicDecision).order_by(StrategicDecision.decision_date.desc()).all()

    @staticmethod
    def create_decision(db: Session, dec_in: StrategicDecisionCreate, user_id: Optional[int] = None) -> StrategicDecision:
        dec = StrategicDecision(
            title=dec_in.title,
            context=dec_in.context,
            decision_outcome=dec_in.decision_outcome,
            rationale=dec_in.rationale,
            decision_date=dec_in.decision_date or datetime.now(timezone.utc),
            status=dec_in.status,
            decision_maker_id=user_id,
        )
        db.add(dec)
        db.commit()
        db.refresh(dec)
        return dec
