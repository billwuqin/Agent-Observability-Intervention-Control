---
title: "Problem Statement for Observability, Intervention and Control (I&C) in Multi-Agent Autonomous Networks"
abbrev: "Observability and I&C"
category: info

docname: draft-wnd-opsawg-icon-ps-latest
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
  latest: "https://billwuqin.github.io/ICON-problem-statement/draft-wnd-opsawg-icon-ps.html"

author:
 -
    fullname: Qin Wu
    organization: Huawei
    email: bill.wu@huawei.com
 -
    fullname: Daniele Ceccarelli
    organization: Cisco
    email: daniele.ietf@gmail.com
 -
   fullname: Zhenqiang Li
   organization: CMCC
   email: li_zhenqiang@hotmail.com
 -
   fullname: Luis. M. Contreras
   organization: Telefonica
   email: luismiguel.contrerasmurillo@telefonica.com
 -
    fullname: Qiufang Ma
    organization: Huawei
    email: maqiufang1@huawei.com

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

  IG1507:
    title: IG1507 Intervention and Control for Agentic Operation V1.0.0 DRAFT
    target: https://projects.tmforum.org/wiki/pages/viewpage.action?pageId=411641744
    date: May 2026

  IG1251G:
    title: IP Network AN Level 4 Agentic Architecture for Multi-Scenario Autonomy
    target: https://projects.tmforum.org/wiki/pages/viewpage.action?pageId=401824956
    date: May 2026

--- abstract

This document provides an overview of the issues associated with the
deployment of the observability, intervention, and control of autonomous
agent pipelines in large-scale heterogeneous network environments. The
term "Intervention and Control" is used to describe a set of automated and
human-initiated mechanisms that guarantee the capability to observe, constrain,
correct, and terminate Autonomous agents at any point, for any reason, irrespective of
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
management Agent applications at the network level and service level. The Agent lifecycle
management comprise the following phases:

- Agent Discovery: Discover capabilities and skills and onboard agent

- Agent Benchmarking: Test behavior before deployment

- Agent Deployment: move agent from pilot project to production environments

- Agent Observability: continuous monitor and evaluate performance and behavior deviation in production

- Agent Intervention and Control: Constrain Agent behavior within operational boundary

- Agent Upgrade: Large language model, tools, prompts, memory related software update

To help network operators manage AI agents with more consistency, visibility and control,
the observability phase, intervention and control phase need to work
in a collaborate manner and are critical for the Agent lifecycle management.

Since AI native operations may be non-deterministic, when network management agents
misbehave or deviate from what Agents are expected to do, current AI control
technologies (often referred to as "AI guardrails") are introduced to constrain
the behavior of AI agents within operational and compliance boundaries, prevent
AI from producing harmful results or taking wrong actions, e.g., escalate a decision
to a human for a high-risk network operation, defend against malicious attacks,
e.g., prompt injection. These AI guardrails enable you to do checks and validations of user
input and agent output and typically break down into input input guardrail, action guardrail,
output guardrail and operate at the input/output/pre-action
filter level with static boundary parameters. For example, imagine you have an agent
that uses a very smart (and hence slow/expensive) model to help with customer requests.
You wouldn't want malicious users to ask the model to help them with their math homework.
So, you can run a guardrail with a fast/cheap model and block agents for specific usages.
If the guardrail detects malicious usage, it can immediately raise an error and prevent
the expensive model from running, saving you time and money.

However, as Agentic AI systems are increasingly integrated into autonomous workflows and
critical infrastructure, these static measures are proving insufficient for the
full operational lifecycle, e.g.,

- Unable to detect, interrupt, and rollover from unanticipated behaviors;

- Network operators usually lack an equivalent infrastructure or platform for human oversight;

- Provide continuous monitoring of an AI system's internal logic or its long-running
  execution paths that match the speed and scale of the network management Agent applications,
  e.g., network failure or security risk is hard to detect and control, occurring at machine speed.

- When a violation related to input/output filter is suspected, there are currently no standardized
  protocols for intervention (e.g., immediate task suspension) and recovery (e.g., reverting to a
  last known safe state or undoing a series of autonomous actions that introduce substantial
  operational risk) mechanisms.

- In non-deterministic environments, the lack of human oversight and human-AI semantic intent exchange
  hinder timely risk mitigation and state recovery during boundary violations by agents.

This document provides a problem statement for protocol on continuous agent observability, intervention and control.
We list the properties the protocol should have, then explain why those properties are necessary. We describe why a
new protocol is the best solution for the more general problem of identifying and characterizing trajectory records
related to agent behavior or workflow operation, continuous monitoring and evaluation, enable human oversight, provide
human and agent interaction for agent intervention and control at the service level and network level.

Where possible, any solutions work will be built in a modular way using existing IETF protocols.
However, no protocol solution choices will be made until the functional requirements have been
agreed, and then this will require an analysis of the capabilities of existing protocols and
identify gaps that need to be filled.

# Conventions and Definitions

{::boilerplate bcp14-tagged}

-  Autonomous Agent: An AI-driven software entity capable of accepting
    a declarative goal and executing non-deterministic tasks.

-  Agent Drift: Gradual performance degradation or misalignment of
    reasoning patterns over time in a production environment.

-  Cascading Failure: A scenario where a failure in one downstream
    agent propagates across multi-agent boundaries.

- Human to Agent Communication: The interaction between human users and network management Agent designed to perform tasks, solve
    problems, or provide information. Unlike standard human-to-machine interaction where a human drives every step of a
    task, human-agent communication involves delegation, where the human provides a goal and the agent autonomously figures out
    how to achieve it.

- Agent Observability: The visibility into an agent's internal state, decision-making logic, and workflow execution from its
   external telemetry outputs (e.g., logs, traces, metrics), enabling human   operators or monitoring systems to understand what
   the agent is doing and why it behaves in a specific manner.

- Intervention: A reactive, emergency action to intervene or take control of an agent with boundary violations, anomalies, failures,
                or risks, so as to block harmful decisions, disrupt hazards, malicious abuse, and promptly mitigate losses.

- Control: Establish a deterministic operational boundary for the agent before execution. By pre-defining the agent's behavior scopes,
           operational constraints, and security baselines, it fundamentally mitigates abnormal behaviors from agents.

- Evaluation: Using Trajectory Record to assess the performance and understand how an Agent solves problems, e.g., checking if the
          agent took the shortest sequence of actions or wasted resources on redundant tools or analyzing specific segments of the
          trajectory to see if the agent excels at information retrieval but struggles with mathematical synthesis.

- Human Oversight: The practice of keeping humans actively involved in continuously monitoring of Autonomous agents. In agent trajectory
                   management, it ensures that network management agents do not go off the rails, violate safety protocols, or waste
                   resources. It transforms a fully autonomous "black box" into a controllable and collaborative system.

- Behavior: pattern of reasoning, decisions, and actions an Autonomous agent takes to achieve a specific goal such as reasoning sequence,
            the sequence and logic of execution paths.

- Trajectory Record: Keep track of Agent behaviour and produce audit log or trace information to Capture the entire "flight path"
                     or reasoning sequence the agent followed to reach its conclusion using a structured Thought,Action,Observation
                     loop.

# Problem Space

The deployment of autonomous agentic systems within operators' networks introduces fundamental operational,
architectural challenges. Current network management paradigms are built on deterministic models that assume
predictable, rule-based behaviors. The shift toward non-deterministic (probabilistic), AI-driven network
operation architectures creates a structural mismatch between machine-speed execution and human-speed oversight.
This gap manifests in several distinct problem areas:

## The Observability Aspect

### Limited Transparency in Planning and Decision-Making

As agents increasingly execute complex operational tasks, they
frequently delegate critical planning paths and execution decisions to
Large Language Models (LLMs) or specialized downstream AI models. This
delegation creates an optimization barrier, offering limited
transparency into how specific decisions are reached or how complex
action sequences are generated.

Without an out-of-band mechanism to inspect this reasoning layer, operators
cannot validate the safety or intent of an agent's planned mutations before
they introduce unexpected consequence on the infrastructure.

### Ambiguity of Accountability Attribution

In distributed multi-agent topologies, operational responsibility for an ultimate
network outcome is scattered across an extended chain of coordinating agents,
foundational models, and abstraction layers. When system failures, performance
degradations, or unintended consequences occur, attributing accountability to
a specific agent entity, localized model decision, or human-in-the-loop anchor
becomes highly ambiguous. This lack of clear traceability or metrics characterizing
agent operational health such as action execution latency, error rates, creates severe
complications for post-incident root-cause analysis and regulatory compliance reporting.

### High-Velocity Data Ingestion

Agents are explicitly designed to operate with high degrees of autonomy, speed, and
scale. However, network operators currently lack the corresponding telemetry
mechanism and control infrastructure required to observe, evaluate, and intercept
these systems at the same machine-speed pace. Consequently, effective
real-time oversight becomes functionally impossible. Always relying on human
escalation paradigms is usually impractical due to the sheer volume and velocity
of the data points involved in active agent pipelines.

## The Control Aspect

### Inadequacy of Deterministic Constraints

Agent behavior cannot be reliably constrained using predefined,
deterministic rules or traditional static guardrails. Because agents
rely on dynamic reasoning patterns to achieve declarative goals, their
exact execution trajectories remain non-deterministic. This intrinsic
variability makes operational outcomes significantly less predictable
during runtime execution, bypassing legacy input/output filters that
fail to account for real-time contextual adaptation.

### Static IAM Limitation

Existing trust and authorization models have failed to evolve in step with
dynamic agentic AI architectures. Traditional Identity and Access Management
(IAM) frameworks were designed exclusively for human operators or static,
deterministic software processes. These frameworks cannot securely tackle
emerging dynamic agent atributes such as autonomous entity identities and behavioral
profiles which are frequently created and modified at runtime rather than being
pre-provisioned with metadata information to describe functional capabilities, nor can
they safely manage downstream sub-agent permission delegation or context-dependent
privilege escalation.

### Fragmentation Across Heterogeneous Integration Layers

Agentic systems operating across mixed Operational Support Systems (OSS)
and Network Management domains must interact with a highly
heterogeneous mix of legacy systems, modern APIs, and third-party
platforms. Establishing consistent, operational and compliance boundaries across these
disparate integration layers is exceptionally complex as agents may routinely validate intent,
invoke actions or retrieve data through pathways (e.g. MCP/A2A etc.) that were never
designed with network management automation we used today.

### Multi-Vendor Dependency Risks

As network operators begin sourcing agentic control capabilities from diverse third-party
vendors, independent software providers, and hyperscalers, operational
accountability becomes externalized in ways that are difficult to technically
or contractually enforce. A typical production agent implementation features
highly fragmented dependency chains spanning completely separate vendor
ecosystems, including LLM/AI model providers, infrastructure hosts, core
agent frameworks, tool/API repositories, and interconnection fabrics.

## The Intervention Aspect

### Lack of Human Oversight

Core features such as multi-agent execution, advanced interoperability frameworks
for agent to agent, agent to tools communication (e.g., Agent-to-Agent {{A2A}}
and Model Context Protocol {{MCP}}), and long-running autonomous actions are
advancing rapidly.

However, essential human oversight capabilities including runtime intervention for execution
interruption, deterministic transaction rollback and Recovery, and human escalation remain highly
immature and lack clear standardisation paths.

### AI-Native Failure Emergence

Agentic systems introduce an entirely new class of complex, systemic failure
modes that legacy operational risk frameworks are blind to detect or contain.
These include:

- Multi-agent alignment failures, where the isolated actions of
  individual sub-agents appear structurally correct and compliant with their
  local plans, yet collectively combine to produce a catastrophic network state.

- Additionally, systems suffer from agent drift, where an agent's reasoning pattern
  and behavioral outputs shift unpredictably over time as it continuously adapts
  to an evolving network context.

# Solution Space for Network Management Agent Observability, Intervention and Control

## Opentelemetry for Agent Observability

Modern agents orchestrate complex workflows: reasoning chains, tool execution, knowledge retrieval, multi-agent collaboration. When
things go wrong, or right, you need to understand exactly what happened. Traditional network monitoring such as gRPC, SNMP, YANG Push
can't capture reasoning processes or decision context. Opentelemetry addresses this by utilizing unified GenAI and Agent Semantic
Conventions to standardise how metrics, logs, and distributed traces are captured across multi-agent system.

Implementing OpenTelemetry for AI agents focuses heavily on distributed tracing to how an agent processes information, arrives at
decisions, and executes tasks as follows:

- Distributed Tracing (Spans): The agent as a whole run acts as the root span. Every individual reasoning loop, agent delegation, LLM
  invocation, and tool/API execution is mapped as a child span. This layout instantly reveals where latencies, bottlenecks, or errors
  occur.

- GenAI Semantic Conventions: Standardised metadata tags provide explicit context. Spans automatically record critical variables across
  four critical domains: System Context, Token Economics, Vector Retrieval, and Agent Reasoning,like gen_ai.request.model,
  gen_ai.usage.input_tokens, and gen_ai.usage.output_tokens.

- Protocol, Decision and System Events: When opted-in, Opentelemetry logs every agent actions, every decision, every protocol
  communication between agents or between agent and tools. This visibility allows engineers to review the exact context that caused an
  agent to exhibit non-deterministic behavior or get stuck in an infinite loop.

## AI Guardrails

These are most mature, and most operationally familiar AI control mechanism in production today. AI Guardrail
approaches currently realized in the industry operate at defined transition points in the agent pipeline, primarily
prompt filtering at the LLM input boundary, response validation at the LLM output boundary, and access control
restrictions on tool invocation boundary. Currently, AI Guardrails are checks that run alongside your agents to catch
bad input or bad output — without necessarily involving your selected large language model(expensive or cheap).
For example, imagine you have an agent that uses a very smart (and hence slow/expensive) model to help with customer
requests. You wouldn't want malicious users to ask the model to help them with their math homework. So, you can run a
guardrail with a fast/cheap model. If the guardrail detects malicious usage, it can immediately raise an error and
prevent the expensive model from running, saving you time and money.

AI Guardrail are realized through 4 different mechanisms:

- Rule based filters: Apply pattern matching, keyword blocking, regular expressions, and deterministic logic to
  prompts, context retrieval and completions.

- LLM based safety classifiers: Use a secondary language model to evaluate the primary model's output for safety
  policy compliance before it is returned.

- Agent framework based guardrail libraries: Provide structured policy specification languages (e.g. NeMo Guardrails)
  that allow developers to express policy rules in a higher-level format, with the framework handling enforcement
  logic.

- Prompt engineering constraints: shape model behaviour by instruction rather than by interception.

## Agent Drift Detection

Agent drift refers to the gradual degradation in an agent's performance and alignment with intended behavior over time
in production environments. It exists in many forms depending on the aspect of the system affected. For example, goal
drift occurs when the quality of goal execution deviates from expectations, context drift when the relevance or
accuracy of the working context deteriorates; reasoning drift when there is a decline in the agent's planning and
decision-making capability, and collaboration drift when the effectiveness of interactions with tools, external APIs,
or other agents degrades.

Agent drift is a well-recognized problem in academic research and agent frameworks. However, there is no universally
applicable control mechanism that addresses all scenarios in practice. A key reason for this is the
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
allowed.

Unlike guardrails which enforce policy constraints at defined boundaries of Agent implementation, quality
gates assess whether the work product of one stage meets a defined quality standard before permitting progression to
the next. The concept is borrowed from DevOps practice i.e. quality gates in CI/CD pipelines that prevent code from
advancing through build, test, and deployment stages unless it meets defined quality criteria. While guardrails determine
crossing points i.e. what enters and exits defined zones, quality gates determine progression points - whether work of
sufficient quality advances to the next stage.

Quality gates are the ideal mechanism to involve humans for agent tasks
execution quality and escalations, i.e., at stage transitions where the accumulated work product of a whole reasoning
stage is ready for assessment where the human is presented with a complete plan, a complete risk assessment, and a
specific decision to make.

Currently none of the available agent frameworks have a named capability called quality gate. However, some of the
existing functionality can be leveraged for realizing this. For example LangGraph has concept of conditional edges that
enable dynamic, non-linear workflows which allows routing execution to different nodes based on a state-evaluating
function or if-else statements. Similarly, Google ADK (Agent Development Kit) provides callback that can be invoked
before or after tool use and implement quality gate logic. So most of the techniques that exist today are agent
framework specific.

## Existing Intervention Approaches

The intervention mechanisms that exist today in agentic systems are mostly implementation-specific, tied to individual
frameworks, and not mature enough to form a consistent or deployable operational practice. Currently, the mechanisms
involve the following:

- Primitive and manually controlled repurposed from the infrastructure: Reuse approaches from the infrastructure
  control such as process termination, API key revocation, service account suspension, and network-level blocking
  which are not primarily designed for agentic systems. While they can be effective, operations like terminating an
  agent process preserves no state, enables no graceful recovery, produces no trace, and cannot be applied selectively
  to a specific action class or task scope.

- Framework specific intervention mechanisms: These are intervention mechanisms provided by specific agent frameworks.
  For example LangGraph provides an option to pause and resume the execution (pause , seek guidance from human, get
  response and then proceed). While this is primarily a Human-in-the-loop mechanism, it can be used as a workaround for
  interventions. But such mechanisms are implemented in code and not accessible externally through interfaces outside
  the agent framework. Crew AI framework provides mechanism to conditionally execute task or allows defining maximum
  iterations for task execution which prevents from getting into infinite loops. The kill-switch functionality (halt or
  restrict an agent's execution when predefined risk, policy, or trust conditions are violated) is supported in the
  Microsoft Agent Control Toolkit, but its interoperability across different agent frameworks is not proven.

## Trust & Security Control Approaches

Trust & Security in autonomous agents spans across multiple dimensions, including identity (who the agent is), authorization (what it is allowed to do), control (how its actions are performed during execution), behavior (whether it acts in alignment with expected goals and produces correct outcomes), and context (under what conditions it operates). Current industry approaches to agent Trust & Security primarily focus on protecting the agent from malicious interference to ensure that the inputs it receives and processes are not tampered with and manipulated. Intervention and Control is concerned with ensuring that actions remain within authorized boundaries, are observable, and can be corrected or reversed when necessary.

Traditional IAM frameworks, designed for human users and deterministic software processes, are insufficient to tackle the dynamic Trust & Security aspects of autonomous agents. The emerging Trust & Security Control approaches extend beyond static identity and permission models to incorporate context-awareness, temporal constraints, and behavior-driven trust evaluation.

From the I&C perspective, a prominent way to manage agent Trust & Security risk is to sandbox the agent's execution environment. This means running the agent in a restricted environment so it cannot cross trust boundaries, even if it is compromised. Dynamically limiting the execution boundary can be achieved by adjusting the agent's runtime environment, permissions, and accessible resources in real time based on task context and trust level.

Some of the approaches followed for controlling the agent trust are given below:

Agent privilege control: The most widely deployed current approach to agent trust control is the application of static least-privilege principles, granting agents the minimum tool access, API permissions, and system scope required for their designated tasks, expressed through standard IAM constructs (service accounts, API keys, OAuth scopes). Its limitation in agent-based systems is that tasks are dynamic. Permissions set for a typical task may be too limited for edge cases, pushing systems to grant broader access than necessary. On the other hand, permissions designed for complex tasks may be too broad for simpler ones. Also, static permissions cannot adapt to changing task needs.

Scoped and time-limited credentials: Agents often use API keys or service accounts with broad, long-lasting permissions (for tool calls, RAG or model access), which can create trust & security risks. Current best practices is to use short-lived, limited-access credentials, such as OAuth tokens with narrow scopes or JWTs with short expiry so that agents only have the minimum access needed for a specific task and only for a limited time.

Context aware trust assignment: Instead of static roles or scopes, access decisions are made dynamically using attributes and runtime context such as task type, data sensitivity, user intent, environment state, or risk level, e.g., agent is allowed to access certain tools/data only within/belonging to a compliant geography, where it is legally allowed to access such data.

Dynamic trust level assignment: This is one of the advanced and emerging mechanism (e.g. Microsoft Agent Control Toolkit) where instead of labelling agents as just trusted or untrusted, this model gives each agent a trust score that changes over time. The score increases when the agent follows policies and drops quickly when it violates them. This score then decides what level of access the agent gets, adjusting its permissions based on how trustworthy it is at that moment.

The first two approaches rely on a well-defined agent identity to assign and enforce permissions. The fourth approach focus more on the behavior of agent, i.e., it requires not just identity, but also continuous behavior-based evaluation, where access is determined by how the agent performs over time,i.e, based on trust score, agent is mapped to a trust zone or trust level that determines the authority and access assigned to agent. The definition and management of agent identity are beyond the scope of this document.

# Gaps in the Current Approaches

## Limitation of OpenTelemetry for Agent Observability

While OpenTelemetry (OTel) is the industry standard for collecting traces, metrics, and logs, it has critical limitations when
applied to AI agent observability. The fundamental limitation is that OpenTelemetry functions as a passive data plane for system
performance, not an evaluation or guardrail engine for AI behavior. It can track how an application runs, but it struggles to
evaluate what an agent decides.

Furthermore, OpenTelemetry only captures the execution process, not the operational motivation. It lacks native support for
observing metrics such as an agent's reasoning logic and internal confidence levels. OpenTelemetry originated in cloud-native
microservice architectures, its tracing lifecycle cannot represent asynchronous Human-in-the-Loop (HITL) workflows.
Consequently, it provides no mechanism to signal within a trace that a specific step constitutes a high-risk action,
has been suspended, and is currently awaiting human approval.

## Limitations of AI Guardrails

There are many areas where guardrails cannot provide adequate control based on the current capabilities.

- Action focus: The majority of the guardrails focus on the text boundary whereas in agentic system the critical
  boundary is the action execution, i.e. the point where a tool call, API invocation, or database write reaches a
  live system.

- Multistep execution: Guardrails are typically applied at single-turn boundaries, i.e. they evaluate one input
  or one output at a time. Currently, there is no well-defined mechanism for evaluating the control implications
  of action sequences, or how a series of individually valid steps may collectively lead to unintended or non-compliant
  outcomes. This gap highlights the need for sequence-aware control and intervention mechanisms that can evaluate intent,
  track execution context across steps, and assess cumulative impact.

- Indirect instruction susceptibility: Agents are susceptible to security attacks, particularly those that exploit how
  context is constructed and consumed during execution. One prominent class of such attacks is prompt injection, which
  takes advantage of a key limitation in current guardrail architectures - i.e. the assumption that malicious or unauthorized
  instructions will appear only at the user input boundary. In reality, agentic systems ingest information from multiple
  sources, and instructions can be introduced indirectly through retrieved documents (RAG), tool outputs, system messages,
  or intermediate reasoning steps. Addressing this limitation requires a shift from boundary-focused guardrails to
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

- Absence of external observability. Quality gate evaluations are internal to the agent workflow. No current framework
  provides a standardised mechanism for an external observability authority to observe what quality evaluation was performed, what
  dimensions were assessed, what score was produced, and why a specific routing decision was made.

- No central intervention and control. Quality gate outcomes particularly human review and/or rejection decisions
  are not connected to a central control infrastructure. A gate that routes to human review pauses execution within the agent
  framework, but that pause is not expressed as a standardised intervention signal that a central control authority can monitor,
  escalate, or resolve. The gate operates in isolation from the broader management and control stack.

## Limitations of Intervention Approaches

As highlighted above intervention mechanisms exist in primitive and framework-specific forms. They have the following limitations.

- Absence of a standardised external interface that allows an authorized authority outside the framework or outside the
  agent application to signal intervention and receive a guaranteed response

- Current practice of intervention (leveraging infrastructure level interventions) is largely binary: either the agent runs or it
  does not. It lacks mechanisms that are flexible and applied across spectrum of scenarios - soft redirect, scope restriction,
  checkpoint, task suspension, rollback, hard termination

- When current intervention mechanisms stop an agent , whether through process termination, task cancellation, or API revocation,
  they do not systematically preserve the agent's execution state in a form that enables recovery.

- Current intervention mechanism requires either a human decision or a pre-coded condition to trigger it. There is no mechanism
  that continuously monitors agent behaviour against control policies and automatically triggers a proportionate intervention
  response when a deviation is detected

## Limitations of Trust & Security Control Approaches

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
- Current frameworks do not provide a consistent approach to handle of delegated trust which is the trust relationship that arises
  when an orchestrating agent delegates authority to a sub-agent. For example, when a highly trusted orchestrator assigns a task to
  a sub-agent, it is unclear what level of trust the sub-agent should inherit, or what constraints should govern the delegated
  authority.

# Standardization Area

This section outlines key areas where standardization is required to support the design, implementation, and operation of Network
Management Agent Observability, Intervention and Control in Agent Fabric networks. In the Agent Fabric Network,
- Two or multiple scenario specifc network management agents can work together to support multi-scenario autonomy or close loop management.
- Two or muitiple scenario specific network management agents can work together to support cross domain collaboration.
- Two or mutiple sceanrio specific network management agents can work together to support collaboration between service layer and network layer.
the agent gateway can be used to collect metric, log, audit information from each network management agents.

The intent is to identify foundational areas that require align with network management technologies developed in IETF OPS Area and drive network
automation moving toward AI Driven Network Operation.

- Agent Observability, Intervention and Control Network Management Architecture: Developing or selecting a framework for enforcing boundaries,
  detecting, evaluating, interrupting, correcting, and recovering from agent behavior within operational and compliance boundaries.

- OpenTelemetry protocol extension Enabling network behavioral assessment through analysis of observed operational network data
  (logs, metrics, traces, etc.)

- Human and Agent Interaction protocol for Human Escalation/Intervention, Agent Intervention and Control

# Security Considerations

The security considerations applicable to Network Digital Twin and Agentic AI based Architecture for AI driven Network Operations
{{?I-D.wmz-nmrg-agent-ndt-arch}} are also applicable to this document.

# IANA Considerations

This document has no IANA actions.


--- back

# Acknowledgments
{:numbered="false"}

The authors of this document would also like to thank Benoit Claise, Daniele Ceccarelli for review and comments.
