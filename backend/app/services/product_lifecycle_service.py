import hashlib
import json
import logging
import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

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
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# ==============================================================================
# LIFECYCLE STAGE TRANSITIONS & VALIDATION
# ==============================================================================

STAGE_TRANSITIONS = {
    "DISCOVERY": {
        "DISCOVERED": ["INVESTIGATING", "VALIDATING", "REJECTED", "ARCHIVED"],
        "INVESTIGATING": ["VALIDATING", "REJECTED", "ARCHIVED"],
        "VALIDATING": ["VALIDATED", "REJECTED", "ARCHIVED"],
        "VALIDATED": ["PRIORITIZED", "PLANNED", "ARCHIVED"],
        "PRIORITIZED": ["PLANNED", "ARCHIVED"],
        "PLANNED": ["ARCHIVED"],
        "REJECTED": ["DISCOVERED", "ARCHIVED"],
        "ARCHIVED": ["DISCOVERED"],
    },
    "IDEA": {
        "NEW": ["UNDER_REVIEW", "VALIDATED", "ARCHIVED"],
        "UNDER_REVIEW": ["VALIDATED", "NEW", "ARCHIVED"],
        "VALIDATED": ["PLANNED", "IN_PROGRESS", "SHIPPED", "ARCHIVED"],
        "PLANNED": ["IN_PROGRESS", "VALIDATED", "ARCHIVED"],
        "IN_PROGRESS": ["SHIPPED", "PLANNED", "ARCHIVED"],
        "SHIPPED": ["ARCHIVED"],
        "ARCHIVED": ["NEW"],
    },
    "FEATURE_REQUEST": {
        "NEW": ["UNDER_REVIEW", "VALIDATED", "DECLINED"],
        "UNDER_REVIEW": ["VALIDATED", "DECLINED", "NEW"],
        "VALIDATED": ["PRIORITIZED", "PLANNED", "DECLINED"],
        "PRIORITIZED": ["PLANNED", "VALIDATED", "DECLINED"],
        "PLANNED": ["IN_PROGRESS", "PRIORITIZED", "DECLINED"],
        "IN_PROGRESS": ["RELEASED", "PLANNED", "DECLINED"],
        "RELEASED": ["ARCHIVED"],
        "DECLINED": ["UNDER_REVIEW", "NEW"],
        "ARCHIVED": ["NEW"],
    },
    "EXPERIMENT": {
        "DRAFT": ["REVIEW", "APPROVED", "SCHEDULED", "RUNNING", "ARCHIVED"],
        "REVIEW": ["APPROVED", "DRAFT", "ARCHIVED"],
        "APPROVED": ["SCHEDULED", "RUNNING", "DRAFT"],
        "SCHEDULED": ["RUNNING", "DRAFT"],
        "RUNNING": ["PAUSED", "COMPLETED", "ARCHIVED"],
        "PAUSED": ["RUNNING", "COMPLETED", "ARCHIVED"],
        "COMPLETED": ["ANALYZED", "ARCHIVED"],
        "ANALYZED": ["ARCHIVED"],
        "ARCHIVED": ["DRAFT"],
    },
    "RELEASE": {
        "DRAFT": ["PLANNING", "PLANNED", "READY", "CANCELLED"],
        "PLANNING": ["DEVELOPMENT", "READY", "RELEASING", "CANCELLED"],
        "DEVELOPMENT": ["CODE_FREEZE", "READY", "CANCELLED"],
        "CODE_FREEZE": ["READY", "RELEASING", "CANCELLED"],
        "PLANNED": ["DEVELOPMENT", "READY", "RELEASING", "CANCELLED"],
        "READY": ["RELEASING", "PLANNED", "CANCELLED"],
        "RELEASING": ["RELEASED", "ROLLED_BACK"],
        "RELEASED": ["ROLLED_BACK", "ARCHIVED"],
        "ROLLED_BACK": ["PLANNING", "PLANNED", "ARCHIVED"],
        "CANCELLED": ["DRAFT", "PLANNING", "ARCHIVED"],
        "ARCHIVED": ["DRAFT", "PLANNING"],
    },
}

def validate_stage_transition(entity_type: str, current_stage: str, target_stage: str) -> bool:
    if not current_stage or not target_stage or current_stage.upper() == target_stage.upper():
        return True
    rules = STAGE_TRANSITIONS.get(entity_type.upper(), {})
    allowed = rules.get(current_stage.upper(), [])
    return target_stage.upper() in [a.upper() for a in allowed]

# ==============================================================================
# PRODUCT LIFECYCLE SERVICE
# ==============================================================================

class ProductLifecycleService:
    @staticmethod
    def validate_stage_transition(entity_type: str, current_stage: str, target_stage: str) -> bool:
        return validate_stage_transition(entity_type, current_stage, target_stage)

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
            freq1 = ProductFeatureRequest(
                title="Automated Jira Two-Way Sync Connector",
                description="Synchronize issue status, assignees, and comments bidirectionally with Jira Cloud and Server.",
                customer_name="Stripe Operations",
                customer_segment="ENTERPRISE",
                source="CUSTOMER_FEEDBACK",
                request_count=18,
                priority="URGENT",
                status="PRIORITIZED",
                business_impact="Unblocks $120k ARR pipeline in enterprise deals.",
                revenue_impact=120000.0,
                owner_id=admin_id,
                organization_id=organization_id,
            )
            freq2 = ProductFeatureRequest(
                title="Custom Automated Webhook Triggers",
                description="Provide out-of-the-box outbound webhook delivery with HMAC verification on task completion events.",
                customer_name="Datadog SRE",
                customer_segment="MID_MARKET",
                source="CUSTOMER_FEEDBACK",
                request_count=12,
                priority="HIGH",
                status="PLANNED",
                business_impact="High demand across engineering customers for observability pipeline integration.",
                revenue_impact=45000.0,
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add_all([freq1, freq2])
            db.commit()

        # 3. Product Opportunities
        existing_opp = db.query(ProductOpportunity)
        if organization_id is not None:
            existing_opp = existing_opp.filter(ProductOpportunity.organization_id == organization_id)
        if existing_opp.count() == 0:
            opp1 = ProductOpportunity(
                title="AI-Powered Predictive Sprint Capacity Planner",
                description="Analyze historical velocity and pull request throughput to automatically balance task distributions.",
                problem_statement="Engineering managers spend 4+ hours per sprint estimating story point allocations manually.",
                customer_segment="ENTERPRISE",
                market_segment="B2B_SAAS",
                product_area="INTELLIGENCE",
                business_impact="Competitive differentiator against legacy project management tools.",
                customer_impact="Prevents engineer burnout and eliminates 80% of sprint estimation overhead.",
                revenue_potential=85000.0,
                effort_estimate="MEDIUM",
                risk_level="LOW",
                validation_status="VALIDATED",
                priority="HIGH",
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add(opp1)
            db.commit()

        # 4. Prioritization Items
        existing_prio = db.query(ProductPrioritizationItem)
        if organization_id is not None:
            existing_prio = existing_prio.filter(ProductPrioritizationItem.organization_id == organization_id)
        if existing_prio.count() == 0:
            prio1 = ProductPrioritizationItem(
                item_type="FEATURE_REQUEST",
                item_id="jira_sync",
                title="Automated Jira Two-Way Sync Connector",
                reach=350.0,
                impact=4.5,
                confidence=0.9,
                effort=2.5,
                rice_score=567.0,
                ease=3.5,
                ice_score=14.18,
                moscow_category="MUST_HAVE",
                weighted_score=92.5,
                priority_rank=1,
                notes="Top enterprise revenue driver with signed customer intent.",
                evaluated_by_id=admin_id,
                organization_id=organization_id,
            )
            db.add(prio1)
            db.commit()

        # 5. Product Initiatives & Roadmap
        existing_init = db.query(ProductInitiative)
        if organization_id is not None:
            existing_init = existing_init.filter(ProductInitiative.organization_id == organization_id)
        if existing_init.count() == 0:
            init1 = ProductInitiative(
                title="Enterprise Connectivity & Ecosystem Expansion",
                description="Establish FocusBoard as the single source of truth connected to enterprise toolchains.",
                strategic_objective="Win 50+ enterprise tier accounts in FY2027.",
                priority="HIGH",
                status="IN_PROGRESS",
                progress_pct=45.0,
                owner_id=admin_id,
                organization_id=organization_id,
                start_date=utc_now() - timedelta(days=30),
                target_date=utc_now() + timedelta(days=90),
            )
            db.add(init1)
            db.flush()

            rmi1 = LifecycleRoadmapItem(
                initiative_id=init1.id,
                title="Release Jira Cloud Bi-Directional Webhooks",
                description="Certified marketplace app with real-time webhooks and task synchronization.",
                product_area="INTEGRATIONS",
                status="IN_PROGRESS",
                priority="URGENT",
                quarter="Q1-2027",
                progress_pct=60.0,
                owner_id=admin_id,
                organization_id=organization_id,
                start_date=utc_now() - timedelta(days=20),
                target_date=utc_now() + timedelta(days=25),
            )
            db.add(rmi1)
            db.commit()

        # 6. Product Experiments (A/B Testing)
        existing_exp = db.query(ProductExperiment)
        if organization_id is not None:
            existing_exp = existing_exp.filter(ProductExperiment.organization_id == organization_id)
        if existing_exp.count() == 0:
            exp1 = ProductExperiment(
                name="Frictionless Single-Click Task Creation Flow",
                description="Tests inline quick-add input bar vs traditional multi-field task modal on activation rate.",
                hypothesis="Reducing required fields on task creation will lift 7-day user activation rate by 18%.",
                experiment_type="AB_TEST",
                primary_metric="activation_rate",
                status="RUNNING",
                audience_segment="NEW_SIGNUPS",
                total_sample_size=120,
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add(exp1)
            db.flush()

            v_a = ExperimentVariant(
                experiment_id=exp1.id,
                variant_name="Control (Standard Modal)",
                variant_key="control_a",
                allocation_pct=50.0,
                impression_count=60,
                conversion_count=18,
                conversion_rate=30.0,
            )
            v_b = ExperimentVariant(
                experiment_id=exp1.id,
                variant_name="Treatment (Quick Inline Bar)",
                variant_key="treatment_b",
                allocation_pct=50.0,
                impression_count=60,
                conversion_count=29,
                conversion_rate=48.33,
            )
            db.add_all([v_a, v_b])
            db.commit()

        # 7. Releases
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
                readiness_score=95.0,
                readiness_status="READY_FOR_RELEASE",
                owner_id=admin_id,
                organization_id=organization_id,
            )
            db.add(prel)
            db.commit()

    @staticmethod
    def calculate_prioritization(reach: float, impact: float, confidence: float, effort: float, ease: float = 3.0) -> Dict[str, Any]:
        """Calculates RICE, ICE, and weighted prioritization scores with robust boundary and input validation."""
        if effort <= 0:
            raise ValueError("Effort estimate must be strictly greater than zero.")
        if reach < 0.0:
            raise ValueError("Reach cannot be negative.")
        if reach < 1.0:
            reach = 1.0
        if impact <= 0 or impact > 10.0:
            raise ValueError("Impact must be between 0.1 and 10.0.")
        if confidence <= 0 or confidence > 1.0:
            raise ValueError("Confidence must be between 0.01 and 1.0.")
        if ease <= 0 or ease > 10.0:
            raise ValueError("Ease must be between 0.1 and 10.0.")

        rice_score = round((reach * impact * confidence) / effort, 2)
        ice_score = round(impact * confidence * ease, 2)
        weighted_score = round((0.6 * rice_score) + (0.4 * ice_score), 2)

        # Classification
        if impact >= 5.0 and effort <= 2.0:
            quadrant = "Quick Win"
        elif impact >= 5.0 and effort > 2.0:
            quadrant = "Major Project"
        elif impact < 5.0 and effort <= 2.0:
            quadrant = "Fill-in"
        else:
            quadrant = "Thankless Task"

        return {
            "rice_score": rice_score,
            "ice_score": ice_score,
            "weighted_score": weighted_score,
            "quadrant": quadrant,
            "formula_metadata": {
                "rice_formula": "(reach * impact * confidence) / effort",
                "ice_formula": "impact * confidence * ease",
                "reach": reach,
                "impact": impact,
                "confidence": confidence,
                "effort": effort,
                "ease": ease,
            },
        }

    @staticmethod
    def convert_idea(
        db: Session,
        idea_id: str,
        target_type: str,
        user_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        target_date: Optional[datetime] = None,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Converts an idea into a feature request, task, or roadmap deliverable."""
        idea = db.query(ProductIdea).filter(ProductIdea.id == idea_id).first()
        if not idea:
            raise ValueError(f"Idea '{idea_id}' not found.")

        target_type_upper = target_type.upper()
        target_id = ""

        if target_type_upper == "FEATURE_REQUEST":
            feat_id = f"freq_{uuid.uuid4().hex[:12]}"
            feature = ProductFeatureRequest(
                id=feat_id,
                title=idea.title,
                description=idea.proposed_solution or idea.description,
                customer_name="Internal Innovation Lab",
                customer_segment="ENTERPRISE",
                source="INTERNAL",
                request_count=1,
                priority=idea.priority,
                status="NEW",
                linked_idea_id=idea.id,
                owner_id=user_id,
                organization_id=organization_id or idea.organization_id,
                workspace_id=workspace_id or idea.workspace_id,
            )
            db.add(feature)
            idea.status = "VALIDATED"
            idea.linked_feature_id = feat_id
            target_id = feat_id

        elif target_type_upper == "TASK":
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            task = Task(
                id=task_id,
                title=idea.title,
                description=idea.proposed_solution or idea.description,
                status="Todo",
                priority=idea.priority.title() if idea.priority else "Medium",
                user_id=user_id,
                workspace_id=workspace_id or idea.workspace_id or 1,
                project_id=project_id,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(task)
            idea.status = "IN_PROGRESS"
            idea.linked_task_id = task_id
            target_id = task_id

        elif target_type_upper == "ROADMAP_ITEM":
            rmi_id = f"lrmi_{uuid.uuid4().hex[:12]}"
            rmi = LifecycleRoadmapItem(
                id=rmi_id,
                title=idea.title,
                description=idea.proposed_solution or idea.description,
                product_area=idea.product_area,
                status="PLANNED",
                priority=idea.priority,
                quarter="Q2-2027",
                owner_id=user_id,
                organization_id=organization_id or idea.organization_id,
                workspace_id=workspace_id or idea.workspace_id,
                linked_feature_id=idea.linked_feature_id,
                linked_task_id=idea.linked_task_id,
            )
            db.add(rmi)
            idea.status = "PLANNED"
            target_id = rmi_id

        else:
            raise ValueError(f"Unsupported target_type '{target_type}'. Supported: FEATURE_REQUEST, TASK, ROADMAP_ITEM")

        idea.updated_at = utc_now()
        db.commit()
        db.refresh(idea)

        # Trigger B15 automation event
        try:
            from app.services.automation_engine_service import dispatch_automation_event
            dispatch_automation_event(
                db,
                event_name="product.idea_converted",
                payload={"idea_id": idea_id, "target_type": target_type_upper, "target_id": target_id},
                workspace_id=workspace_id or idea.workspace_id,
                actor_id=user_id,
            )
        except Exception:
            pass

        return {
            "status": "CONVERTED",
            "target_type": target_type_upper,
            "target_id": target_id,
            "idea_id": idea.id,
            "message": f"Successfully converted idea '{idea.title}' to {target_type_upper} ({target_id}).",
        }

    @staticmethod
    def create_roadmap_dependency(
        db: Session,
        roadmap_item_id: str,
        depends_on_item_id: str,
        dependency_type: str = "BLOCKS",
        risk_level: str = "MEDIUM",
        notes: Optional[str] = None,
        organization_id: Optional[int] = None,
    ) -> RoadmapDependency:
        """Creates roadmap dependency with automated cycle detection."""
        if roadmap_item_id == depends_on_item_id:
            raise ValueError("Roadmap item cannot depend on itself.")

        # Verify items exist
        item1 = db.query(LifecycleRoadmapItem).filter(LifecycleRoadmapItem.id == roadmap_item_id).first()
        item2 = db.query(LifecycleRoadmapItem).filter(LifecycleRoadmapItem.id == depends_on_item_id).first()
        if not item1 or not item2:
            raise ValueError("Both roadmap items must exist to create a dependency.")

        # Cycle detection: check if roadmap_item_id is reachable from depends_on_item_id
        visited = set()
        stack = [depends_on_item_id]
        while stack:
            curr = stack.pop()
            if curr == roadmap_item_id:
                raise ValueError("Circular dependency detected: adding this dependency would create a cycle.")
            if curr not in visited:
                visited.add(curr)
                children = db.query(RoadmapDependency.depends_on_item_id).filter(
                    RoadmapDependency.roadmap_item_id == curr
                ).all()
                for (ch,) in children:
                    if ch not in visited:
                        stack.append(ch)

        dep = RoadmapDependency(
            id=f"rdep_{uuid.uuid4().hex[:12]}",
            roadmap_item_id=roadmap_item_id,
            depends_on_item_id=depends_on_item_id,
            dependency_type=dependency_type,
            risk_level=risk_level,
            notes=notes,
            status="ACTIVE",
            created_at=utc_now(),
        )
        db.add(dep)
        db.commit()
        db.refresh(dep)
        return dep

    @staticmethod
    def reorder_roadmap_items(
        db: Session,
        items: List[Dict[str, Any]],
        organization_id: Optional[int] = None,
    ) -> List[LifecycleRoadmapItem]:
        """Updates sort_order and quarter positioning for drag-and-drop roadmap items."""
        updated = []
        for itm in items:
            item_id = itm.get("id")
            order = itm.get("sort_order", 0)
            quarter = itm.get("quarter")

            query = db.query(LifecycleRoadmapItem).filter(LifecycleRoadmapItem.id == item_id)
            if organization_id is not None:
                query = query.filter(LifecycleRoadmapItem.organization_id == organization_id)
            record = query.first()
            if record:
                record.sort_order = order
                if quarter:
                    record.quarter = quarter
                record.updated_at = utc_now()
                updated.append(record)

        db.commit()
        return updated

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
            id=f"easn_{uuid.uuid4().hex[:12]}",
            experiment_id=experiment_id,
            variant_id=selected_variant.id,
            user_id=user_id,
            assigned_at=utc_now(),
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
            id=f"eevt_{uuid.uuid4().hex[:12]}",
            experiment_id=experiment_id,
            variant_id=assignment.variant_id,
            user_id=user_id,
            event_name=event_name,
            metric_value=metric_value,
            timestamp=utc_now(),
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
    def analyze_experiment_statistics(
        db: Session,
        experiment_id: str,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Calculates rigorous statistical significance, relative uplift, z-score, and p-value."""
        exp_query = db.query(ProductExperiment).filter(ProductExperiment.id == experiment_id)
        if organization_id is not None:
            exp_query = exp_query.filter(ProductExperiment.organization_id == organization_id)
        exp = exp_query.first()
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found.")

        variants = db.query(ExperimentVariant).filter(
            ExperimentVariant.experiment_id == experiment_id
        ).order_by(ExperimentVariant.variant_key).all()

        if len(variants) < 2:
            return {
                "experiment_id": experiment_id,
                "status": exp.status,
                "primary_metric": exp.primary_metric,
                "total_sample_size": exp.total_sample_size,
                "control_variant": variants[0].variant_key if variants else None,
                "control_conversion_rate": variants[0].conversion_rate if variants else 0.0,
                "treatment_variant": None,
                "treatment_conversion_rate": 0.0,
                "relative_uplift_pct": 0.0,
                "z_score": 0.0,
                "p_value": 1.0,
                "is_statistically_significant": False,
                "confidence_interval_95": [0.0, 0.0],
                "sample_sufficient": False,
                "conclusion": "Insufficient variants to calculate statistical significance. Need at least 2 variants.",
            }

        control = variants[0]
        treatment = variants[1]

        n_c = control.impression_count
        x_c = control.conversion_count
        n_t = treatment.impression_count
        x_t = treatment.conversion_count

        p_c = (x_c / n_c) if n_c > 0 else 0.0
        p_t = (x_t / n_t) if n_t > 0 else 0.0

        uplift = ((p_t - p_c) / p_c * 100.0) if p_c > 0 else 0.0
        uplift = round(uplift, 2)

        sample_sufficient = (n_c >= 30 and n_t >= 30)
        z_score = 0.0
        p_value = 1.0
        ci_lower = 0.0
        ci_upper = 0.0
        sig = False

        if n_c > 0 and n_t > 0:
            p_pool = (x_c + x_t) / (n_c + n_t)
            se_pool = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n_c + 1.0 / n_t)) if 0 < p_pool < 1 else 0.0
            if se_pool > 0:
                z_score = (p_t - p_c) / se_pool
                # Two-tailed p-value
                p_value = 1.0 - math.erf(abs(z_score) / math.sqrt(2.0))
                p_value = max(0.0001, min(1.0, round(p_value, 4)))

            se_diff = math.sqrt((p_c * (1.0 - p_c) / n_c) + (p_t * (1.0 - p_t) / n_t))
            ci_lower = round((p_t - p_c - 1.96 * se_diff) * 100.0, 2)
            ci_upper = round((p_t - p_c + 1.96 * se_diff) * 100.0, 2)

            if p_value < 0.05 and sample_sufficient:
                sig = True

        z_score = round(z_score, 2)

        if sig and uplift > 0:
            conclusion = f"Statistically significant positive uplift of +{uplift}% detected with 95% confidence (p={p_value}). Treatment '{treatment.variant_name}' outperforms control."
        elif sig and uplift < 0:
            conclusion = f"Statistically significant negative impact of {uplift}% detected (p={p_value}). Treatment underperforms control."
        elif not sample_sufficient:
            conclusion = f"Sample size insufficient ({n_c + n_t} total impressions, recommended min 60). Experiment continues gathering data."
        else:
            conclusion = f"No statistically significant difference detected between variants (p={p_value} >= 0.05)."

        res = {
            "experiment_id": experiment_id,
            "status": exp.status,
            "primary_metric": exp.primary_metric,
            "total_sample_size": exp.total_sample_size,
            "control_variant": control.variant_key,
            "control_conversion_rate": round(p_c * 100.0, 2),
            "treatment_variant": treatment.variant_key,
            "treatment_conversion_rate": round(p_t * 100.0, 2),
            "relative_uplift_pct": uplift,
            "z_score": z_score,
            "p_value": p_value,
            "is_statistically_significant": sig,
            "confidence_interval_95": [ci_lower, ci_upper],
            "sample_sufficient": sample_sufficient,
            "conclusion": conclusion,
        }
        exp.statistical_summary_json = json.dumps(res)
        exp.conclusion = conclusion
        db.commit()
        return res

    @staticmethod
    def calculate_release_readiness(
        db: Session,
        release_id: str,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Computes verifiable release readiness score based on feature completion and risk blockers."""
        rel_q = db.query(ProductRelease).filter(ProductRelease.id == release_id)
        if organization_id is not None:
            rel_q = rel_q.filter(ProductRelease.organization_id == organization_id)
        rel = rel_q.first()
        if not rel:
            raise ValueError(f"Release {release_id} not found.")

        # Features linked or in scope
        feat_q = db.query(ProductFeatureRequest)
        if rel.organization_id is not None:
            feat_q = feat_q.filter(ProductFeatureRequest.organization_id == rel.organization_id)
        features = feat_q.all()

        total_feats = len(features)
        completed_feats = sum(1 for f in features if f.status in ["RELEASED", "COMPLETED"])

        # Open risks
        risk_q = db.query(ProductRiskRecord).filter(
            ProductRiskRecord.status.in_(["IDENTIFIED", "ASSESSED", "MITIGATING"])
        )
        if rel.organization_id is not None:
            risk_q = risk_q.filter(ProductRiskRecord.organization_id == rel.organization_id)
        risks = risk_q.all()

        crit_risks = sum(1 for r in risks if r.severity == "CRITICAL")
        high_risks = sum(1 for r in risks if r.severity == "HIGH")

        blockers = []
        if crit_risks > 0:
            blockers.append(f"{crit_risks} unresolved CRITICAL product risk(s) identified")
        if total_feats > 0 and completed_feats < (total_feats / 2.0):
            blockers.append(f"Less than 50% of scheduled features completed ({completed_feats}/{total_feats})")

        # Base score from feature completion
        base_score = 100.0
        if total_feats > 0:
            base_score = (completed_feats / total_feats) * 100.0

        risk_deduction = (crit_risks * 25.0) + (high_risks * 10.0)
        final_score = max(0.0, min(100.0, round(base_score - risk_deduction, 1)))

        if final_score >= 85.0 and not blockers:
            readiness_status = "READY_FOR_RELEASE"
        elif final_score >= 65.0:
            readiness_status = "ON_TRACK"
        elif final_score >= 40.0:
            readiness_status = "AT_RISK"
        else:
            readiness_status = "BLOCKED"

        rel.readiness_score = final_score
        rel.readiness_status = readiness_status
        db.commit()

        return {
            "release_id": release_id,
            "release_version": rel.release_version,
            "readiness_score": final_score,
            "readiness_status": readiness_status,
            "linked_features_count": total_feats,
            "completed_features_count": completed_feats,
            "open_risks_count": len(risks),
            "blockers": blockers,
            "details": {
                "critical_risks": crit_risks,
                "high_risks": high_risks,
                "feature_completion_rate": round((completed_feats / total_feats * 100.0), 1) if total_feats > 0 else 100.0,
            },
        }

    @staticmethod
    def get_lifecycle_overview(db: Session, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Returns consolidated metric aggregates across the entire product lifecycle funnel."""
        def apply_filter(query, model):
            if organization_id is not None:
                return query.filter(model.organization_id == organization_id)
            return query

        disc_count = apply_filter(db.query(func.count(ProductDiscovery.id)), ProductDiscovery).scalar() or 0
        ideas_count = apply_filter(db.query(func.count(ProductIdea.id)), ProductIdea).scalar() or 0
        freq_count = apply_filter(db.query(func.count(ProductFeatureRequest.id)), ProductFeatureRequest).scalar() or 0

        demand_sum = apply_filter(db.query(func.sum(ProductFeatureRequest.request_count)), ProductFeatureRequest).scalar() or 0
        revenue_sum = apply_filter(db.query(func.sum(ProductFeatureRequest.revenue_impact)), ProductFeatureRequest).scalar() or 0.0

        initiatives_count = apply_filter(db.query(func.count(ProductInitiative.id)), ProductInitiative).scalar() or 0
        roadmap_count = apply_filter(db.query(func.count(LifecycleRoadmapItem.id)), LifecycleRoadmapItem).scalar() or 0
        experiments_count = apply_filter(db.query(func.count(ProductExperiment.id)), ProductExperiment).filter(ProductExperiment.status == "RUNNING").scalar() or 0
        releases_count = apply_filter(db.query(func.count(ProductRelease.id)), ProductRelease).scalar() or 0

        return {
            "total_discoveries": disc_count,
            "total_ideas": ideas_count,
            "total_feature_requests": freq_count,
            "total_customer_demand_count": demand_sum,
            "total_pipeline_revenue_impact": round(revenue_sum, 2),
            "total_initiatives": initiatives_count,
            "total_roadmap_items": roadmap_count,
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

    @staticmethod
    def execute_product_lifecycle_automation_action(
        db: Session,
        action_type: str,
        config: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """B15 Automation Engine handler for product lifecycle operations."""
        norm_action = action_type.replace("product.", "").replace(".", "_").lower()
        merged = {**payload, **config}

        if norm_action in ["create_idea", "create_product_idea"]:
            title = merged.get("title", "New Automated Idea")
            desc = merged.get("description", "")
            idea = ProductIdea(
                id=f"idea_{uuid.uuid4().hex[:12]}",
                title=title,
                description=desc,
                problem_statement=merged.get("problem_statement", desc),
                proposed_solution=merged.get("proposed_solution", desc),
                priority=merged.get("priority", "MEDIUM"),
                status="NEW",
                organization_id=merged.get("organization_id"),
                workspace_id=merged.get("workspace_id"),
            )
            db.add(idea)
            db.commit()
            db.refresh(idea)
            return {"status": "success", "action": action_type, "idea_id": idea.id}

        elif norm_action in ["update_idea_status", "update_product_idea_status"]:
            idea_id = merged.get("idea_id")
            new_status = merged.get("status", "VALIDATED")
            idea = db.query(ProductIdea).filter(ProductIdea.id == idea_id).first()
            if not idea:
                return {"status": "error", "reason": f"Idea {idea_id} not found"}
            idea.status = new_status
            idea.updated_at = utc_now()
            db.commit()
            return {"status": "success", "action": action_type, "new_status": new_status}

        elif norm_action in ["create_feature_request", "create_product_feature_request"]:
            title = merged.get("title", "Feature Request")
            freq = ProductFeatureRequest(
                id=f"freq_{uuid.uuid4().hex[:12]}",
                title=title,
                description=merged.get("description", ""),
                customer_name=merged.get("customer_name", "Enterprise Customer"),
                source=merged.get("source", "AUTOMATION"),
                priority=merged.get("priority", "HIGH"),
                status="NEW",
                revenue_impact=float(merged.get("revenue_impact", 0.0)),
                organization_id=merged.get("organization_id"),
                workspace_id=merged.get("workspace_id"),
            )
            db.add(freq)
            db.commit()
            db.refresh(freq)
            return {"status": "success", "action": action_type, "feature_request_id": freq.id}

        elif norm_action in ["update_feature_status", "update_feature_request_status"]:
            freq_id = merged.get("feature_request_id") or merged.get("freq_id")
            new_status = merged.get("status", "PRIORITIZED")
            freq = db.query(ProductFeatureRequest).filter(ProductFeatureRequest.id == freq_id).first()
            if not freq:
                return {"status": "error", "reason": f"Feature request {freq_id} not found"}
            freq.status = new_status
            freq.updated_at = utc_now()
            db.commit()
            return {"status": "success", "action": action_type, "new_status": new_status}

        elif norm_action in ["create_release", "create_product_release"]:
            version = merged.get("release_version") or f"v{uuid.uuid4().hex[:4]}"
            title = merged.get("title", f"Release {version}")
            rel = ProductRelease(
                id=f"prel_{uuid.uuid4().hex[:12]}",
                release_version=version,
                title=title,
                description=merged.get("description", "Automated deployment release"),
                status="PLANNED",
                release_notes=merged.get("release_notes", "Automated release notes"),
                organization_id=merged.get("organization_id"),
                workspace_id=merged.get("workspace_id"),
            )
            db.add(rel)
            db.commit()
            db.refresh(rel)
            return {"status": "success", "action": action_type, "release_id": rel.id}

        elif norm_action in ["advance_release_stage", "update_release_status"]:
            rel_id = merged.get("release_id")
            new_status = merged.get("status", "DEVELOPMENT")
            rel = db.query(ProductRelease).filter(ProductRelease.id == rel_id).first()
            if not rel:
                return {"status": "error", "reason": f"Release {rel_id} not found"}
            rel.status = new_status
            rel.updated_at = utc_now()
            db.commit()
            return {"status": "success", "action": action_type, "new_status": new_status}

        return {"status": "unsupported_action", "action_type": action_type}


def execute_product_lifecycle_automation_action(
    db: Session,
    action_type: str,
    payload: Dict[str, Any],
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    conf = dict(config or {})
    if organization_id and "organization_id" not in conf:
        conf["organization_id"] = organization_id
    if user_id and "user_id" not in conf:
        conf["user_id"] = user_id
    return ProductLifecycleService.execute_product_lifecycle_automation_action(
        db=db,
        action_type=action_type,
        config=conf,
        payload=payload,
    )

