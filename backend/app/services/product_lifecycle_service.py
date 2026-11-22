import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.product_lifecycle import (
    ProductDiscovery,
    ProductIdea,
    ProductFeatureRequest,
    ProductOpportunity,
    ProductPrioritizationItem,
    ProductInitiative,
    LifecycleRoadmapItem,
    RoadmapDependency,
    ProductValidation,
    ProductExperiment,
    ExperimentVariant,
    ExperimentAssignment,
    ExperimentEvent,
    ProductRelease,
    ProductRetrospective,
    ProductEventRecord,
    ProductDecision,
    ProductRiskRecord,
)
from app.models.user import User

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ProductLifecycleService:
    @staticmethod
    def seed_initial_product_lifecycle_data(db: Session, organization_id: Optional[int] = None) -> None:
        """Explicitly seeds initial product lifecycle demo data scoped to tenant organization."""
        admin_user = db.query(User).filter(User.role == "admin").first()
        admin_id = admin_user.id if admin_user else None

        # 1. Product Discoveries & Ideas
        existing_disc = db.query(ProductDiscovery)
        if organization_id is not None:
            existing_disc = existing_disc.filter(ProductDiscovery.organization_id == organization_id)
        if existing_disc.count() == 0:
            disc1 = ProductDiscovery(
                title="Cross-Team Collaborative Real-Time Whiteboard",
                problem_statement="Distributed product teams need a unified canvas directly inside FocusBoard to brainstorm and link tasks visually.",
                hypothesis="Embedding an interactive diagram canvas into workspace views will increase daily active collaboration by 35%.",
                target_users="Product Managers, UX Designers, Engineering Leads",
                customer_segment="ENTERPRISE",
                business_impact="Drives enterprise seat upgrades and multi-department expansion.",
                customer_impact="Reduces context-switching between external whiteboard tools and FocusBoard tasks.",
                status="VALIDATED",
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add(disc1)
            db.flush()

            idea1 = ProductIdea(
                discovery_id=disc1.id,
                title="Interactive Canvas & Visual Task Flow Editor",
                description="Drag-and-drop workflow diagramming with direct two-way task card synchronization.",
                problem_statement="Visualizing multi-step project phases is currently limited to list and kanban views.",
                proposed_solution="Lightweight SVG/Canvas workspace view supporting node connectors and task status badges.",
                product_area="CORE_PLATFORM",
                category="COLLABORATION",
                priority="HIGH",
                status="PLANNED",
                owner_id=admin_id,
                organization_id=organization_id,
                tags_json=json.dumps(["whiteboard", "visual-workflow", "canvas"]),
            )
            db.add(idea1)
            db.commit()

        # 2. Feature Requests (Customer Demand Hub)
        existing_freq = db.query(ProductFeatureRequest)
        if organization_id is not None:
            existing_freq = existing_freq.filter(ProductFeatureRequest.organization_id == organization_id)
        if existing_freq.count() == 0:
            frequests = [
                ProductFeatureRequest(
                    title="Two-Way Jira and Linear Bidirectional Issue Sync",
                    description="Allow engineering teams to mirror tickets between FocusBoard boards and Jira/Linear projects automatically.",
                    customer_name="Acme Enterprise Corp",
                    customer_segment="ENTERPRISE",
                    source="CUSTOMER_FEEDBACK",
                    request_count=18,
                    priority="HIGH",
                    status="PRIORITIZED",
                    business_impact="Critical for closing 5 prospective Fortune 500 SaaS deals.",
                    revenue_impact=120000.0,
                    owner_id=admin_id,
                    organization_id=organization_id,
                ),
                ProductFeatureRequest(
                    title="SOC 2 Type II Self-Serve Compliance Report Generator",
                    description="Automated one-click PDF export containing compliance controls, evidence links, and auditor attestation.",
                    customer_name="Fintech Global",
                    customer_segment="ENTERPRISE",
                    source="SALES",
                    request_count=12,
                    priority="CRITICAL",
                    status="VALIDATED",
                    business_impact="Required for security compliance vendor assessments.",
                    revenue_impact=85000.0,
                    owner_id=admin_id,
                    organization_id=organization_id,
                ),
                ProductFeatureRequest(
                    title="Dark Mode System Theme Syncing for Mobile PWA",
                    description="Automatically match device OS light/dark schedule on iOS and Android standalone PWAs.",
                    customer_name="DesignCraft Studio",
                    customer_segment="MID_MARKET",
                    source="SURVEY",
                    request_count=8,
                    priority="LOW",
                    status="IN_PROGRESS",
                    business_impact="Improves mobile engagement and NPS.",
                    revenue_impact=15000.0,
                    owner_id=admin_id,
                    organization_id=organization_id,
                ),
            ]
            db.add_all(frequests)
            db.commit()

        # 3. Product Opportunities
        existing_opp = db.query(ProductOpportunity)
        if organization_id is not None:
            existing_opp = existing_opp.filter(ProductOpportunity.organization_id == organization_id)
        if existing_opp.count() == 0:
            opp = ProductOpportunity(
                title="AI-Powered Sprint Retrospective & Velocity Forecasting",
                description="Predict sprint completion confidence and highlight productivity bottlenecks before deadlines slip.",
                problem_statement="Sprint planning relies on subjective velocity estimates rather than historical delivery data.",
                customer_segment="ENTERPRISE",
                market_segment="B2B_SAAS",
                product_area="AI_ANALYTICS",
                business_impact="Differentiates FocusBoard from legacy project management platforms.",
                customer_impact="Enables teams to hit committed sprint goals with higher reliability.",
                revenue_potential=250000.0,
                effort_estimate="MEDIUM",
                risk_level="LOW",
                validation_status="VALIDATED",
                priority="HIGH",
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add(opp)
            db.commit()

        # 4. Product Initiatives & Lifecycle Roadmaps
        existing_init = db.query(ProductInitiative)
        if organization_id is not None:
            existing_init = existing_init.filter(ProductInitiative.organization_id == organization_id)
        if existing_init.count() == 0:
            init1 = ProductInitiative(
                title="Enterprise Zero-Trust & Developer Integration Ecosystem",
                description="Deliver comprehensive SOC 2, bi-directional webhooks, and marketplace plugins.",
                strategic_objective="Expand ARR by 40% in enterprise security and developer tiers.",
                priority="STRATEGIC",
                status="IN_PROGRESS",
                progress_pct=75.0,
                owner_id=admin_id,
                organization_id=organization_id,
                start_date=utc_now() - timedelta(days=60),
                target_date=utc_now() + timedelta(days=30),
            )
            db.add(init1)
            db.flush()

            roadmap_items = [
                LifecycleRoadmapItem(
                    initiative_id=init1.id,
                    title="Real-Time SOC 2 Compliance Audit Evidence Hub",
                    description="Self-serve auditor workspace with cryptographic log integrity.",
                    product_area="SECURITY",
                    status="IN_PROGRESS",
                    priority="HIGH",
                    quarter="Q1-2027",
                    start_date=utc_now() - timedelta(days=20),
                    target_date=utc_now() + timedelta(days=15),
                    progress_pct=80.0,
                    owner_id=admin_id,
                    organization_id=organization_id,
                ),
                LifecycleRoadmapItem(
                    initiative_id=init1.id,
                    title="Integration Marketplace & Public REST/Webhook Platform",
                    description="Third-party app ecosystem with OAuth 2.0 app grants.",
                    product_area="INTEGRATIONS",
                    status="COMPLETED",
                    priority="HIGH",
                    quarter="Q1-2027",
                    start_date=utc_now() - timedelta(days=45),
                    target_date=utc_now() - timedelta(days=5),
                    progress_pct=100.0,
                    owner_id=admin_id,
                    organization_id=organization_id,
                ),
                LifecycleRoadmapItem(
                    initiative_id=init1.id,
                    title="A/B Experimentation Engine & Product Analytics",
                    description="In-app deterministic variant allocation and conversion tracking.",
                    product_area="PRODUCT_GROWTH",
                    status="IN_PROGRESS",
                    priority="MEDIUM",
                    quarter="Q2-2027",
                    start_date=utc_now(),
                    target_date=utc_now() + timedelta(days=45),
                    progress_pct=50.0,
                    owner_id=admin_id,
                    organization_id=organization_id,
                ),
            ]
            db.add_all(roadmap_items)
            db.commit()

        # 5. Experiments & A/B Testing
        existing_exp = db.query(ProductExperiment)
        if organization_id is not None:
            existing_exp = existing_exp.filter(ProductExperiment.organization_id == organization_id)
        if existing_exp.count() == 0:
            exp = ProductExperiment(
                name="Onboarding Wizard vs. Interactive Checklist",
                description="Testing whether a step-by-step modal wizard or an embedded sidebar checklist achieves higher day-7 activation.",
                hypothesis="Interactive checklist provides faster time-to-value, yielding a 20% higher task creation conversion.",
                experiment_type="AB_TEST",
                primary_metric="first_task_created_rate",
                status="RUNNING",
                audience_segment="NEW_SIGNUPS",
                total_sample_size=320,
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add(exp)
            db.flush()

            variants = [
                ExperimentVariant(
                    experiment_id=exp.id,
                    variant_name="Control (Modal Wizard)",
                    variant_key="control_a",
                    allocation_pct=50.0,
                    config_json=json.dumps({"flow_type": "MODAL_WIZARD", "step_count": 4}),
                    impression_count=160,
                    conversion_count=48,
                    conversion_rate=30.0,
                ),
                ExperimentVariant(
                    experiment_id=exp.id,
                    variant_name="Treatment (Interactive Checklist)",
                    variant_key="treatment_b",
                    allocation_pct=50.0,
                    config_json=json.dumps({"flow_type": "SIDEBAR_CHECKLIST", "step_count": 5}),
                    impression_count=160,
                    conversion_count=67,
                    conversion_rate=41.9,
                ),
            ]
            db.add_all(variants)
            db.commit()

        # 6. Product Releases
        existing_rel = db.query(ProductRelease)
        if organization_id is not None:
            existing_rel = existing_rel.filter(ProductRelease.organization_id == organization_id)
        if existing_rel.count() == 0:
            prel = ProductRelease(
                release_version="v2.5.0",
                title="FocusBoard Enterprise Intelligence & Security Release",
                description="Includes Security Intelligence SOC, Zero-Trust Access Reviews, and Product Lifecycle Engine.",
                status="READY",
                release_date=utc_now() + timedelta(days=5),
                rollout_percentage=100.0,
                release_notes="Major enterprise release featuring full SOC dashboard, threat detection, RICE prioritization, and A/B testing engine.",
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add(prel)
            db.commit()

    @staticmethod
    def calculate_prioritization(reach: float, impact: float, confidence: float, effort: float, ease: float = 3.0) -> Dict[str, float]:
        """Calculates RICE, ICE, and weighted prioritization scores with robust boundary and input validation."""
        if effort <= 0:
            raise ValueError("Effort estimate must be strictly greater than zero.")
        if reach < 1.0:
            raise ValueError("Reach must be at least 1.0.")
        if impact <= 0 or impact > 10.0:
            raise ValueError("Impact must be between 0.1 and 10.0.")
        if confidence <= 0 or confidence > 1.0:
            raise ValueError("Confidence must be between 0.01 and 1.0.")
        if ease <= 0 or ease > 10.0:
            raise ValueError("Ease must be between 0.1 and 10.0.")

        rice_score = round((reach * impact * confidence) / effort, 2)
        ice_score = round(impact * confidence * ease, 2)
        # Weighted normalized score out of 100
        weighted_score = round(min(max((rice_score / 5.0) + (ice_score * 2.0), 10.0), 100.0), 1)
        return {
            "rice_score": rice_score,
            "ice_score": ice_score,
            "weighted_score": weighted_score,
        }

    @staticmethod
    def assign_experiment_variant(db: Session, experiment_id: str, user_id: int, organization_id: Optional[int] = None) -> ExperimentVariant:
        """Deterministically assigns user to experiment variant using SHA-256 hash with tenant and lifecycle checks."""
        exp_query = db.query(ProductExperiment).filter(ProductExperiment.id == experiment_id)
        if organization_id is not None:
            exp_query = exp_query.filter(ProductExperiment.organization_id == organization_id)
        exp = exp_query.first()
        if not exp:
            raise ValueError(f"Experiment '{experiment_id}' not found in authorized organization context.")

        if exp.status != "RUNNING":
            raise ValueError(f"Cannot assign user to experiment with status '{exp.status}'. Experiment must be in 'RUNNING' status.")

        # Check existing assignment
        existing = db.query(ExperimentAssignment).filter(
            ExperimentAssignment.experiment_id == experiment_id,
            ExperimentAssignment.user_id == user_id,
        ).first()

        if existing:
            variant = db.query(ExperimentVariant).filter(ExperimentVariant.id == existing.variant_id).first()
            if variant:
                return variant

        variants = db.query(ExperimentVariant).filter(ExperimentVariant.experiment_id == experiment_id).order_by(ExperimentVariant.variant_key).all()
        if not variants:
            raise ValueError(f"No variants configured for experiment {experiment_id}")

        # Deterministic hashing: hash(exp_id:user_id) % 100
        hash_val = int(hashlib.sha256(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16) % 100
        cumulative = 0.0
        selected_variant = variants[0]

        for v in variants:
            cumulative += v.allocation_pct
            if hash_val < cumulative:
                selected_variant = v
                break

        # Save assignment
        assignment = ExperimentAssignment(
            experiment_id=experiment_id,
            variant_id=selected_variant.id,
            user_id=user_id,
        )
        db.add(assignment)

        # Increment impression
        selected_variant.impression_count += 1
        if selected_variant.impression_count > 0:
            selected_variant.conversion_rate = round((selected_variant.conversion_count / selected_variant.impression_count) * 100, 2)

        exp.total_sample_size += 1
        db.commit()
        db.refresh(selected_variant)
        return selected_variant

    @staticmethod
    def track_experiment_event(db: Session, experiment_id: str, user_id: int, event_name: str, metric_value: float = 1.0, organization_id: Optional[int] = None) -> bool:
        """Records telemetry event for user's assigned variant and updates conversion stats."""
        exp_query = db.query(ProductExperiment).filter(ProductExperiment.id == experiment_id)
        if organization_id is not None:
            exp_query = exp_query.filter(ProductExperiment.organization_id == organization_id)
        exp = exp_query.first()
        if not exp:
            raise ValueError(f"Experiment '{experiment_id}' not found in authorized organization context.")

        assignment = db.query(ExperimentAssignment).filter(
            ExperimentAssignment.experiment_id == experiment_id,
            ExperimentAssignment.user_id == user_id,
        ).first()

        if not assignment:
            raise ValueError(f"User {user_id} has not been assigned to experiment {experiment_id}.")

        evt = ExperimentEvent(
            experiment_id=experiment_id,
            variant_id=assignment.variant_id,
            user_id=user_id,
            event_name=event_name,
            metric_value=metric_value,
        )
        db.add(evt)

        # Update variant conversion stats
        variant = db.query(ExperimentVariant).filter(ExperimentVariant.id == assignment.variant_id).first()
        if variant:
            variant.conversion_count += 1
            if variant.impression_count > 0:
                variant.conversion_rate = round((variant.conversion_count / variant.impression_count) * 100, 2)

        db.commit()
        return True

    @staticmethod
    def get_lifecycle_overview(db: Session, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Aggregates real-time tenant-scoped product discovery, customer demand, and experiment metrics."""
        disc_q = db.query(ProductDiscovery)
        idea_q = db.query(ProductIdea)
        freq_q = db.query(ProductFeatureRequest)
        opp_q = db.query(ProductOpportunity)
        init_q = db.query(ProductInitiative)
        rmap_q = db.query(LifecycleRoadmapItem)
        exp_q = db.query(ProductExperiment)
        rel_q = db.query(ProductRelease)

        if organization_id is not None:
            disc_q = disc_q.filter(ProductDiscovery.organization_id == organization_id)
            idea_q = idea_q.filter(ProductIdea.organization_id == organization_id)
            freq_q = freq_q.filter(ProductFeatureRequest.organization_id == organization_id)
            opp_q = opp_q.filter(ProductOpportunity.organization_id == organization_id)
            init_q = init_q.filter(ProductInitiative.organization_id == organization_id)
            rmap_q = rmap_q.filter(LifecycleRoadmapItem.organization_id == organization_id)
            exp_q = exp_q.filter(ProductExperiment.organization_id == organization_id)
            rel_q = rel_q.filter(ProductRelease.organization_id == organization_id)

        discoveries_count = disc_q.count()
        ideas_count = idea_q.count()
        feature_requests_count = freq_q.count()

        total_demand_requests = freq_q.with_entities(func.sum(ProductFeatureRequest.request_count)).scalar() or 0
        total_potential_revenue = freq_q.with_entities(func.sum(ProductFeatureRequest.revenue_impact)).scalar() or 0.0

        opportunities_count = opp_q.count()
        initiatives_count = init_q.count()
        roadmap_items_count = rmap_q.count()
        experiments_count = exp_q.filter(ProductExperiment.status == "RUNNING").count()
        releases_count = rel_q.count()

        return {
            "total_discoveries": discoveries_count,
            "total_ideas": ideas_count,
            "total_feature_requests": feature_requests_count,
            "total_customer_demand_count": int(total_demand_requests),
            "total_pipeline_revenue_impact": round(float(total_potential_revenue), 2),
            "total_opportunities": opportunities_count,
            "total_initiatives": initiatives_count,
            "total_roadmap_items": roadmap_items_count,
            "active_experiments_count": experiments_count,
            "total_releases": releases_count,
        }

    @staticmethod
    def answer_ai_product_query(db: Session, query: str, context_type: str = "PRODUCT_OVERVIEW", organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Tenant-isolated Product AI Assistant delivering grounded prioritization, roadmap, and customer demand insights."""
        overview = ProductLifecycleService.get_lifecycle_overview(db, organization_id=organization_id)

        freq_q = db.query(ProductFeatureRequest)
        exp_q = db.query(ProductExperiment)
        rmap_q = db.query(LifecycleRoadmapItem)

        if organization_id is not None:
            freq_q = freq_q.filter(ProductFeatureRequest.organization_id == organization_id)
            exp_q = exp_q.filter(ProductExperiment.organization_id == organization_id)
            rmap_q = rmap_q.filter(LifecycleRoadmapItem.organization_id == organization_id)

        top_requests = freq_q.order_by(desc(ProductFeatureRequest.request_count)).limit(3).all()
        experiments = exp_q.filter(ProductExperiment.status == "RUNNING").all()
        roadmap_items = rmap_q.filter(LifecycleRoadmapItem.status == "IN_PROGRESS").all()

        q_lower = query.lower()
        if "feature" in q_lower or "request" in q_lower or "demand" in q_lower:
            if top_requests:
                req_names = ", ".join([f"'{r.title}' ({r.request_count} reqs)" for r in top_requests])
                answer = (
                    f"Customer demand analysis highlights {overview['total_feature_requests']} feature requests with "
                    f"{overview['total_customer_demand_count']} cumulative customer endorsements totaling ${overview['total_pipeline_revenue_impact']:,.2f} in pipeline value. "
                    f"Top prioritized items include: {req_names}."
                )
            else:
                answer = "No active feature requests logged for this workspace. Use the Customer Demand Hub to capture user requests."
            actions = [
                "Schedule review for feature requests exceeding 10 customer requests",
                "Link top demand requests to upcoming product roadmap initiatives",
                "Validate customer willingness to pilot upcoming beta builds",
            ]
        elif "experiment" in q_lower or "test" in q_lower or "a/b" in q_lower:
            if experiments:
                exp_names = ", ".join([f"'{e.name}'" for e in experiments[:2]])
                answer = (
                    f"There are currently {overview['active_experiments_count']} active A/B experiments running across "
                    f"user cohorts: {exp_names}. Variant conversions are being recorded in real-time."
                )
            else:
                answer = f"No A/B experiments currently running. Total configured experiments: {overview['active_experiments_count']}."
            actions = [
                "Monitor variant conversion rates until reaching statistical sample size",
                "Inspect drop-off telemetry between trial signup and first task creation",
            ]
        elif "roadmap" in q_lower or "timeline" in q_lower:
            answer = (
                f"The product roadmap contains {overview['total_roadmap_items']} items across {overview['total_initiatives']} strategic initiatives. "
                f"Currently {len(roadmap_items)} items are actively in progress for current milestones."
            )
            actions = [
                "Resolve critical dependencies between compliance milestones and integration platform",
                "Verify sprint capacity with engineering leads",
            ]
        else:
            answer = (
                f"Product Lifecycle Intelligence reports {overview['total_discoveries']} discoveries, "
                f"{overview['total_ideas']} backlog ideas, {overview['total_feature_requests']} customer requests, "
                f"and {overview['active_experiments_count']} live A/B experiments driving strategic roadmap execution."
            )
            actions = [
                "Prioritize top backlog requests using RICE framework",
                "Conduct customer discovery interviews for high-impact opportunities",
                "Publish sprint release notes to customers for planned releases",
            ]

        return {
            "query": query,
            "answer": answer,
            "total_discoveries": overview["total_discoveries"],
            "total_ideas": overview["total_ideas"],
            "total_feature_requests": overview["total_feature_requests"],
            "active_experiments": overview["active_experiments_count"],
            "recommended_roadmap_actions": actions,
            "grounded_evidence": {
                "source": "focusboard_product_lifecycle_telemetry",
                "mode": "deterministic_grounded_analysis",
                "organization_id": organization_id,
                "evaluated_at": utc_now().isoformat(),
                "metrics": overview,
                "top_demanded_features": [
                    {"title": r.title, "demand_count": r.request_count, "revenue_impact": r.revenue_impact}
                    for r in top_requests
                ],
            },
        }
