import json
import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc, not_

from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.team import Team, TeamMember
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.board import Board
from app.models.comment import Comment
from app.models.organization import Organization, OrganizationMember
from app.models.search import SearchHistory, SavedSearch
from app.schemas.search import (
    SearchResultItem,
    SearchFacets,
    SearchResponse,
    SearchSuggestionItem,
    SearchSuggestionsResponse,
    SearchHistoryItemResponse,
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchResponse,
    AdvancedFilterRequest,
)

def utc_now() -> datetime:
    return datetime.utcnow()

class SearchService:
    # -------------------------------------------------------------
    # User Context & Authorization Helpers
    # -------------------------------------------------------------
    def get_user_context(self, db: Session, user_id: int) -> Tuple[List[int], List[int], List[int]]:
        """
        Determine user accessible workspace IDs, organization IDs, and team IDs.
        Enforces tenant isolation across all multi-entity searches.
        """
        # Workspaces: owned + member
        ws_owned = [w.id for w in db.query(Workspace.id).filter(Workspace.owner_id == user_id).all()]
        ws_member = [m.workspace_id for m in db.query(WorkspaceMember.workspace_id).filter(
            WorkspaceMember.user_id == user_id
        ).all()]
        accessible_workspace_ids = list(set(ws_owned + ws_member))

        # Organizations: owned + member
        org_owned = [o.id for o in db.query(Organization.id).filter(Organization.owner_id == user_id).all()]
        org_member = [m.organization_id for m in db.query(OrganizationMember.organization_id).filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True
        ).all()]
        accessible_org_ids = list(set(org_owned + org_member))

        # Teams: owned + member
        team_owned = [t.id for t in db.query(Team.id).filter(Team.owner_id == user_id).all()]
        team_member = [m.team_id for m in db.query(TeamMember.team_id).filter(
            TeamMember.user_id == user_id,
            TeamMember.status == "ACTIVE"
        ).all()]
        accessible_team_ids = list(set(team_owned + team_member))

        return accessible_workspace_ids, accessible_org_ids, accessible_team_ids

    def calculate_relevance(
        self,
        title: str,
        description: Optional[str],
        query: str,
        updated_at: Optional[datetime] = None
    ) -> float:
        """Score result relevance based on exact, prefix, partial match, and recency."""
        if not query or not query.strip():
            return 1.0

        q_clean = query.strip().lower()
        t_clean = (title or "").strip().lower()
        d_clean = (description or "").strip().lower()

        score = 0.0

        if t_clean == q_clean:
            score += 10.0
        elif t_clean.startswith(q_clean):
            score += 6.0
        elif q_clean in t_clean:
            score += 3.5

        if d_clean and q_clean in d_clean:
            score += 1.5

        if updated_at:
            # Boost items updated in the last 7 days
            try:
                days_old = (utc_now() - updated_at).days
                if days_old <= 7:
                    score += 0.8
                elif days_old <= 30:
                    score += 0.3
            except Exception:
                pass

        return round(score if score > 0 else 0.5, 2)

    # -------------------------------------------------------------
    # Entity-Specific Searches
    # -------------------------------------------------------------
    def search_tasks(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        assignee_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        due_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[SearchResultItem]:
        """Search tasks accessible to the user."""
        ws_ids, _, _ = self.get_user_context(db, current_user.id)

        # Authorization: user owns the task OR task belongs to an accessible workspace
        auth_cond = (Task.user_id == current_user.id)
        if ws_ids:
            auth_cond = or_(auth_cond, Task.workspace_id.in_(ws_ids))

        query = db.query(Task).filter(auth_cond, Task.is_deleted == False)

        if workspace_id is not None:
            query = query.filter(Task.workspace_id == workspace_id)
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)
        if status and status.lower() != "all":
            query = query.filter(Task.status.ilike(status))
        if priority and priority.lower() != "all":
            query = query.filter(Task.priority.ilike(priority))
        if category and category.lower() != "all":
            query = query.filter(Task.category.ilike(category))
        if assignee_id is not None:
            query = query.filter(Task.assignee_id == assignee_id)
        if due_date:
            query = query.filter(Task.due_date == due_date)

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Task.title).like(term),
                    func.lower(Task.description).like(term),
                    func.lower(Task.category).like(term),
                    Task.id.like(f"%{q.strip()}%"),
                )
            )

        tasks = query.order_by(desc(Task.updated_at)).limit(limit).all()
        results = []
        for t in tasks:
            score = self.calculate_relevance(t.title, t.description, q or "", t.updated_at)
            results.append(SearchResultItem(
                id=str(t.id),
                type="TASK",
                title=t.title,
                description=t.description,
                status=t.status,
                priority=t.priority,
                category=t.category,
                workspace_id=t.workspace_id,
                project_id=t.project_id,
                score=score,
                metadata={"assignee_id": t.assignee_id, "due_date": t.due_date},
                created_at=t.created_at,
                url_path=f"/?task_id={t.id}" if not t.workspace_id else f"/workspaces/{t.workspace_id}?task_id={t.id}"
            ))
        return results

    def search_projects(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        workspace_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[SearchResultItem]:
        """Search projects accessible to the user."""
        ws_ids, org_ids, _ = self.get_user_context(db, current_user.id)

        auth_cond = (Project.owner_id == current_user.id)
        if ws_ids:
            auth_cond = or_(auth_cond, Project.workspace_id.in_(ws_ids))
        if org_ids:
            auth_cond = or_(auth_cond, Project.organization_id.in_(org_ids))

        query = db.query(Project).filter(auth_cond, Project.is_deleted == False)

        if workspace_id is not None:
            query = query.filter(Project.workspace_id == workspace_id)
        if status and status.lower() != "all":
            query = query.filter(Project.status.ilike(status))
        if priority and priority.lower() != "all":
            query = query.filter(Project.priority.ilike(priority))
        if category and category.lower() != "all":
            query = query.filter(Project.category.ilike(category))

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Project.name).like(term),
                    func.lower(Project.description).like(term),
                )
            )

        projects = query.order_by(desc(Project.updated_at)).limit(limit).all()
        results = []
        for p in projects:
            score = self.calculate_relevance(p.name, p.description, q or "", p.updated_at)
            results.append(SearchResultItem(
                id=str(p.id),
                type="PROJECT",
                title=p.name,
                description=p.description,
                status=p.status,
                priority=p.priority,
                category=p.category or "Project",
                workspace_id=p.workspace_id,
                project_id=p.id,
                score=score,
                created_at=p.created_at,
                url_path=f"/workspaces/{p.workspace_id}?project_id={p.id}" if p.workspace_id else f"/projects/{p.id}"
            ))
        return results

    def search_teams(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        limit: int = 100,
    ) -> List[SearchResultItem]:
        """Search teams accessible to the user."""
        _, org_ids, team_ids = self.get_user_context(db, current_user.id)

        auth_cond = (Team.owner_id == current_user.id)
        if team_ids:
            auth_cond = or_(auth_cond, Team.id.in_(team_ids))
        if org_ids:
            auth_cond = or_(auth_cond, Team.organization_id.in_(org_ids))

        query = db.query(Team).filter(auth_cond)

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Team.name).like(term),
                    func.lower(Team.description).like(term),
                )
            )

        teams = query.order_by(desc(Team.updated_at)).limit(limit).all()
        results = []
        for tm in teams:
            score = self.calculate_relevance(tm.name, tm.description, q or "", tm.updated_at)
            results.append(SearchResultItem(
                id=str(tm.id),
                type="TEAM",
                title=tm.name,
                description=tm.description,
                status=tm.status,
                team_id=tm.id,
                workspace_id=tm.workspace_id,
                score=score,
                created_at=tm.created_at,
                url_path=f"/teams/{tm.id}"
            ))
        return results

    def search_workspaces(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        limit: int = 100,
    ) -> List[SearchResultItem]:
        """Search workspaces accessible to the user."""
        ws_ids, org_ids, _ = self.get_user_context(db, current_user.id)

        auth_cond = (Workspace.owner_id == current_user.id)
        if ws_ids:
            auth_cond = or_(auth_cond, Workspace.id.in_(ws_ids))
        if org_ids:
            auth_cond = or_(auth_cond, Workspace.organization_id.in_(org_ids))

        query = db.query(Workspace).filter(auth_cond)

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Workspace.name).like(term),
                    func.lower(Workspace.description).like(term),
                )
            )

        workspaces = query.order_by(desc(Workspace.updated_at)).limit(limit).all()
        results = []
        for w in workspaces:
            score = self.calculate_relevance(w.name, w.description, q or "", w.updated_at)
            results.append(SearchResultItem(
                id=str(w.id),
                type="WORKSPACE",
                title=w.name,
                description=w.description,
                status="ACTIVE",
                workspace_id=w.id,
                score=score,
                created_at=w.created_at,
                url_path=f"/workspaces/{w.id}"
            ))
        return results

    def search_boards(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        workspace_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[SearchResultItem]:
        """Search boards accessible to the user."""
        ws_ids, org_ids, _ = self.get_user_context(db, current_user.id)

        auth_cond = (Board.owner_id == current_user.id)
        if ws_ids:
            auth_cond = or_(auth_cond, Board.workspace_id.in_(ws_ids))
        if org_ids:
            auth_cond = or_(auth_cond, Board.organization_id.in_(org_ids))

        query = db.query(Board).filter(auth_cond, Board.is_archived == False)

        if workspace_id is not None:
            query = query.filter(Board.workspace_id == workspace_id)

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Board.name).like(term),
                    func.lower(Board.description).like(term),
                )
            )

        boards = query.order_by(desc(Board.updated_at)).limit(limit).all()
        results = []
        for b in boards:
            score = self.calculate_relevance(b.name, b.description, q or "", b.updated_at)
            results.append(SearchResultItem(
                id=str(b.id),
                type="BOARD",
                title=b.name,
                description=b.description,
                status="ACTIVE",
                workspace_id=b.workspace_id,
                project_id=b.project_id,
                score=score,
                created_at=b.created_at,
                url_path=f"/boards/{b.id}"
            ))
        return results

    def search_members(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        limit: int = 100,
    ) -> List[SearchResultItem]:
        """
        Search members with strict tenant isolation.
        Users can ONLY discover users who share an organization, workspace, or team.
        """
        ws_ids, org_ids, team_ids = self.get_user_context(db, current_user.id)

        co_user_ids = set()

        if org_ids:
            org_members = db.query(OrganizationMember.user_id).filter(
                OrganizationMember.organization_id.in_(org_ids),
                OrganizationMember.is_active == True
            ).all()
            co_user_ids.update(m[0] for m in org_members)

        if ws_ids:
            ws_members = db.query(WorkspaceMember.user_id).filter(
                WorkspaceMember.workspace_id.in_(ws_ids)
            ).all()
            co_user_ids.update(m[0] for m in ws_members)

        if team_ids:
            team_members = db.query(TeamMember.user_id).filter(
                TeamMember.team_id.in_(team_ids),
                TeamMember.status == "ACTIVE"
            ).all()
            co_user_ids.update(m[0] for m in team_members)

        co_user_ids.add(current_user.id)

        query = db.query(User).filter(
            User.id.in_(list(co_user_ids)),
            User.is_active == True
        )

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.name).like(term),
                    func.lower(User.display_name).like(term),
                    func.lower(User.email).like(term),
                )
            )

        users = query.order_by(asc(User.name)).limit(limit).all()
        results = []
        for u in users:
            display = u.display_name or u.name
            score = self.calculate_relevance(display, u.email, q or "", u.updated_at)
            results.append(SearchResultItem(
                id=str(u.id),
                type="MEMBER",
                title=display,
                description=u.email,
                status=u.status,
                score=score,
                metadata={"role": u.role, "avatar_url": u.avatar_url},
                created_at=u.created_at,
                url_path=f"/profile/{u.id}"
            ))
        return results

    def search_comments(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        limit: int = 100,
    ) -> List[SearchResultItem]:
        """Search comments with tenant access control."""
        ws_ids, org_ids, _ = self.get_user_context(db, current_user.id)

        auth_cond = (Comment.author_id == current_user.id)
        if ws_ids:
            auth_cond = or_(auth_cond, Comment.workspace_id.in_(ws_ids))
        if org_ids:
            auth_cond = or_(auth_cond, Comment.organization_id.in_(org_ids))

        query = db.query(Comment).filter(auth_cond, Comment.is_deleted == False)

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(func.lower(Comment.content).like(term))

        comments = query.order_by(desc(Comment.created_at)).limit(limit).all()
        results = []
        for c in comments:
            snippet = c.content[:100] + ("..." if len(c.content) > 100 else "")
            score = self.calculate_relevance(snippet, None, q or "", c.updated_at)
            results.append(SearchResultItem(
                id=str(c.id),
                type="COMMENT",
                title=f"Comment on {c.entity_type} #{c.entity_id}",
                description=snippet,
                status="ACTIVE",
                workspace_id=c.workspace_id,
                project_id=c.project_id,
                score=score,
                metadata={"entity_type": c.entity_type, "entity_id": c.entity_id},
                created_at=c.created_at,
                url_path=f"/?task_id={c.entity_id}" if c.entity_type == "TASK" else f"/comments/{c.id}"
            ))
        return results

    # -------------------------------------------------------------
    # Global Search Aggregator
    # -------------------------------------------------------------
    def global_search(
        self,
        db: Session,
        current_user: User,
        q: Optional[str] = None,
        type: Optional[str] = "ALL",
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = "relevance",
        sort_order: str = "desc",
    ) -> SearchResponse:
        """Centralized unified global search across all FocusBoard entities."""
        target_type = (type or "ALL").upper()
        all_results: List[SearchResultItem] = []
        by_type_counts: Dict[str, int] = {
            "TASK": 0, "PROJECT": 0, "BOARD": 0, "TEAM": 0, "WORKSPACE": 0, "MEMBER": 0, "COMMENT": 0
        }
        by_status_counts: Dict[str, int] = {}
        by_priority_counts: Dict[str, int] = {}

        # 1. Fetch from each requested entity domain
        if target_type in ["ALL", "TASK"]:
            tasks = self.search_tasks(
                db=db, current_user=current_user, q=q, status=status,
                priority=priority, category=category, workspace_id=workspace_id,
                project_id=project_id, limit=200
            )
            by_type_counts["TASK"] = len(tasks)
            all_results.extend(tasks)

        if target_type in ["ALL", "PROJECT"]:
            projects = self.search_projects(
                db=db, current_user=current_user, q=q, status=status,
                priority=priority, category=category, workspace_id=workspace_id, limit=200
            )
            by_type_counts["PROJECT"] = len(projects)
            all_results.extend(projects)

        if target_type in ["ALL", "BOARD"]:
            boards = self.search_boards(
                db=db, current_user=current_user, q=q, workspace_id=workspace_id, limit=200
            )
            by_type_counts["BOARD"] = len(boards)
            all_results.extend(boards)

        if target_type in ["ALL", "TEAM"]:
            teams = self.search_teams(
                db=db, current_user=current_user, q=q, limit=200
            )
            by_type_counts["TEAM"] = len(teams)
            all_results.extend(teams)

        if target_type in ["ALL", "WORKSPACE"]:
            workspaces = self.search_workspaces(
                db=db, current_user=current_user, q=q, limit=200
            )
            by_type_counts["WORKSPACE"] = len(workspaces)
            all_results.extend(workspaces)

        if target_type in ["ALL", "MEMBER"]:
            members = self.search_members(
                db=db, current_user=current_user, q=q, limit=200
            )
            by_type_counts["MEMBER"] = len(members)
            all_results.extend(members)

        if target_type in ["ALL", "COMMENT"]:
            comments = self.search_comments(
                db=db, current_user=current_user, q=q, limit=200
            )
            by_type_counts["COMMENT"] = len(comments)
            all_results.extend(comments)

        # 2. Compute facets
        for item in all_results:
            if item.status:
                by_status_counts[item.status] = by_status_counts.get(item.status, 0) + 1
            if item.priority:
                by_priority_counts[item.priority] = by_priority_counts.get(item.priority, 0) + 1

        # 3. Sort results
        reverse = (sort_order.lower() == "desc")
        if sort_by == "relevance" and q and q.strip():
            all_results.sort(key=lambda x: (x.score or 0.0, x.created_at or datetime.min), reverse=reverse)
        elif sort_by == "title":
            all_results.sort(key=lambda x: (x.title or "").lower(), reverse=reverse)
        else:
            all_results.sort(key=lambda x: x.created_at or datetime.min, reverse=reverse)

        # 4. Paginate
        total = len(all_results)
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = all_results[start_idx:end_idx]

        # 5. Record Search History asynchronously / in session
        if q and q.strip():
            try:
                self.record_history(
                    db=db,
                    user_id=current_user.id,
                    query=q.strip(),
                    entity_type=target_type,
                    result_count=total,
                )
            except Exception:
                pass

        return SearchResponse(
            results=paginated_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            facets=SearchFacets(
                by_type=by_type_counts,
                by_status=by_status_counts,
                by_priority=by_priority_counts,
            )
        )

    # -------------------------------------------------------------
    # Autocomplete Suggestions
    # -------------------------------------------------------------
    def get_suggestions(
        self,
        db: Session,
        current_user: User,
        q: str,
        limit_per_type: int = 5
    ) -> SearchSuggestionsResponse:
        """Fast typeahead suggestions across tasks, projects, teams, workspaces, and members."""
        if not q or not q.strip():
            return SearchSuggestionsResponse(query="", suggestions=[], grouped={})

        clean_q = q.strip()
        grouped: Dict[str, List[SearchSuggestionItem]] = {}
        all_suggs: List[SearchSuggestionItem] = []

        # Tasks
        tasks = self.search_tasks(db, current_user, q=clean_q, limit=limit_per_type)
        if tasks:
            grouped["TASK"] = [
                SearchSuggestionItem(id=t.id, type="TASK", title=t.title, subtitle=f"{t.category or 'Task'} • {t.status}", url_path=t.url_path)
                for t in tasks
            ]
            all_suggs.extend(grouped["TASK"])

        # Projects
        projects = self.search_projects(db, current_user, q=clean_q, limit=limit_per_type)
        if projects:
            grouped["PROJECT"] = [
                SearchSuggestionItem(id=p.id, type="PROJECT", title=p.title, subtitle=f"Project • {p.status}", url_path=p.url_path)
                for p in projects
            ]
            all_suggs.extend(grouped["PROJECT"])

        # Teams
        teams = self.search_teams(db, current_user, q=clean_q, limit=limit_per_type)
        if teams:
            grouped["TEAM"] = [
                SearchSuggestionItem(id=tm.id, type="TEAM", title=tm.title, subtitle="Team", url_path=tm.url_path)
                for tm in teams
            ]
            all_suggs.extend(grouped["TEAM"])

        # Workspaces
        workspaces = self.search_workspaces(db, current_user, q=clean_q, limit=limit_per_type)
        if workspaces:
            grouped["WORKSPACE"] = [
                SearchSuggestionItem(id=w.id, type="WORKSPACE", title=w.title, subtitle="Workspace", url_path=w.url_path)
                for w in workspaces
            ]
            all_suggs.extend(grouped["WORKSPACE"])

        # Members
        members = self.search_members(db, current_user, q=clean_q, limit=limit_per_type)
        if members:
            grouped["MEMBER"] = [
                SearchSuggestionItem(id=m.id, type="MEMBER", title=m.title, subtitle=m.description, url_path=m.url_path)
                for m in members
            ]
            all_suggs.extend(grouped["MEMBER"])

        return SearchSuggestionsResponse(
            query=clean_q,
            suggestions=all_suggs[:20],
            grouped=grouped
        )

    # -------------------------------------------------------------
    # Advanced Filtering Engine
    # -------------------------------------------------------------
    def apply_advanced_filter(
        self,
        db: Session,
        current_user: User,
        filter_req: AdvancedFilterRequest
    ) -> SearchResponse:
        """
        Evaluate complex multi-field and multi-operator conditions with full security.
        Operators: eq, ne, contains, not_contains, starts_with, ends_with, is_empty, is_not_empty,
                   gt, gte, lt, lte, between, in, not_in, before, after.
        """
        entity_type = (filter_req.entity_type or "TASK").upper()
        model_cls = Task if entity_type == "TASK" else Project
        ws_ids, org_ids, _ = self.get_user_context(db, current_user.id)

        # Baseline authorization
        if entity_type == "TASK":
            auth_cond = (Task.user_id == current_user.id)
            if ws_ids:
                auth_cond = or_(auth_cond, Task.workspace_id.in_(ws_ids))
            query = db.query(Task).filter(auth_cond, Task.is_deleted == False)
        else:
            auth_cond = (Project.owner_id == current_user.id)
            if ws_ids:
                auth_cond = or_(auth_cond, Project.workspace_id.in_(ws_ids))
            if org_ids:
                auth_cond = or_(auth_cond, Project.organization_id.in_(org_ids))
            query = db.query(Project).filter(auth_cond, Project.is_deleted == False)

        clauses = []
        for cond in filter_req.conditions:
            field_name = cond.field
            op = cond.operator.lower()
            val = cond.value

            col = getattr(model_cls, field_name, None)
            if col is None:
                continue

            clause = None
            if op in ["eq", "equals"]:
                clause = (col == val)
            elif op in ["ne", "not_equals"]:
                clause = (col != val)
            elif op == "contains":
                clause = col.ilike(f"%{str(val).strip()}%")
            elif op == "not_contains":
                clause = not_(col.ilike(f"%{str(val).strip()}%"))
            elif op == "starts_with":
                clause = col.ilike(f"{str(val).strip()}%")
            elif op == "ends_with":
                clause = col.ilike(f"%{str(val).strip()}")
            elif op == "is_empty":
                clause = or_(col.is_(None), col == "")
            elif op == "is_not_empty":
                clause = and_(col.is_not(None), col != "")
            elif op in ["gt", "after", "greater_than"]:
                clause = (col > val)
            elif op in ["gte", "greater_than_or_equal"]:
                clause = (col >= val)
            elif op in ["lt", "before", "less_than"]:
                clause = (col < val)
            elif op in ["lte", "less_than_or_equal"]:
                clause = (col <= val)
            elif op == "between" and isinstance(val, list) and len(val) == 2:
                clause = col.between(val[0], val[1])
            elif op == "in" and isinstance(val, list) and val:
                clause = col.in_(val)
            elif op == "not_in" and isinstance(val, list) and val:
                clause = not_(col.in_(val))

            if clause is not None:
                clauses.append(clause)

        if clauses:
            if filter_req.match_type.upper() == "ANY":
                query = query.filter(or_(*clauses))
            else:
                query = query.filter(and_(*clauses))

        # Sorting
        sort_col = getattr(model_cls, filter_req.sort_by or "created_at", getattr(model_cls, "created_at", None))
        if sort_col is not None:
            if (filter_req.sort_order or "desc").lower() == "desc":
                query = query.order_by(desc(sort_col))
            else:
                query = query.order_by(asc(sort_col))

        total = query.count()
        page = max(1, filter_req.page or 1)
        page_size = max(1, min(100, filter_req.page_size or 20))
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        items = query.offset((page - 1) * page_size).limit(page_size).all()

        results = []
        for it in items:
            if entity_type == "TASK":
                results.append(SearchResultItem(
                    id=str(it.id),
                    type="TASK",
                    title=it.title,
                    description=it.description,
                    status=it.status,
                    priority=it.priority,
                    category=it.category,
                    workspace_id=it.workspace_id,
                    project_id=it.project_id,
                    created_at=it.created_at,
                    url_path=f"/?task_id={it.id}"
                ))
            else:
                results.append(SearchResultItem(
                    id=str(it.id),
                    type="PROJECT",
                    title=it.name,
                    description=it.description,
                    status=it.status,
                    priority=it.priority,
                    category=it.category,
                    workspace_id=it.workspace_id,
                    project_id=it.id,
                    created_at=it.created_at,
                    url_path=f"/projects/{it.id}"
                ))

        return SearchResponse(
            results=results,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            facets=SearchFacets(
                by_type={entity_type: total},
                by_status={},
                by_priority={},
            )
        )

    # -------------------------------------------------------------
    # Search History
    # -------------------------------------------------------------
    def record_history(
        self,
        db: Session,
        user_id: int,
        query: str,
        entity_type: str = "ALL",
        result_count: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchHistory:
        """Record or update user search history with query normalization."""
        clean_q = query.strip()
        norm_q = re.sub(r"\s+", " ", clean_q.lower())

        existing = db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id,
            SearchHistory.normalized_query == norm_q,
            SearchHistory.entity_type == entity_type,
        ).first()

        now = utc_now()
        if existing:
            existing.query = clean_q
            existing.last_searched_at = now
            existing.result_count = result_count
            if filters:
                existing.filters = filters
            db.commit()
            db.refresh(existing)
            return existing

        hist = SearchHistory(
            user_id=user_id,
            query=clean_q,
            normalized_query=norm_q,
            entity_type=entity_type,
            result_count=result_count,
            last_searched_at=now,
            created_at=now,
        )
        if filters:
            hist.filters = filters

        db.add(hist)
        db.commit()
        db.refresh(hist)
        return hist

    def get_history(self, db: Session, user_id: int, limit: int = 20) -> List[SearchHistory]:
        """Retrieve recent search history for the authenticated user."""
        return db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(desc(SearchHistory.last_searched_at)).limit(limit).all()

    def delete_history_item(self, db: Session, history_id: int, user_id: int) -> bool:
        """Delete an individual search history entry owned by the user."""
        item = db.query(SearchHistory).filter(
            SearchHistory.id == history_id,
            SearchHistory.user_id == user_id
        ).first()
        if not item:
            raise ValueError("History item not found")
        db.delete(item)
        db.commit()
        return True

    def clear_history(self, db: Session, user_id: int) -> int:
        """Clear all search history for the user."""
        affected = db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).delete(synchronize_session=False)
        db.commit()
        return affected

    # -------------------------------------------------------------
    # Saved Searches & Filter Presets
    # -------------------------------------------------------------
    def create_saved_search(
        self,
        db: Session,
        current_user: User,
        saved_in: SavedSearchCreate
    ) -> SavedSearch:
        """Create a new saved search / filter preset."""
        # Derive primary organization
        org_mem = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_active == True
        ).first()
        org_id = org_mem.organization_id if org_mem else None

        now = utc_now()
        saved = SavedSearch(
            user_id=current_user.id,
            organization_id=org_id,
            name=saved_in.name.strip(),
            description=saved_in.description.strip() if saved_in.description else None,
            entity_type=(saved_in.entity_type or "TASK").upper(),
            query=saved_in.query.strip() if saved_in.query else None,
            is_shared=bool(saved_in.is_shared),
            created_at=now,
            updated_at=now,
        )
        saved.filter_definition = saved_in.filter_definition or {}
        saved.sorting_config = saved_in.sorting_config or {}

        db.add(saved)
        db.commit()
        db.refresh(saved)
        return saved

    def list_saved_searches(
        self,
        db: Session,
        current_user: User,
        entity_type: Optional[str] = None
    ) -> List[SavedSearch]:
        """List saved searches owned by the user or shared within their organization."""
        org_mem = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_active == True
        ).first()
        org_id = org_mem.organization_id if org_mem else None

        auth_cond = (SavedSearch.user_id == current_user.id)
        if org_id:
            auth_cond = or_(
                auth_cond,
                and_(SavedSearch.organization_id == org_id, SavedSearch.is_shared == True)
            )

        query = db.query(SavedSearch).filter(auth_cond)
        if entity_type:
            query = query.filter(SavedSearch.entity_type == entity_type.upper())

        return query.order_by(desc(SavedSearch.updated_at)).all()

    def get_saved_search(self, db: Session, saved_id: int, current_user: User) -> SavedSearch:
        """Get a single saved search respecting ownership and sharing."""
        saved = db.query(SavedSearch).filter(SavedSearch.id == saved_id).first()
        if not saved:
            raise ValueError("Saved search not found")

        if saved.user_id != current_user.id:
            # Check sharing
            if not saved.is_shared:
                raise ValueError("Saved search not found")
            org_mem = db.query(OrganizationMember).filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == saved.organization_id,
                OrganizationMember.is_active == True
            ).first()
            if not org_mem:
                raise ValueError("Saved search not found")

        return saved

    def update_saved_search(
        self,
        db: Session,
        saved_id: int,
        update_in: SavedSearchUpdate,
        current_user: User
    ) -> SavedSearch:
        """Update a saved search owned by the user."""
        saved = db.query(SavedSearch).filter(
            SavedSearch.id == saved_id,
            SavedSearch.user_id == current_user.id
        ).first()
        if not saved:
            raise ValueError("Saved search not found")

        if update_in.name is not None:
            saved.name = update_in.name.strip()
        if update_in.description is not None:
            saved.description = update_in.description.strip()
        if update_in.query is not None:
            saved.query = update_in.query.strip() if update_in.query else None
        if update_in.filter_definition is not None:
            saved.filter_definition = update_in.filter_definition
        if update_in.sorting_config is not None:
            saved.sorting_config = update_in.sorting_config
        if update_in.is_shared is not None:
            saved.is_shared = update_in.is_shared

        saved.updated_at = utc_now()
        db.commit()
        db.refresh(saved)
        return saved

    def delete_saved_search(self, db: Session, saved_id: int, current_user: User) -> bool:
        """Delete a saved search owned by the user."""
        saved = db.query(SavedSearch).filter(
            SavedSearch.id == saved_id,
            SavedSearch.user_id == current_user.id
        ).first()
        if not saved:
            raise ValueError("Saved search not found")
        db.delete(saved)
        db.commit()
        return True

search_service = SearchService()
