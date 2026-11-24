/**
 * Frontend Unit & Workflow Tests for Module B52: Service Desk & SLA Management.
 */

import assert from 'assert';
import { serviceDeskApi } from '../../src/services/serviceDeskApi.js';

console.log('--- RUNNING MODULE B52: SERVICE DESK & SLA MANAGEMENT FRONTEND TESTS ---');

// 1. Verify API Service Exposure
assert(typeof serviceDeskApi.getTickets === 'function', 'serviceDeskApi must expose getTickets');
assert(typeof serviceDeskApi.getTicketDetail === 'function', 'serviceDeskApi must expose getTicketDetail');
assert(typeof serviceDeskApi.createTicket === 'function', 'serviceDeskApi must expose createTicket');
assert(typeof serviceDeskApi.assignTicket === 'function', 'serviceDeskApi must expose assignTicket');
assert(typeof serviceDeskApi.updateTicketStatus === 'function', 'serviceDeskApi must expose updateTicketStatus');
assert(typeof serviceDeskApi.escalateTicket === 'function', 'serviceDeskApi must expose escalateTicket');
assert(typeof serviceDeskApi.getTicketComments === 'function', 'serviceDeskApi must expose getTicketComments');
assert(typeof serviceDeskApi.addTicketComment === 'function', 'serviceDeskApi must expose addTicketComment');
assert(typeof serviceDeskApi.getCategories === 'function', 'serviceDeskApi must expose getCategories');
assert(typeof serviceDeskApi.createCategory === 'function', 'serviceDeskApi must expose createCategory');
assert(typeof serviceDeskApi.getSLAPolicies === 'function', 'serviceDeskApi must expose getSLAPolicies');
assert(typeof serviceDeskApi.createSLAPolicy === 'function', 'serviceDeskApi must expose createSLAPolicy');
assert(typeof serviceDeskApi.getEscalationRules === 'function', 'serviceDeskApi must expose getEscalationRules');
assert(typeof serviceDeskApi.createEscalationRule === 'function', 'serviceDeskApi must expose createEscalationRule');
assert(typeof serviceDeskApi.recalculateSLAs === 'function', 'serviceDeskApi must expose recalculateSLAs');
assert(typeof serviceDeskApi.getDashboard === 'function', 'serviceDeskApi must expose getDashboard');
assert(typeof serviceDeskApi.getPerformanceReports === 'function', 'serviceDeskApi must expose getPerformanceReports');
console.log('✓ serviceDeskApi exposes all 17 required B52 client endpoints.');

// 2. Business Hours SLA Calendar Calculator
function calculateSLATarget(startTime, targetMinutes, businessHoursStart = "09:00", businessHoursEnd = "17:00", workDays = ["MON", "TUE", "WED", "THU", "FRI"]) {
  const [startH, startM] = businessHoursStart.split(':').map(Number);
  const [endH, endM] = businessHoursEnd.split(':').map(Number);

  const dayNames = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  let current = new Date(startTime.getTime());
  let remaining = targetMinutes;

  while (remaining > 0) {
    const dayName = dayNames[current.getUTCDay()];
    if (!workDays.includes(dayName)) {
      current.setUTCDate(current.getUTCDate() + 1);
      current.setUTCHours(startH, startM, 0, 0);
      continue;
    }

    const currentMinutes = current.getUTCHours() * 60 + current.getUTCMinutes();
    const dayStartMinutes = startH * 60 + startM;
    const dayEndMinutes = endH * 60 + endM;

    if (currentMinutes < dayStartMinutes) {
      current.setUTCHours(startH, startM, 0, 0);
      continue;
    }

    if (currentMinutes >= dayEndMinutes) {
      current.setUTCDate(current.getUTCDate() + 1);
      current.setUTCHours(startH, startM, 0, 0);
      continue;
    }

    const availableToday = dayEndMinutes - currentMinutes;
    if (remaining <= availableToday) {
      current = new Date(current.getTime() + remaining * 60 * 1000);
      remaining = 0;
    } else {
      remaining -= availableToday;
      current.setUTCDate(current.getUTCDate() + 1);
      current.setUTCHours(startH, startM, 0, 0);
    }
  }

  return current;
}

// Test SLA calculation: Started Monday at 10:00 AM with 120 minutes target -> Monday 12:00 PM
const monday10am = new Date('2026-11-23T10:00:00Z');
const dueMonday = calculateSLATarget(monday10am, 120);
assert.strictEqual(dueMonday.getUTCHours(), 12, '120 min from Monday 10:00 must be 12:00');

// Test SLA calculation across end of day: Monday 16:00 (4:00 PM) with 120 minutes target -> Tuesday 10:00 AM
const monday4pm = new Date('2026-11-23T16:00:00Z');
const dueTuesday = calculateSLATarget(monday4pm, 120);
assert.strictEqual(dueTuesday.getUTCDate(), 24, 'Must roll over to Tuesday');
assert.strictEqual(dueTuesday.getUTCHours(), 10, 'Must be 10:00 AM Tuesday (1h Mon + 1h Tue)');
console.log('✓ Business hours SLA target calculator correctly computes multi-day deadlines.');

// 3. Status Workflow State Machine Transition Validation
const ALLOWED_TRANSITIONS = {
  NEW: ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'CANCELLED'],
  OPEN: ['ASSIGNED', 'IN_PROGRESS', 'WAITING_FOR_REQUESTER', 'WAITING_FOR_THIRD_PARTY', 'RESOLVED', 'CANCELLED'],
  ASSIGNED: ['IN_PROGRESS', 'WAITING_FOR_REQUESTER', 'WAITING_FOR_THIRD_PARTY', 'ESCALATED', 'RESOLVED', 'CANCELLED'],
  IN_PROGRESS: ['WAITING_FOR_REQUESTER', 'WAITING_FOR_THIRD_PARTY', 'ESCALATED', 'RESOLVED', 'CANCELLED'],
  WAITING_FOR_REQUESTER: ['IN_PROGRESS', 'OPEN', 'RESOLVED', 'CANCELLED'],
  WAITING_FOR_THIRD_PARTY: ['IN_PROGRESS', 'OPEN', 'RESOLVED', 'CANCELLED'],
  ESCALATED: ['IN_PROGRESS', 'ASSIGNED', 'RESOLVED', 'CANCELLED'],
  RESOLVED: ['CLOSED', 'REOPENED'],
  CLOSED: ['REOPENED'],
  REOPENED: ['ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CANCELLED'],
  CANCELLED: ['REOPENED'],
};

function isValidTransition(fromStatus, toStatus) {
  if (fromStatus === toStatus) return true;
  return Boolean(ALLOWED_TRANSITIONS[fromStatus]?.includes(toStatus));
}

assert(isValidTransition('NEW', 'OPEN'), 'NEW -> OPEN must be valid');
assert(isValidTransition('NEW', 'ASSIGNED'), 'NEW -> ASSIGNED must be valid');
assert(isValidTransition('IN_PROGRESS', 'WAITING_FOR_REQUESTER'), 'IN_PROGRESS -> WAITING_FOR_REQUESTER must be valid');
assert(isValidTransition('RESOLVED', 'CLOSED'), 'RESOLVED -> CLOSED must be valid');
assert(isValidTransition('RESOLVED', 'REOPENED'), 'RESOLVED -> REOPENED must be valid');
assert(!isValidTransition('NEW', 'CLOSED'), 'NEW -> CLOSED must be invalid directly');
assert(!isValidTransition('WAITING_FOR_REQUESTER', 'CLOSED'), 'WAITING_FOR_REQUESTER -> CLOSED must be invalid directly');
console.log('✓ Ticket status transition state machine strictly enforces governance rules.');

// 4. SLA Pause & Resume Logic
function applyStatusTransition(ticket, newStatus, timestamp = new Date()) {
  const prevStatus = ticket.status;
  if (!isValidTransition(prevStatus, newStatus)) {
    throw new Error(`Invalid transition from ${prevStatus} to ${newStatus}`);
  }

  ticket.status = newStatus;

  // Entering pause state
  if (newStatus === 'WAITING_FOR_REQUESTER' && !ticket.is_sla_paused) {
    ticket.is_sla_paused = true;
    ticket.sla_paused_at = timestamp;
  }
  // Exiting pause state
  else if (prevStatus === 'WAITING_FOR_REQUESTER' && newStatus !== 'WAITING_FOR_REQUESTER') {
    if (ticket.sla_paused_at) {
      const pausedMs = timestamp.getTime() - ticket.sla_paused_at.getTime();
      ticket.total_paused_minutes += Math.round(pausedMs / (60 * 1000));
      // Extend due dates
      if (ticket.first_response_due_at) {
        ticket.first_response_due_at = new Date(ticket.first_response_due_at.getTime() + pausedMs);
      }
      if (ticket.resolution_due_at) {
        ticket.resolution_due_at = new Date(ticket.resolution_due_at.getTime() + pausedMs);
      }
    }
    ticket.is_sla_paused = false;
    ticket.sla_paused_at = null;
  }

  return ticket;
}

const testTicket = {
  id: 101,
  status: 'IN_PROGRESS',
  is_sla_paused: false,
  sla_paused_at: null,
  total_paused_minutes: 0,
  first_response_due_at: new Date('2026-11-24T14:00:00Z'),
  resolution_due_at: new Date('2026-11-24T18:00:00Z'),
};

const pauseTime = new Date('2026-11-24T11:00:00Z');
applyStatusTransition(testTicket, 'WAITING_FOR_REQUESTER', pauseTime);
assert.strictEqual(testTicket.is_sla_paused, true, 'Ticket must be paused');

const resumeTime = new Date('2026-11-24T12:30:00Z'); // 90 min later
applyStatusTransition(testTicket, 'IN_PROGRESS', resumeTime);
assert.strictEqual(testTicket.is_sla_paused, false, 'Ticket must be resumed');
assert.strictEqual(testTicket.total_paused_minutes, 90, 'Paused minutes must equal 90');
assert.strictEqual(testTicket.resolution_due_at.toISOString(), '2026-11-24T19:30:00.000Z', 'Resolution deadline must be pushed forward by 90 minutes');
console.log('✓ SLA pause and deadline extension mechanics operate deterministically.');

// 5. Internal Note Privacy and Confidentiality Filter
function filterCommentsForUser(comments, currentUser, ticketRequesterId) {
  const isAgentOrAdmin = ['ADMIN', 'OWNER', 'SUPPORT_AGENT'].includes(currentUser.role);
  if (isAgentOrAdmin) return comments;
  return comments.filter(c => !c.is_internal_note);
}

const mockComments = [
  { id: 1, author_id: 10, content: 'Can you provide logs?', is_internal_note: false },
  { id: 2, author_id: 20, content: 'Database cluster is restarting, do not tell requester yet', is_internal_note: true },
  { id: 3, author_id: 10, content: 'Logs attached.', is_internal_note: false },
];

const customerUser = { id: 5, role: 'MEMBER' };
const agentUser = { id: 20, role: 'SUPPORT_AGENT' };

const customerView = filterCommentsForUser(mockComments, customerUser, 5);
assert.strictEqual(customerView.length, 2, 'Customer must only see public messages');
assert(!customerView.some(c => c.is_internal_note), 'Customer must never see internal notes');

const agentView = filterCommentsForUser(mockComments, agentUser, 5);
assert.strictEqual(agentView.length, 3, 'Agent must see all notes including confidential notes');
console.log('✓ Internal note confidentiality filter prevents exposure of internal records.');

// 6. SLA Breach & Risk Evaluation
function evaluateSLARisk(dueAt, completedAt, now = new Date(), atRiskRatio = 0.75, created = new Date(dueAt.getTime() - 4 * 3600 * 1000)) {
  if (completedAt) {
    return completedAt <= dueAt ? 'COMPLIED' : 'BREACHED';
  }
  if (now > dueAt) {
    return 'BREACHED';
  }
  const totalWindow = dueAt.getTime() - created.getTime();
  const elapsed = now.getTime() - created.getTime();
  if (totalWindow > 0 && elapsed / totalWindow >= atRiskRatio) {
    return 'AT_RISK';
  }
  return 'OK';
}

const createdAt = new Date('2026-11-24T08:00:00Z');
const dueAt = new Date('2026-11-24T12:00:00Z'); // 4h window
const earlyNow = new Date('2026-11-24T09:00:00Z'); // 25% elapsed
assert.strictEqual(evaluateSLARisk(dueAt, null, earlyNow, 0.75, createdAt), 'OK');

const lateNow = new Date('2026-11-24T11:30:00Z'); // 87.5% elapsed
assert.strictEqual(evaluateSLARisk(dueAt, null, lateNow, 0.75, createdAt), 'AT_RISK');

const breachedNow = new Date('2026-11-24T12:01:00Z'); // past due
assert.strictEqual(evaluateSLARisk(dueAt, null, breachedNow, 0.75, createdAt), 'BREACHED');
console.log('✓ SLA Risk and Breach detection evaluator correctly identifies OK, AT_RISK and BREACHED.');

console.log('ALL MODULE B52 SERVICE DESK & SLA MANAGEMENT FRONTEND TESTS PASSED SUCCESSFULLY!');
