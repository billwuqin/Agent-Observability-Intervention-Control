---
title: "Problem Statement for Observability, Intervention and Control (I&C) in Multi-Agent Autonomous Networks"
abbrev: "Observability and I&C"
category: info

docname: draft-nair-icon-problem-statement-latest
submissiontype: IETF
number:
date:
consensus: true
v: 3
# area: AREA
# workgroup: WG Working Group
keyword:
 - next generation
 - unicorn
 - sparkling distributed ledger
venue:
#  group: WG
#  type: Working Group
#  mail: WG@example.com
#  arch: https://example.com/WG
  github: "billwuqin/ICON-problem-statement"
  latest: "https://billwuqin.github.io/ICON-problem-statement/draft-nair-icon-problem-statement.html"

author:
 -
    fullname: Qin Wu
    organization: Huawei
    email: bill.wu@huawei.com

normative:

informative:

  MCP:
    title: Model Context Protocol
    target: https://modelcontextprotocol.io/
    date: November 2024

  A2A:
    title: Agent2Agent (A2A) protocol
    target: https://google-a2a.github.io/A2A/#/documentation?id=agent2agent-protocol-a2a
    date: April 2025

--- abstract

This document provides an overview of the issues associated with the
deployment of the observability, intervention, and control of autonomous
agent pipelines in large-scale heterogeneous network environments.  The
term "Intervention and Control" is used to describe a set of automated and
human-initiated mechanisms that guarantee the capability to observe, constrain,
correct, and terminate AI agents at any point, for any reason, irrespective of
their level of autonomy under which it operates, to ensure resilience, recovery,
and operational continuity.

The set of enabled observability, intervention and control reflects operator
service offerings to ensure that autonomous operations can be stopped, or safely
redirected when required and is designed in conjunction with agent to agent, agent
to tools, agent to human interaction and service and network policy.

This document also identifies several key areas that the Agent Observability,
Intervention and Control group will investigate to guide its
architectural and protocol work and associated documents.

--- middle

# Introduction

Network operations are increasingly autonomous with the growth of network
management Agent applications at the network level and service level. Since
AI native operations may be non-deterministic, when network management agents
misbehave or deviate from what Agents are expected to do, Current AI safety
technologies, often referred to as "AI guardrails" are introduced to constrain
the behavior of AI agents within operational and compliance boundaries, prevent
AI from producing harmful results or taking wrong actions, e.g.,escalate a decision
to a human for a high-risk network operation, defend against malicious attacks,
e.g., prompt injection. These guardrails typically operate at the input/output/pre-action
filter level or through static boundary alignment.

However as AI systems are increasingly integrated into autonomous workflows and
critical infrastructure, these static measures are proving insufficient for the
full operational lifecycle, they often cannot detect, interrupt, and rollover from
unanticipated behaviors. Network operators usually lack an equivalent infrastructure
for human oversight or to provide continuous, monitoring of an AI system’s internal
logic or its long-running execution paths that match the speed and scale of the network
management Agent applications, e.g., network failure or security risk is hard to detect
and control, occurring at machine speed. When a violation is suspected, there are currently
no standardized protocols for intervention (e.g., immediate task suspension) and recovery
(e.g., reverting to a last known safe state or undoing a series of autonomous actions that
introduce substantial operational risk) mechanisms. In non-deterministic environments, the
lack of human oversight and human-AI semantic intent exchange hinder timely risk mitigation
and state recovery during boundary violations by agents.

This document provides a problem statement for protocol on agent observability, intervation and control.
We list the properties the protocol should have, then explain why those properties are necessary.  We describe why a
new protocol is the best solution for the more general problem of identifying and characterizing trajectory records
related to agent behavior or workflow operation, continuous monitoring and evaluation, enable human oversight, provide
human and agent interaction for agent intervention and control at the service level and network level.

Where possible, any solutions work will be built in a modular way using existing IETF protocols.
However, no protocol solution choices will be made until the functional requirements have been
agreed, and then this will require an analysis of the capabilities of existing protocols and
identify gaps that need to be filled.

# Conventions and Definitions

{::boilerplate bcp14-tagged}

 The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
 "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
 "OPTIONAL" in this document are to be interpreted as described in
 BCP 14 {{!RFC2119}} {{!RFC8174}} when, and only when, they appear in all
 capitals, as shown here.

-  Autonomous Agent: An AI-driven software entity capable of accepting
    a declarative goal and executing non-deterministic tasks.

-  Agent Drift: Gradual performance degradation or misalignment of
    reasoning patterns over time in a production environment.

-  Cascading Failure: A scenario where a failure in one downstream
    sub-agent propagates across multi-agent boundaries.

- Human to Agent Communication: The interaction between human users and network management Agent designed to perform tasks, solve problems,
                                 or provide information. Unlike standard human-to-machine interaction where a human drives every step of a
                                 task, human-agent communication involves delegation, where the human provides a goal and the agent
                                 autonomously figures out how to achieve it.

- Observability: Enabling network behavioral assessment through analysis of observed operational network data (logs, metrics, traces, etc.)
                with the aim of detecting symptoms of network behavior, and to identify anomalies and their causes.

- Intervention: Operates when something has gone wrong, is going wrong, or is about to go wrong that provides humans with the
                ability to detect, interrupt, correct, and recover from agent behavior that is not anticipated by control mechanism.

- Control: Operates before and during agent action execution defining what an agent is permitted to do, enforcing boundaries,
           and structuring the environment so that harmful or unauthorized actions are difficult or impossible to execute.

- Evaluation:Using Trajectory record to assess the performance and understand how an gent solves problem,e.g.,Checking if the agent took
             the shortest sequence of actions or wasted resources on redundant tool or Analyzing specific segments of the trajectory to
             see if the agent excels at information retrieval but struggles with mathematical synthesis.

- Human Oversight: The practice of keeping humans actively involved in continuously monitoring of AI agents.In agent trajectory management,
                   it ensures that network management agents do not go off the rails, violate safety protocols, or waste resources. It transforms
                   a fully autonomous "black box" into a controllable and collaborative system.

- Behavior: pattern of reasoning, decisions, and actions an AI agent takes to achieve a specific goal such as reasoning sequence, the sequence
            and logic of execution paths.

- Trajectory record: Keep track of Agent behaviour and produce audit log or trace information to Capture the entire "flight path" or reasoning
                     sequence the agent followed to reach its conclusion using using a structured Thought,Action,Observation loop.


# Problem Space

The deployment of autonomous agentic systems within Communications
Service Provider (CSP) networks introduces fundamental operational,
architectural, and governance challenges. Current network management
paradigms are built on deterministic models that assume predictable,
rule-based behaviors. The shift toward non-deterministic, AI-native
architectures creates a structural mismatch between machine-speed execution and human-speed oversight.
This gap manifests in several distinct problem areas:

## Inadequacy of Deterministic Constraints

Agent behavior cannot be reliably constrained using predefined,
deterministic rules or traditional static guardrails. Because agents
rely on dynamic reasoning patterns to achieve declarative goals, their
exact execution trajectories remain non-deterministic. This intrinsic
variability makes operational outcomes significantly less predictable
during runtime execution, bypassing legacy input/output filters that
fail to account for real-time contextual adaptation.

## Limited Transparency in Planning and Decision-Making

As agents increasingly execute complex operational tasks, they
frequently delegate critical planning paths and execution decisions to
Large Language Models (LLMs) or specialized downstream AI models. This
delegation creates an optimization barrier, offering limited
transparency into how specific decisions are reached or how complex
action sequences are generated. Without an out-of-band mechanism to
inspect this reasoning layer, operators cannot validate the safety or
intent of an agent's planned mutations before they hit the infrastructure.

## Velocity Mismatch and Observation Deficit

Agents are explicitly designed to operate with high degrees of autonomy,
speed, and scale. However, CSPs currently lack the corresponding telemetry
and control infrastructure required to observe, evaluate, and intercept
these systems at the same machine-speed pace. Consequently, effective
real-time oversight becomes functionally impossible. Relying on human
escalation paradigms is impractical due to the sheer volume and velocity
of the data points involved in active agent pipelines.

## Maturity Asymmetry in Governance Enablers

A distinct functional asymmetry has emerged between operational
capabilities and governance mechanisms. Core features such as multi-agent
execution, advanced interoperability frameworks (e.g., Agent-to-Agent
{{A2A}} and Model Context Protocol {{MCP}}), and long-running autonomous actions
are advancing rapidly. Conversely, essential governance enablers—including
runtime intervention controls, deterministic transaction rollback, and
cross-agent lineage traceability—remain highly immature and lack clear
standardisation paths.

## Fragmentation Across Heterogeneous Integration Layers

Agentic systems operating across mixed Operational Support Systems (OSS)
and Network Management domains must interact with a highly
heterogeneous mix of legacy systems, modern APIs, and third-party
platforms. Establishing consistent, bounded governance across these
disparate integration layers is exceptionally complex. Agents routinely
invoke actions or retrieve sensitive network data through emerging pathways
(e.g., MCP endpoints) that were originally engineered for standard software
clients and never designed to handle AI-driven, autonomous agency.

## Obsolescence of Identity and Authorization Models

Existing trust and authorization models have failed to evolve in step with
dynamic agentic architectures. Traditional Identity and Access Management
(IAM) frameworks were designed exclusively for human operators or static,
deterministic software processes. These frameworks cannot securely govern
emerging dynamic agent personas—which are frequently defined on the fly through
custom skills—nor can they safely manage downstream sub-agent permission
delegation or context-dependent privilege escalation.

## Ambiguity of Lineage and Accountability Attribution

In distributed multi-agent topologies, operational responsibility for an
ultimate network outcome is scattered across an extended chain of
coordinating agents, foundational models, and abstraction layers. When
system failures, performance degradations, or unintended consequences occur,
attributing accountability to a specific agent entity, localized model decision,
or human-in-the-loop anchor becomes highly ambiguous. This lack of clear
lineage creates severe complications for post-incident root-cause analysis
and regulatory compliance reporting.

## Externalization of Governance Chains

As CSPs begin sourcing agentic capabilities from diverse third-party
vendors, independent software providers, and hyperscalers, operational
accountability becomes externalized in ways that are difficult to technically
or contractually enforce. A typical production agent implementation features
highly fragmented dependency chains spanning completely separate vendor
ecosystems, including LLM/AI model providers, infrastructure hosts, core
agent frameworks, tool/API repositories, and interconnection fabrics.

## Emergence of Novel Failure Modes

Agentic systems introduce an entirely new class of complex, systemic failure
modes that legacy operational risk frameworks are blind to detect or contain.
These include multi-agent alignment failures, where the isolated actions of
individual sub-agents appear structurally correct and compliant with their
local plans, yet collectively combine to produce a catastrophic network state.
Additionally, systems suffer from agent drift, where an agent's reasoning pattern
and behavioral outputs shift unpredictably over time as it continuously adapts
to an evolving network context.

# Solution Space for Network Management Agent Observability, Intervention and Control

## Guardrails

These are most mature, and most operationally familiar AI governance mechanism in production today. Guardrail
approaches currently realized in the industry operate at defined transition points in the agent pipeline, primarily
prompt filtering at the LLM input boundary, response validation at the LLM output boundary, and access control
restrictions on tool invocation. Currently, Guardrails are realized through 4 different mechanisms.

- Rule based filters: apply pattern matching, keyword blocking, regular expressions, and deterministic logic to
  prompts, context retrieval and completions.
- LLM based safety classifiers: use a secondary language model to evaluate the primary model's output for safety
  policy compliance before it is returned.
- Agent framework based guardrail libraries: provide structured policy specification languages (e.g. NeMo Guardrails)
  that allow developers to express governance rules in a higher-level format, with the framework handling enforcement
  logic.
- Prompt engineering constraints: shape model behaviour by instruction rather than by interception.

## Agent Drift Detection

Agent drift refers to the gradual degradation in an agent’s performance and alignment with intended behavior over time
in production environments. It exists in many forms depending on the aspect of the system affected. For example, goal
drift occurs when the quality of goal execution deviates from expectations, context drift when the relevance or
accuracy of the working context deteriorates; reasoning drift when there is a decline in the agent’s planning and
decision-making capability, and collaboration drift when the effectiveness of interactions with tools, external APIs,
or other agents degrades.

Agent drift is a well-recognized problem in academic research and agent frameworks. However, there is no universally
applicable governance or control mechanism that addresses all scenarios in practice. A key reason for this is the
strong dependence on domain-specific expertise and observability mechanisms to detect, diagnose, and mitigate drift
effectively. Many of these also may require fine-tuning the base model with revised data sets. So a runtime control of
drift needs to be addressed in a case-by-case basis. Some of the practices followed for addressing the Agent drift are
as follows

- Goal drift is observed by statistical evaluation of production tasks against the evaluation tasks. The mitigation
  may involve fine-tuning the model with revised task lists and associated agent performance.

- Context drift is detected by monitoring the retrieved context, retrieval parameters/metrics and mitigated through
  context refresh, context window management and memory management.

- Reasoning drift is detected through metrics such as relevance, success rate, tool selection/usage, LLM-as-a-judge
  and it is mitigated through fine-tuning of models, optimizing the prompts/prompt engineering

- Collaboration drift is typically detected through interaction success rates across agent interactions and mitigated
  by fixing the issues with tool/API/agent interactions.

## Quality Gates

Quality gates are checkpoints that evaluate whether an operation should proceed or not, or should be conditionally
allowed. Unlike guardrails which enforce policy constraints at defined boundaries of Agent implementation, quality
gates assess whether the work product of one stage meets a defined quality standard before permitting progression to
the next.  The concept is borrowed from DevOps practice i.e. quality gates in CI/CD pipelines that prevent code from
advancing through build, test, and deployment stages unless it meets defined quality criteria. While guardrails govern
crossing points i.e. what enters and exits defined zones, quality gates govern progression points - whether work of
sufficient quality advances to the next stage. Quality gates are the ideal mechanism to involve humans for agent tasks
execution quality and escalations - i.e. at stage transitions where the accumulated work product of a whole reasoning
stage is ready for assessment where the human is presented with a complete plan, a complete risk assessment, and a
specific decision to make.

Currently none of the available agent frameworks have a named capability called quality gate. However, some of the
existing functionality can be leveraged for realizing this. For example LangGraph has concept of conditional edges that
enable dynamic, non-linear workflows which allows routing execution to different nodes based on a state-evaluating
function or if-else statements. Similarly, Google ADK (Agent Development Kit) provides callback that can be invoked
before or after tool use and implement quality gate logic. So most of the techniques that exist today are agent
framework specific.

## Intervention Approaches

The intervention mechanisms that exist today in agentic systems are mostly implementation-specific, tied to individual
frameworks, and not mature enough to form a consistent or deployable operational practice. Currently, the mechanisms
involve the following:

- Primitive and manually controlled repurposed from the infrastructure: Reuse approaches from the infrastructure
  control such as process termination, API key revocation, service account suspension, and network-level blocking -
  which are not primarily designed for agentic systems. While they can be effective, operations like terminating an
  agent process preserves no state, enables no graceful recovery, produces no trace, and cannot be applied selectively
  to a specific action class or task scope.

- Framework specific intervention mechanisms: These are intervention mechanisms provided by specific agent frameworks.
  For example LangGraph provides an option to pause and resume the execution (pause , seek guidance from human, get
  response and then proceed). While this is primarily a Human-in-the-loop mechanism, it can be used as a workaround for
  interventions. But such mechanisms are implemented in code and not accessible externally through interfaces outside
  the agent framework. Crew AI framework provides mechanism to conditionally execute task or allows defining maximum
  iterations for task execution which prevents from getting into infinite loops. The kill-switch functionality (halt or
  restrict an agent’s execution when predefined risk, policy, or trust conditions are violated) is supported in the
  Microsoft Agent Governance Toolkit, but its interoperability across different agent frameworks is not proven.

## Security I&C Approaches

Whether security control (specifically control mechanisms, not broader security governance) should fall within the
scope of I&C requires further discussion.

Current industry approaches to agent security primarily focus on protecting the agent from malicious interference to
ensure that the inputs it receives and processes are not tampered with and manipulated. I&C is concerned with governing
what the agent does, i.e. its actions within the operational environment. This includes ensuring that actions remain
within authorized boundaries, are observable, and can be corrected or reversed when necessary.

It is believed that the security and I&C should be treated as distinct disciplines, with separate tooling and
governance responsibilities, but closely coordinated. Security acts as the first line of defense, preserving the
integrity of the agent’s inputs and reasoning. I&C serves as the operational control layer, governing agent behaviour
regardless of whether decisions are valid or compromised. Another way to view this is: when an agent's security is
compromised, it is the responsibility of the security layer to prevent or detect this. However, if the security layer
is bypassed (when adversarial techniques evolve) and if agent still proceeds to action execution, I&C functions as the
governance backstop, that intervenes to constrain or correct the agent’s actions. I&C ensures that there is a minimum
level of control is in place to control agent behavior when such security issues emerge and bypassed.

From an I&C perspective, a prominent way to manage agent security risk is to sandbox the agent’s execution environment.
This means running the agent in a restricted environment so it cannot cross trust boundaries, even if it is
compromised. Dynamically limiting the execution boundary can be achieved by adjusting the agent’s runtime environment,
permissions, and accessible resources in real time based on task context and trust level. In addition, several
guardrail-based techniques are applied, such as sanitizing inputs before they enter the agent’s context, verifying the
source of retrieved data, using intent classifiers to detect hidden or malicious instructions in non-instructional
inputs.

## Trust I&C Approaches

TR270 defines Trust as "An assessment by an agent in a trustor role that another agent in a trustee role can satisfy a
request to perform an action or provide information with acceptable expected outcomes and risk". Trust in autonomous
agents spans multiple dimensions, including identity (who the agent is), authorization (what it is allowed to do),
control(how its actions are governed during execution), behavior (whether it acts in alignment with expected goals
and produces correct outcomes), and context (under what conditions it operates). There are also different scope of
trust under discussion across industry including
- Trust at the individual agent and multi-agent execution and operational behavior, focusing on execution reliability,
  explainability, and accountability
- Trust in the wider ecosystem where the agent is procured and operated, including the LLM, vendor or infrastructure
  from where it is sourced, tools it access, agent framework used for develpment, runtime environment/harness sanity,
  and governance/certification mechanisms.
- Across agent ecosystem where trust is established between different organizations/platforms through trust domains and
  trust federation across them.

Trust I&C is considered as a set of mechanisms that enable the establishment, enforcement, and continuous adaptation of
trust governance for autonomous agents. These mechanisms address both pre-execution controls (defining what an agent is
allowed to do) and in-execution adaptations (adjusting trust based on context and observed behavior).

Traditional IAM frameworks, designed for human users and deterministic software processes, are insufficient to model the
dynamic trust governance aspects of  autonomous agents. The emerging Trust I&C approaches extend beyond static identity
and permission models to incorporate context-awareness, temporal constraints, and behavior-driven trust evaluation. Since
this is a cross cutting concen with Security, it requires broader discussion on whether Trust governance and control should
be driven by an Agent Governance Control Plane or a separate Security governance plane.

Some of the approaches followed for controlling the agent trust are given below:

- Agent privilege control: The most widely deployed current approach to agent trust governance is the application of static
  least-privilege principles -  granting agents the minimum tool access, API permissions, and system scope required for their
  designated tasks, expressed through standard IAM constructs (service accounts, API keys, OAuth scopes). Its limitation in
  agent-based systems is that tasks are dynamic. Permissions set for a typical task may be too limited for edge cases, pushing
  systems to grant broader access than necessary. On the other hand, permissions designed for complex tasks may be too broad for
  simpler ones. Also, static permissions cannot adapt to changing task needs.

- Scoped and time-limited credentials: Agents often use API keys or service accounts with broad, long-lasting permissions (for
  tool calls, RAG or model access), which can create trust & security risks. Current best practices is to use short-lived,
  limited-access credentials, such as OAuth tokens with narrow scopes or JWTs with short expiry so that agents only have the
  minimum access needed for a specific task and only for a limited time.

- Context aware trust assignment: Instead of static roles or scopes, access decisions are made dynamically using attributes and
  runtime context such as task type, data sensitivity, user intent, environment state, or risk level. For e.g. agent is allowed
  to access certain tools/data only within/belonging to a compliant geography, where it is legally allowed to access such data.

- Dynamic trust level assignment: This is one of the advanced and emerging mechanism (e.g. Microsoft Agent Governance Toolkit)
  where instead of labeling agents as just trusted or untrusted, this model gives each agent a trust score that changes over time.
  The score increases when the agent follows policies and drops quickly when it violates them. This score then decides what level
  of access the agent gets, adjusting its permissions based on how trustworthy it is at that moment.

The first two approaches rely on a well-defined agent identity to assign and enforce permissions. The fourth approach focus more on
the behavior of agent, i.e. it requires not just identity, but also continuous behavior-based evaluation, where access is determined
by how the agent performs over time - i.e based on trust score, agent is mapped to a trust zone or trust level that determines the
authority and access assigned to agent. The definition and management of agent identity are beyond the scope of this document.

### Trust Delegation Across Agents

Trust delegation between agents has a governance challenge that is distinct from single agent trust models. When an orchestrating
agent delegates a task to a sub-agent, it is not passing work alone. It is extending a scope of authority to an entity that will
take real operational actions on behalf of the orchestrating or parent agent. In this scenario how much trust, and how much permission,
should transfer through that delegation is still an area that traditional IAM has evolved to address well.  Traditional delegation
models assume a human delegating to another human or to a deterministic software process. The delegating party has a fixed identity,
the receiving party has a fixed role, and the scope of delegation is defined at design time. The delegating agent may itself be
operating under dynamically adjusted trust constraints. The receiving agent may be a different implementation, framework, or vendor.
The scope of work being delegated may not have been anticipated when permissions were originally configured.  The techniques used
in trust delegation follows similar patterns as in single agent scenario.

- Flat delegation: One of the popular pattern today and not advisable in production environment (violated least-privilege principle).
  In this approach delegating agent's full permission scope is passed to the sub-agent without constraint. The sub-agent operates with
  the same access as the orchestrator, regardless of whether the delegated task requires it.

- Scoped delegation : The orchestrating agent generates a time-limited, scope-limited delegation token that the sub-agent presents to the
 systems it needs to access. This requires the orchestrating agent to have the capability to generate delegation tokens which is a
 capability most current agent frameworks do not provide natively.

- Trust score inheritance: In this approach (which is based on trust scoring discussed above), the trust level of a sub-agent is
  constrained to a level lower than the current trust score of the delegating agent. This pattern requires a shared trust scoring
  infrastructure that all agents in the pipeline participate in, which does not currently exist in standardised form.

Another related problem is when an orchestrating agent delegate task to a sub-agent, how can the receiving agent verify that the
delegating agent is authentic and not introducing security risks, such as through prompt injection or malicious instructions. This
is currently being discussed in open source development forums like Microsoft Agent Governance Toolkit where discussions are ongoing
around establishing trust verification mechanisms between agents and there are proposals for new protocols like Inter-Agent Trust
Protocol which aim to address this by enabling agents to validate the identity, intent, and trustworthiness of other agents before
accepting and executing delegated tasks. Refer to link for more details.

### Intervention and Control Relevance

From an I&C perspective, both single-agent trust models and multi-agent trust delegation scenarios require a shift from static
access control followed in current software and human based systems to a continuous, real-time supervisory control framework.
It is essential to establish intervention points across the entire agent lifecycle, that allows I&C systems or human supervisors
to monitor, validate, override, or terminate actions based on contextual risk, policy compliance, and business impact. This
includes defining autonomy levels (e.g., observe-only, human-in-the-loop, human-on-the-loop, fully autonomous) that dynamically
adjust based on the agent’s trust score, task criticality, and operational context. Control mechanisms need to also support dynamic
constraint injection, that allows permissions, and execution boundaries (e.g., budget, scope, data access) to be modified during
runtime for both individual agents and chains of delegated agents. This also highlights the need for observability into the agent
actions so that I&C system can intervene to control based on trust score and associated risks.


# Gaps in the Current Approaches

## Limitations of Guardrails

There are many areas where guardrails cannot provide adequate control based on the current capabilities.

- Action focus: The Majority of the guardrails focus on the text boundary whereas in agentic system the critical
  boundary is the action execution, i.e. the point where a tool call, API invocation, or database write reaches a
  live system.

- Multistep execution: Guardrails are typically applied at single-turn boundaries, i.e. they evaluate one input
  or one output at a time. Currently, there is no well-defined mechanism for evaluating the governance implications
  of action sequences, or how a series of individually valid steps may collectively lead to unintended or non-compliant
  outcomes. This gap highlights the need for sequence-aware control and intervention mechanisms that can evaluate intent,
  track execution context across steps, and assess cumulative impact.

- Indirect instruction susceptibility: Agents are susceptible to security attacks, particularly those that exploit how
  context is constructed and consumed during execution. One prominent class of such attacks is prompt injection, which
  takes advantage of a key limitation in current guardrail architectures - i.e. the assumption that malicious or unauthorized
  instructions will appear only at the user input boundary.  In reality, agentic systems ingest information from multiple
  sources, and instructions can be introduced indirectly through retrieved documents (RAG), tool outputs, system messages,
  or intermediate reasoning steps.  Addressing this limitation requires a shift from boundary-focused guardrails to
  context-aware intervention and control mechanisms.

- Heavy human dependency:  Many guardrail implementations rely on human review for edge cases or escalations, which does not
  scale in high-speed or high-volume environments. Also, there is a fine balance required between flexibility of agent execution
  and reasoning, with the boundary of execution which is subjective.

## Limitations of Agent Drift Analysis

Agent drift is hard to detect as it seldom produce a failure event, only the effect of the drift can be observed through
continuous monitoring. Current drift management techniques are retrospective and does not intercept the degraded agent
behaviour as it occurs or does not automatically adjust agent policy in response to detected drift, and does not coordinate
drift signals with runtime intervention mechanisms. Agent drift management has similarities to Anomaly management. So a
potential direction is to leverage some of the techniques used in Anomaly management applied to Agents.

## Limitations of Quality gates

Three limitations characterize current implementation of quality gate.

- Implementation dependency on framework primitives. Quality gate behaviour is entirely developer-constructed from
  framework-specific primitives. There is no standard quality gate interface, no standard evaluation schema, no standard
  routing decision vocabulary, and no standard audit record format. A quality gate implemented in LangGraph is architecturally
  incompatible with one implemented in CrewAI or AutoGen. They cannot be governed, observed, or audited through common
  infrastructure.

- Absence of external governance observability. Quality gate evaluations are internal to the agent workflow. No current framework
  provides a standardised mechanism for an external governance authority to observe what quality evaluation was performed, what
  dimensions were assessed, what score was produced, and why a specific routing decision was made.

- No central governance or intervention and control. Quality gate outcomes particularly human review and/or rejection decisions
  are not connected to a central governance infrastructure. A gate that routes to human review pauses execution within the agent
  framework, but that pause is not expressed as a standardised intervention signal that a central governance authority can monitor,
  escalate, or resolve. The gate operates in isolation from the broader governance stack.

## Limitations of Intervention Approaches

As highlighted above intervention mechanisms exist in primitive and framework-specific forms. They have the following limitations.

- Absence of a standardised external interface that allows an authorized governance authority outside the framework or outside the
  agent application to signal intervention and receive a guaranteed response

- Current practice of intervention (leveraging infrastructure level interventions) is largely binary: either the agent runs or it
  does not. It lacks mechanisms that are flexible and applied across spectrum of scenarios - soft redirect, scope restriction,
  checkpoint, task suspension, rollback, hard termination

- When current intervention mechanisms stop an agent , whether through process termination, task cancellation, or API revocation,
  they do not systematically preserve the agent's execution state in a form that enables recovery.

- Current intervention mechanism requires either a human decision or a pre-coded condition to trigger it. There is no mechanism
  that continuously monitors agent behaviour against governance policies and automatically triggers a proportionate intervention
  response when a deviation is detected

## Limitations of Security I&C

From the I&C perspective following are some of the key limitations in incorporating Security controls in agent.

- Security control mechanisms primarily govern inputs and outputs, but have limited ability to fully interpret or validate the
  internal reasoning process of the agent. As a result, reasoning errors or misalignment may go undetected until they take effect
  through actions.

- In federated or multi-agent environments, enforcing consistent security and I&C policies across domains is complex. Differences
  in trust models, policies, and enforcement mechanisms can lead to gaps in control.

- Security standardization for agents is still evolving (e.g. OWASP Top 10 for Agentic Applications provide an emerging taxonomy
  of agent-related security risks) but they remain primarily focused on risk identification rather than operational control. At
  present, most control mechanisms are tightly coupled to specific frameworks or vendor implementations, leading to fragmented and
  non-interoperable approaches.

## Limitations of Trust I&C

Current trust models are implementation-specific and lack interoperability across agent frameworks. Advanced approaches highlighted
above, such as dynamic trust scoring, evaluate agent behavior within the context of a single framework, rather than considering
interactions across collaborating agents. A key limitation in existing trust control models is the handling of delegated trust which
is the trust relationship that arises when an orchestrating agent delegates authority to a sub-agent. Current frameworks do not provide
a consistent approach to this. For example, when a highly trusted orchestrator assigns a task to a sub-agent, it is unclear what level
of trust the sub-agent should inherit, or what constraints should govern the delegated authority.

# Standardization Area

As highlighted in previous sections, the realization of I&C capabilities needs to move toward a more uniform approach aligned with
established governance practices. The current pattern of implementing these capabilities within individual frameworks results in
fragmentation, limiting interoperability and increasing maintenance overhead. To address this, I&C must be supported through a
standardised approach that enables consistent behavior across agents, platforms, and domains. Such an approach should provide
shared interaction models, and standardised interfaces that allow governance policies, control mechanisms, trust delegation and
observability constructs to be applied uniformly.

This section outlines key areas where standardization is required to support the design, implementation, and operation of I&C in
autonomous networks. These areas span architectural considerations, interaction models, governance mechanisms, and protocol-level
extensions, highlighting the cross-cutting nature of I&C across the system stack. The intent is to identify foundational areas that
require further study and alignment within IETF Autonomous Networks work items and the broader CSP transformation towards AI-native
operations. Note that some of these items can span development across multiple stages - for example Stage 1 - Service
Description/Requirements, Stage 2 - Technical Realization, Stage 3 - Protocol Level extensions (e.g. A2A-T)

- Agent Intervention and Control Architecture: Define/Formalize the structural extensions required to the current AN Agent Architecture
  to support centralized, framework-agnostic governance.

- Agent I&C Taxonomy - Failure Modes, Intervention & Control Messages, Observability Constructs: Provides a standardised vocabulary of
  failure modes, I&C actions, and observability constructs across multi-agent systems. It establishes a common foundation for consistent
  monitoring, diagnosis, and intervention.

- Agent I&C Interface Specification: Specifies the standardised external interface through which the governance plane communicates with
  agents from the human operators. Currently, every control and intervention point is only reachable through framework-specific, proprietary mechanisms. This
  specification defines a common protocol capabilities that any compliant agent must expose, regardless of its underlying framework.

- Agent I&C Contract Specification:Addresses the absence of a standardised governance contract model for expressing the runtime I&C
  relationship between an agent and its operational environment (or between agents). Specifies, in a vendor-neutral and framework-agnostic
  way, the minimum set of I&C capabilities an agent must expose: what obligations it accepts, what authorities the operator holds to control
  the agent, and how these are communicated and enforced across the agent execution lifecycle.

  * Optional - Zero-Trust for Agent

  * Optional - Agent Trust Control and Delegation: Defines how trust is assigned, delegated, and enforced across agents

- Guardrail Specification: Focuses on defining the constraints and safeguards that govern agent behavior at runtime. Guardrails may apply to
  inputs, outputs, actions, and access to context or data, and are intended to prevent unsafe, non-compliant, or unintended outcomes. The
  objective is to provide a structured approach to specifying and enforcing these constraints in a way that is consistent, composable, and
  aligned with overall governance policies.

- Agent Interoperability/Interaction Standards Extension: Focuses on extending existing agent interaction protocols and standards to incorporate
  governance, trust, and I&C capabilities. It addresses how agents can interoperate not only at the level of functionality but also with respect
  to control, policy enforcement, and observability.

  * Agent Card Extension - Governance Capability Declaration - Extends the Agent Card with a governance manifest block that declares what I&C
    capabilities an agent supports
  * Agent Governance Contract Establishment - Negotiation and exchange of governance terms at connection or session initiation
  * Multi-Agent Task Execution Authority Delegation - Defines a protocol-level mechanism for carrying the authority chain alongside task delegation between agents
  * Intervention and Control Message Envelope - Structure and semantics of messages used to perform intervention and control actions.
  * Human Escalation/Intervention Message Envelope - Focuses on enabling human-in-the-loop interactions by standardizing how escalation and
    intervention requests are communicated.

# Security Considerations

There are no security considerations for this document.  It does
discuss a number of security issues in the course of problem
analysis, such as Identity and Access Management, Trust Delegation
across Agent, Trust Level Assignment.  The security considerations for
Agent Intervention and Control are discussed separately in
{{?I-D.wmz-nmrg-agent-ndt-arch}}.


# IANA Considerations

This document has no IANA actions.


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.

