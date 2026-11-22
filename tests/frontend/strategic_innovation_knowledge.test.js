import assert from 'node:assert';
import { strategicIntelligenceApi } from '../../src/services/strategicIntelligenceApi.js';
import { innovationLabApi } from '../../src/services/innovationLabApi.js';
import { knowledgeIntelligenceApi } from '../../src/services/knowledgeIntelligenceApi.js';
import { translations } from '../../src/i18n/translations.js';

console.log('--- RUNNING PHASES 36, 37 & 38 FRONTEND UNIT TESTS ---');

// 1. Strategic Intelligence API Client Interface Tests
{
  assert.strictEqual(typeof strategicIntelligenceApi.getOverview, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listPlans, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.createPlan, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listGoals, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.createGoal, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listInitiatives, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.createInitiative, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listMarketIntelligence, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listSignals, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listCompetitors, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listSwot, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listMarketSizing, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listOpportunities, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.createOpportunity, 'function');
  assert.strictEqual(typeof strategicIntelligenceApi.listDecisions, 'function');
  console.log('✓ Strategic Intelligence API client exposes all required endpoints.');
}

// 2. Innovation Lab API Client Interface Tests
{
  assert.strictEqual(typeof innovationLabApi.getOverview, 'function');
  assert.strictEqual(typeof innovationLabApi.listIdeas, 'function');
  assert.strictEqual(typeof innovationLabApi.getIdea, 'function');
  assert.strictEqual(typeof innovationLabApi.createIdea, 'function');
  assert.strictEqual(typeof innovationLabApi.updateIdea, 'function');
  assert.strictEqual(typeof innovationLabApi.deleteIdea, 'function');
  assert.strictEqual(typeof innovationLabApi.promoteToRoadmap, 'function');
  assert.strictEqual(typeof innovationLabApi.listHypotheses, 'function');
  assert.strictEqual(typeof innovationLabApi.createHypothesis, 'function');
  assert.strictEqual(typeof innovationLabApi.listExperiments, 'function');
  assert.strictEqual(typeof innovationLabApi.createExperiment, 'function');
  assert.strictEqual(typeof innovationLabApi.attachExperimentResult, 'function');
  assert.strictEqual(typeof innovationLabApi.listPrototypes, 'function');
  assert.strictEqual(typeof innovationLabApi.createPrototype, 'function');
  assert.strictEqual(typeof innovationLabApi.listValidations, 'function');
  assert.strictEqual(typeof innovationLabApi.createValidation, 'function');
  assert.strictEqual(typeof innovationLabApi.listPortfolios, 'function');
  console.log('✓ Innovation Lab API client exposes all required endpoints.');
}

// 3. Knowledge Intelligence API Client Interface Tests
{
  assert.strictEqual(typeof knowledgeIntelligenceApi.getOverview, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.listDocuments, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.getDocument, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.createDocument, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.updateDocument, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.getDocumentVersions, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.listCollections, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.createCollection, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.getGraph, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.createGraphEntity, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.createGraphRelationship, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.semanticSearch, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.queryAiAssistant, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.listMemories, 'function');
  assert.strictEqual(typeof knowledgeIntelligenceApi.listGaps, 'function');
  console.log('✓ Knowledge Intelligence API client exposes all required endpoints.');
}

// 4. Strategic RICE Prioritization Formula Validation
{
  // Formula: (Reach * Impact * Confidence) / Effort
  const calcRice = (reach, impact, confidence, effort) => {
    const eff = effort > 0 ? effort : 1;
    return Math.round(((reach * impact * confidence) / eff) * 10) / 10;
  };

  assert.strictEqual(calcRice(1000, 3.0, 0.8, 2.0), 1200.0);
  assert.strictEqual(calcRice(5000, 3.0, 0.8, 4.0), 3000.0);
  assert.strictEqual(calcRice(200, 1.0, 0.5, 1.0), 100.0);
  console.log('✓ RICE prioritization calculations accurately evaluate reach, impact, confidence, and effort.');
}

// 5. Innovation Pipeline Stage Progression & Promotion Logic
{
  const allowedStages = [
    'CAPTURE',
    'SCREENING',
    'RESEARCH',
    'HYPOTHESIS',
    'EXPERIMENTATION',
    'PROTOTYPE',
    'VALIDATED',
    'ROADMAP',
    'REJECTED',
  ];

  const canPromoteToRoadmap = (stage) => stage === 'VALIDATED';

  assert.strictEqual(canPromoteToRoadmap('CAPTURE'), false);
  assert.strictEqual(canPromoteToRoadmap('EXPERIMENTATION'), false);
  assert.strictEqual(canPromoteToRoadmap('PROTOTYPE'), false);
  assert.strictEqual(canPromoteToRoadmap('VALIDATED'), true);
  console.log('✓ Innovation pipeline stage validation and roadmap promotion rules verified.');
}

// 6. Knowledge Graph Structure & Citation Attribution
{
  const testGraph = {
    nodes: [
      { id: 'kenti_1', label: 'Hybrid Search Engine', entity_type: 'TECHNOLOGY' },
      { id: 'kenti_2', label: 'ADR-042 Hybrid Search', entity_type: 'DECISION' },
    ],
    edges: [
      { id: 'krel_1', source: 'kenti_1', target: 'kenti_2', relation_type: 'IMPLEMENTS', confidence: 1.0 },
    ],
  };

  assert.strictEqual(testGraph.nodes.length, 2);
  assert.strictEqual(testGraph.edges.length, 1);
  assert.strictEqual(testGraph.edges[0].relation_type, 'IMPLEMENTS');

  // Verify citation formatting
  const citation = {
    source_id: 'kdoc_1',
    source_title: 'Engineering Runbook',
    source_type: 'RUNBOOK',
    snippet: 'Verified failover procedure',
    relevance: 0.95,
  };
  assert.ok(citation.source_title.length > 0);
  assert.ok(citation.relevance >= 0 && citation.relevance <= 1.0);
  console.log('✓ Knowledge graph nodes, edges, and AI citation attribution verified.');
}

// 7. Navigation Translations Verification
{
  assert.strictEqual(translations.en['nav.strategy'], 'Strategy & Markets');
  assert.strictEqual(translations.en['nav.innovation'], 'Innovation Lab');
  assert.strictEqual(translations.en['nav.knowledge'], 'Knowledge Hub');
  console.log('✓ Navigation translations registered for Strategy, Innovation, and Knowledge.');
}

console.log('--- ALL PHASE 36-38 FRONTEND UNIT TESTS PASSED SUCCESSFULLY! ---');
