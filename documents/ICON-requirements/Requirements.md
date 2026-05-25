---
title: "Requirements for Observability, Control and Intervention of Network Management Agents"
abbrev: "icon requirements"
category: info

docname: draft-XXX-icon-requirements-latest
submissiontype: IETF  # also: "independent", "editorial", "IAB", or "IRTF"
number:
date:
consensus: true
v: 3
# area: AREA
# workgroup: WG Working Group
keyword:
 - Network Management Agents
 - Observability
 - Control
 - Intervention

author:
-
   fullname: Qiufang Ma
   organization: Huawei
   role: editor
   street: 101 Software Avenue, Yuhua District
   city: Nanjing, Jiangsu
   code: 210012
   country: China
   email: maqiufang1@huawei.com
-
   fullname: Qin Wu
   organization: Huawei
   street: 101 Software Avenue, Yuhua District
   city: Nanjing, Jiangsu
   code: 210012
   country: China
   email: bill.wu@huawei.com


normative:

informative:

--- abstract

This document defines a set of requirements for ICON (Observability, Control, and Intervention for Network Management Agents).

It identifies gaps in existing mechanisms and specifies required interaction capabilities between humans (or other agent supervision systems) and network management agents across multi-vendor environments, specifically observability, control, and run-time intervention. The requirements aim to mitigate agent unreliability and hallucination issues, and to minimize the negative impacts that agents might cause to networks when they deviate from expected behaviors.


--- middle

# Introduction

AI agents are increasingly deployed for network management tasks {{?I-D.wmz-nmrg-agent-ndt-arch}} — including service provisioning and network configuration change, service assurance and automated incident diagnosis and resolution. While the introduction of agents significantly improves the efficiency for network management, it also inevitably brings challenges such as hallucination and execution unreliability.

Existing mechanisms for agent assurance typically rely on static guardrails (e.g., input/output validation, operation allowlists/blocklists, pre-action approval), while assuming that all agent failure modes can be predefined. Unlike deterministic software systems, however, LLM-based agents exhibit emergent behaviors that cannot be fully anticipated or encoded in static rules. When agentic systems produce novel actions or reasoning paths that fall outside predefined static boundaries, it might lead to risks such as unintended configuration changes, policy violations, or cascading failures in the network.

This document defines requirements for ICON — Intervention, Control, and Observability for Network Management Agents. It emphasizes essential requirements that operators need when deploying agents in real networks for agent observability, control, and intervention.

This document does not specify a particular protocol, data model, or implementation API. Those topics are orthogonal to the operational requirements defined here, which are intended to be solution-neutral.

# Conventions and Definitions

{::boilerplate bcp14-tagged}


 This document defines the following terms:

Observability:
: The visibility into an agent's internal state, decision-making logic, and workflow execution from its external telemetry outputs (e.g., logs, traces, metrics), enabling human operators or monitoring systems to understand what the agent is doing and why it behaves in a specific manner.

Control:
: Establish a deterministic operational boundary for the agent before execution. By pre-defining the agent's behavior scopes, operational constraints, and security baselines, it fundamentally mitigates abnormal behaviors from agents.

Intervention:
: A reactive, emergency action to intervene or take control of an agent with boundary violations, anomalies, failures, or risks, so as to block harmful decisions, disrupt hazards, and promptly mitigate losses.

# Existing Mechanisms for Agent Observability, Control, and Intervention

After receiving a user request, agents will perform a Chain-of-Thought (CoT) reasoning process, then it will autonomously decide whether to break down the task into subtasks, or dynamically decide to invoke multiple external tools, retrieve vector databases (RAG), or request more information from the user. Existing telemetry mechanisms are excellent for tracking traditional network infrastructure or software which are built for deterministic systems. However, they are facing severe limitations when applied to AI agents. For example, existing logging practices only record what action was taken, completely missing why it was taken, including the agent's internal reasoning provenance and confidence scores. Existing tracing mechanism designed for static and linear execution path also cannot capture the complex and dynamic execution trajectories of AI agents.

Existing AI guardrails primarily operate at static boundaries, such as input/output validation and pre-action checks. These mechanisms are designed to constrain AI agents within predefined operational and compliance boundaries, but they assume that all possible violations can be anticipated and encoded in static rules. As AI systems increasingly operate in non‑deterministic environments, these static measures are proving insufficient as they cannot detect, interrupt, and recover from unanticipated behaviours.

Although there are some modern agent systems that provide interrupt or kill switch capabilities, they remain framework-specific, insufficient, or proprietary.

These gaps motivate the requirements for agent observability, control, and intervention defined in {{requirements}}.

# Requirements {#requirements}

## Observability Requirements

OBS-1: Execution Trajectory Capture
: The framework MUST support visibility into complete agent execution trajectories, including reasoning chain/chain-of-thought, actions plans, executed steps, and observations in specific format.

OBS-2: Reasoning Provenance Capture
: The framework MUST support visibility into reasoning provenance, including intent understanding, inference, confidence scores, evidence chains. Agents should expose why a decision was made, not only what action was taken.

OBS-3: Metrics Collection
: The framework MUST support collection of metrics characterizing agent operational health, including action execution latency, error rates, token consumption, resource usage, task completion rates, and confidence calibration.

OBS-4: Multi-Agent Correlation
: The framework MUST support logging and trace correlation across distributed multiple agent execution, supporting querying and analysis.

## Control Requirements

CTL-1: Access and Permission Control
: The framework MUST provide mechanisms to define and enforce what systems, skills, tools, and data fields an agent is permitted to access and operate.

CTL-2: Authorization and Approval Controls (Escalation)
: The framework MUST support the designation of certain actions or decisions as requiring explicit human approval before execution.

CTL-3: Temporal and Data/Context Validity
: The framework MUST ensure the agent is acting on current, accurate context.

CTL-4: Trust and Integrity Protection
: The framework MUST protect the agent from adversarial manipulation, including integrity checks for agent decisions, provenance verification for tool outputs, and resistance against prompt injection or other adversarial inputs.

CTL-5: Alignment and Calibration Control
: The framework MUST ensure the agent optimize for what the operator actually intends. Detect and correct divergence between the agent's measured objective, its world model, and the operational reality.

## Intervention Requirements

INT-1: Execution Interruption
: The operator MUST be able to stop or redirect a running agent. Emergency response from a temporary pause that preserves state (e.g., when operators needs time to assess before deciding further action) to a hard stop that terminates execution (e.g., when agent is actively causing damage) regardless of task progress.

INT-2: Containment
: The operator MUST be able to limit the extent of a failure (impact scope). Stop further harm from accumulating without necessarily reversing what has already occurred.

INT-3: Rollback and Recovery
: The operator MUST be able to reverse actions already taken by an agent. Can be a single transaction or a coordinated cross-system reversal of an entire multi-agent workflow.

INT-4: Escalation
: The operator MUST be able to route decisions, alerts, and conflicts to a higher authority. Used when the current level cannot (or should not) resolve the situation without supervision.

INT-5: Correction
: The operator MUST be able to correct failures by modifying an agent's pending action, planned sequence, or internal state before execution proceeds.

INT-6: Auditability and Accountability
: The framework MUST support attribution of failures to responsible entities (e.g., agents, humans, or systems), quantification of consequences (e.g., resource impact, downtime, cost), and traceability from failure through intervention to recovery.
This post-failure capability MUST enable accountability and quantify operational impact.

# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.

--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
