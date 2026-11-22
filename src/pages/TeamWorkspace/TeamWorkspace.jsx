import React, { useState, useEffect } from 'react';
import {
  Users,
  FolderPlus,
  Plus,
  Send,
  MessageSquare,
  Activity,
  Layers,
  CheckCircle2,
  Clock,
  UserPlus,
  AlertCircle,
  Briefcase,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { collaborationApi } from '../../services/collaborationApi';
import './TeamWorkspace.css';

export function TeamWorkspace() {
  const { isAuthenticated, token, user } = useAuth();

  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [subTab, setSubTab] = useState('tasks'); // 'tasks' | 'projects' | 'activity' | 'analytics'
  const [loading, setLoading] = useState(false);

  // Data states
  const [projects, setProjects] = useState([]);
  const [workspaceTasks, setWorkspaceTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [activities, setActivities] = useState([]);
  const [teamAnalytics, setTeamAnalytics] = useState(null);

  // Modals & Drawers
  const [showCreateWsModal, setShowCreateWsModal] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [newWsDesc, setNewWsDesc] = useState('');

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('MEMBER');

  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false);
  const [newProjName, setNewProjName] = useState('');
  const [newProjDesc, setNewProjDesc] = useState('');
  const [newProjDeadline, setNewProjDeadline] = useState('');

  const [selectedTaskForComments, setSelectedTaskForComments] = useState(null);
  const [comments, setComments] = useState([]);
  const [newCommentText, setNewCommentText] = useState('');

  // 1. Fetch user workspaces
  useEffect(() => {
    if (isAuthenticated) {
      loadWorkspaces();
    }
  }, [isAuthenticated]);

  const loadWorkspaces = async () => {
    try {
      setLoading(true);
      const wsList = await collaborationApi.getWorkspaces();
      setWorkspaces(wsList || []);
      if (wsList && wsList.length > 0 && !activeWorkspace) {
        setActiveWorkspace(wsList[0]);
      }
    } catch (err) {
      console.warn('Failed to fetch workspaces:', err);
    } finally {
      setLoading(false);
    }
  };

  // 2. Fetch workspace data on active workspace change
  useEffect(() => {
    if (activeWorkspace) {
      loadWorkspaceDetails(activeWorkspace.id);
    }
  }, [activeWorkspace]);

  const loadWorkspaceDetails = async (wsId) => {
    try {
      const [projList, taskList, memberList, actList, analData] = await Promise.all([
        collaborationApi.getProjects(wsId).catch(() => []),
        collaborationApi.getWorkspaceTasks(wsId).catch(() => []),
        collaborationApi.getMembers(wsId).catch(() => []),
        collaborationApi.getActivities(wsId).catch(() => []),
        collaborationApi.getTeamAnalytics(wsId).catch(() => null),
      ]);
      setProjects(projList || []);
      setWorkspaceTasks(taskList || []);
      setMembers(memberList || []);
      setActivities(actList || []);
      setTeamAnalytics(analData);
    } catch (err) {
      console.error('Failed to load workspace data:', err);
    }
  };

  // 3. Create Workspace
  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!newWsName.trim()) return;
    try {
      const created = await collaborationApi.createWorkspace({
        name: newWsName.trim(),
        description: newWsDesc.trim(),
      });
      setWorkspaces((prev) => [...prev, created]);
      setActiveWorkspace(created);
      setShowCreateWsModal(false);
      setNewWsName('');
      setNewWsDesc('');
    } catch (err) {
      alert(`Error creating workspace: ${err.message}`);
    }
  };

  // 4. Invite Member
  const handleInviteMember = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim() || !activeWorkspace) return;
    try {
      const inv = await collaborationApi.inviteMember(activeWorkspace.id, inviteEmail.trim(), inviteRole);
      alert(`Invitation generated! Share this token for demo acceptance: ${inv.token}`);
      setShowInviteModal(false);
      setInviteEmail('');
    } catch (err) {
      alert(`Invitation error: ${err.message}`);
    }
  };

  // 5. Create Project
  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjName.trim() || !activeWorkspace) return;
    try {
      const created = await collaborationApi.createProject(activeWorkspace.id, {
        name: newProjName.trim(),
        description: newProjDesc.trim(),
        deadline: newProjDeadline || null,
      });
      setProjects((prev) => [...prev, created]);
      setShowCreateProjectModal(false);
      setNewProjName('');
      setNewProjDesc('');
      setNewProjDeadline('');
    } catch (err) {
      alert(`Error creating project: ${err.message}`);
    }
  };

  // 6. Comments Workflow
  const handleOpenComments = async (task) => {
    setSelectedTaskForComments(task);
    try {
      const commList = await collaborationApi.getComments(activeWorkspace.id, task.id);
      setComments(commList || []);
    } catch (err) {
      console.error('Failed to load comments:', err);
    }
  };

  const handlePostComment = async (e) => {
    e.preventDefault();
    if (!newCommentText.trim() || !selectedTaskForComments || !activeWorkspace) return;
    try {
      const comm = await collaborationApi.addComment(
        activeWorkspace.id,
        selectedTaskForComments.id,
        newCommentText.trim()
      );
      setComments((prev) => [...prev, { ...comm, author: { name: user.name } }]);
      setNewCommentText('');
    } catch (err) {
      alert(`Error adding comment: ${err.message}`);
    }
  };

  // 7. Assign Task
  const handleAssignTask = async (taskId, assigneeId) => {
    if (!activeWorkspace) return;
    try {
      const updated = await collaborationApi.assignTask(activeWorkspace.id, taskId, {
        assignee_id: assigneeId ? parseInt(assigneeId, 10) : null,
      });
      setWorkspaceTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, assignee_id: updated.assignee_id } : t)));
    } catch (err) {
      alert(`Error assigning task: ${err.message}`);
    }
  };

  return (
    <div className="team-workspace-page">
      {/* Workspace Bar */}
      <div className="workspace-header-bar">
        <div className="workspace-selector-group">
          <Briefcase size={20} className="ws-icon" />
          <div className="ws-dropdown-wrapper">
            <label className="ws-label">ACTIVE WORKSPACE</label>
            <select
              className="ws-select"
              value={activeWorkspace?.id || ''}
              onChange={(e) => {
                const found = workspaces.find((w) => w.id === parseInt(e.target.value, 10));
                if (found) setActiveWorkspace(found);
              }}
            >
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
              {workspaces.length === 0 && <option value="">No Workspaces (Create one below)</option>}
            </select>
          </div>
        </div>

        <div className="workspace-header-actions">
          <button
            type="button"
            className="ws-action-btn secondary"
            onClick={() => setShowCreateWsModal(true)}
          >
            <Plus size={15} />
            <span>New Workspace</span>
          </button>
          {activeWorkspace && (
            <button
              type="button"
              className="ws-action-btn primary"
              onClick={() => setShowInviteModal(true)}
            >
              <UserPlus size={15} />
              <span>Invite Member</span>
            </button>
          )}
        </div>
      </div>

      {!activeWorkspace ? (
        <div className="empty-workspace-screen">
          <Users size={48} className="empty-ws-icon" />
          <h3>No Team Workspace Selected</h3>
          <p>Collaborate with your team, assign tasks, track shared projects, and review audit feeds.</p>
          <button
            type="button"
            className="create-first-ws-btn"
            onClick={() => setShowCreateWsModal(true)}
          >
            <Plus size={16} />
            <span>Create Your First Workspace</span>
          </button>
        </div>
      ) : (
        <>
          {/* Sub Navigation */}
          <div className="team-subnav">
            <button
              type="button"
              className={`subnav-tab ${subTab === 'tasks' ? 'active' : ''}`}
              onClick={() => setSubTab('tasks')}
            >
              <Layers size={15} />
              <span>Shared Tasks ({workspaceTasks.length})</span>
            </button>
            <button
              type="button"
              className={`subnav-tab ${subTab === 'projects' ? 'active' : ''}`}
              onClick={() => setSubTab('projects')}
            >
              <FolderPlus size={15} />
              <span>Projects ({projects.length})</span>
            </button>
            <button
              type="button"
              className={`subnav-tab ${subTab === 'activity' ? 'active' : ''}`}
              onClick={() => setSubTab('activity')}
            >
              <Activity size={15} />
              <span>Activity Feed</span>
            </button>
            <button
              type="button"
              className={`subnav-tab ${subTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setSubTab('analytics')}
            >
              <CheckCircle2 size={15} />
              <span>Team Analytics</span>
            </button>
          </div>

          {/* --- TAB 1: SHARED TASKS --- */}
          {subTab === 'tasks' && (
            <div className="team-tasks-tab">
              <div className="team-tasks-header">
                <div>
                  <h3>Team Assignments</h3>
                  <p>Shared tasks assigned across members of {activeWorkspace.name}.</p>
                </div>
              </div>

              {workspaceTasks.length === 0 ? (
                <div className="empty-team-tasks">
                  <p>No shared tasks created in this workspace yet.</p>
                </div>
              ) : (
                <div className="shared-tasks-list">
                  {workspaceTasks.map((t) => {
                    const assignedMember = members.find((m) => m.user_id === t.assignee_id);
                    return (
                      <div key={t.id} className="shared-task-card">
                        <div className="task-main-info">
                          <span className={`task-badge ${t.priority?.toLowerCase()}`}>{t.priority}</span>
                          <h4 className="shared-task-title">{t.title}</h4>
                          {t.description && <p className="shared-task-desc">{t.description}</p>}
                        </div>

                        <div className="task-collab-controls">
                          {/* Assignee Selector */}
                          <div className="assignee-picker">
                            <label>Assigned to:</label>
                            <select
                              value={t.assignee_id || ''}
                              onChange={(e) => handleAssignTask(t.id, e.target.value)}
                            >
                              <option value="">Unassigned</option>
                              {members.map((m) => (
                                <option key={m.user_id} value={m.user_id}>
                                  {m.user?.name || `Member ${m.user_id}`}
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Open comments */}
                          <button
                            type="button"
                            className="comments-bubble-btn"
                            onClick={() => handleOpenComments(t)}
                            title="Open task comments"
                          >
                            <MessageSquare size={14} />
                            <span>Discussion</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* --- TAB 2: PROJECTS --- */}
          {subTab === 'projects' && (
            <div className="team-projects-tab">
              <div className="projects-header-row">
                <div>
                  <h3>Team Projects</h3>
                  <p>Organize assignments into milestone-driven deliverables.</p>
                </div>
                <button
                  type="button"
                  className="add-project-btn"
                  onClick={() => setShowCreateProjectModal(true)}
                >
                  <Plus size={15} />
                  <span>New Project</span>
                </button>
              </div>

              <div className="projects-grid">
                {projects.map((p) => (
                  <div key={p.id} className="project-card">
                    <div className="project-card-header">
                      <span className="project-status-badge">{p.status}</span>
                      {p.deadline && <span className="project-deadline">Deadline: {p.deadline}</span>}
                    </div>
                    <h4 className="project-name">{p.name}</h4>
                    <p className="project-desc">{p.description || 'No description provided.'}</p>
                  </div>
                ))}
                {projects.length === 0 && (
                  <div className="empty-projects-notice">
                    <p>No projects created yet. Start a project to group tasks together.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* --- TAB 3: ACTIVITY FEED --- */}
          {subTab === 'activity' && (
            <div className="team-activity-tab">
              <h3>Workspace Audit Activity Feed</h3>
              <p>Audit trail of actions and updates across the team.</p>

              <div className="activity-timeline">
                {activities.map((act) => (
                  <div key={act.id} className="activity-row">
                    <div className="activity-dot" />
                    <div className="activity-content">
                      <p className="activity-desc">{act.description}</p>
                      <span className="activity-time">
                        {new Date(act.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
                {activities.length === 0 && <p className="no-activity">No recent activity recorded.</p>}
              </div>
            </div>
          )}

          {/* --- TAB 4: TEAM ANALYTICS --- */}
          {subTab === 'analytics' && (
            <div className="team-analytics-tab">
              <h3>Shared Workspace Analytics</h3>
              <div className="team-kpi-grid">
                <div className="team-kpi-card">
                  <span className="kpi-num">{teamAnalytics?.total_shared_tasks || 0}</span>
                  <span className="kpi-lbl">TOTAL SHARED TASKS</span>
                </div>
                <div className="team-kpi-card">
                  <span className="kpi-num">{teamAnalytics?.completed_tasks || 0}</span>
                  <span className="kpi-lbl">COMPLETED TASKS</span>
                </div>
                <div className="team-kpi-card">
                  <span className="kpi-num">{teamAnalytics?.members_count || members.length}</span>
                  <span className="kpi-lbl">TEAM MEMBERS</span>
                </div>
                <div className="team-kpi-card">
                  <span className="kpi-num">{teamAnalytics?.active_projects_count || projects.length}</span>
                  <span className="kpi-lbl">ACTIVE PROJECTS</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* --- MODAL: CREATE WORKSPACE --- */}
      {showCreateWsModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateWsModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>Create Shared Workspace</h3>
            <form onSubmit={handleCreateWorkspace}>
              <div className="form-field">
                <label>Workspace Name</label>
                <input
                  type="text"
                  placeholder="e.g. Core Design System"
                  value={newWsName}
                  onChange={(e) => setNewWsName(e.target.value)}
                  required
                />
              </div>
              <div className="form-field">
                <label>Description</label>
                <textarea
                  placeholder="Goals and team scope..."
                  value={newWsDesc}
                  onChange={(e) => setNewWsDesc(e.target.value)}
                />
              </div>
              <div className="modal-btn-row">
                <button type="button" onClick={() => setShowCreateWsModal(false)}>Cancel</button>
                <button type="submit" className="primary-btn">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL: INVITE MEMBER --- */}
      {showInviteModal && (
        <div className="modal-backdrop" onClick={() => setShowInviteModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>Invite Team Member</h3>
            <form onSubmit={handleInviteMember}>
              <div className="form-field">
                <label>Member Email</label>
                <input
                  type="email"
                  placeholder="colleague@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                />
              </div>
              <div className="form-field">
                <label>Role</label>
                <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
                  <option value="MEMBER">Member (Can view, create and complete tasks)</option>
                  <option value="ADMIN">Admin (Can manage projects, tasks and members)</option>
                </select>
              </div>
              <div className="modal-btn-row">
                <button type="button" onClick={() => setShowInviteModal(false)}>Cancel</button>
                <button type="submit" className="primary-btn">Send Invite</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL: CREATE PROJECT --- */}
      {showCreateProjectModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateProjectModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>Create Project</h3>
            <form onSubmit={handleCreateProject}>
              <div className="form-field">
                <label>Project Name</label>
                <input
                  type="text"
                  placeholder="e.g. Q4 Mobile Redesign"
                  value={newProjName}
                  onChange={(e) => setNewProjName(e.target.value)}
                  required
                />
              </div>
              <div className="form-field">
                <label>Description</label>
                <textarea
                  placeholder="Key milestones..."
                  value={newProjDesc}
                  onChange={(e) => setNewProjDesc(e.target.value)}
                />
              </div>
              <div className="form-field">
                <label>Target Deadline</label>
                <input
                  type="date"
                  value={newProjDeadline}
                  onChange={(e) => setNewProjDeadline(e.target.value)}
                />
              </div>
              <div className="modal-btn-row">
                <button type="button" onClick={() => setShowCreateProjectModal(false)}>Cancel</button>
                <button type="submit" className="primary-btn">Create Project</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- COMMENTS DRAWER --- */}
      {selectedTaskForComments && (
        <div className="modal-backdrop" onClick={() => setSelectedTaskForComments(null)}>
          <div className="comments-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className="drawer-badge">TASK DISCUSSION</span>
                <h4>{selectedTaskForComments.title}</h4>
              </div>
              <button
                type="button"
                className="close-drawer-btn"
                onClick={() => setSelectedTaskForComments(null)}
              >
                ✕
              </button>
            </div>

            <div className="comments-thread">
              {comments.map((c) => (
                <div key={c.id} className="comment-bubble">
                  <div className="comment-head">
                    <span className="comment-author">{c.author?.name || `Member ${c.author_id}`}</span>
                    <span className="comment-time">
                      {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="comment-text">{c.content}</p>
                </div>
              ))}
              {comments.length === 0 && (
                <p className="no-comments">No discussion on this task yet. Leave a note below.</p>
              )}
            </div>

            <form onSubmit={handlePostComment} className="comment-input-form">
              <input
                type="text"
                placeholder="Write a comment or status update..."
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
              />
              <button type="submit" disabled={!newCommentText.trim()}>
                <Send size={15} />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
