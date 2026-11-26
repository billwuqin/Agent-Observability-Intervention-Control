# What is ICON:

ICON focuses on addressing non deterministic behaivior exhibiting by AI Agent,
-	It is built on top of continuous observability of AI agent behavior;

-	Introduce the ability of human operators to intervene on demand when an agent goes wrong (e.g., task suspension, rollback to a last known safe state, or termination),

-	Enable the control of what an agent is permitted to do before and during action execution.

# Who are the Consumers of ICON related technologies?

a. Network Operators:

  * Autonomous Network Operations (AIOps)

	- Preventing catastrophic actions
      * e.g., block unauthorized or high-risk configuration changes

    - Enforcing operational policies
      * e.g., stays within strict engineering safety limits before executing commands

  * Customer-Facing & Internal AI Assistants

    - Customer service bots
      * Prevent support chatbots from hallucinating billing policies, promising unauthorized plan discounts, or leaking subscriber data.

    - Technician copilots
      * Verify factual accuracy of network maintainance manual from AI assistant

  * Enterprise B2B Offerings (Telco-as-a-Platform)

	- Network-level AI security
      * Integrate into enterprise cloud and private 5G offerings to inspect AI traffic, block prompt injections, and filter sensitive data

	- Sovereign AI compliance
      * Help local businesses comply with national data privacy and AI safety regulations

b. Industry Verticals

 * Financial Services & Banking
   - e.g., Ensure customer-facing chatbots do not give unauthorized investment advice, leak account details, or violate strict compliance laws.

 * Healthcare & Life Sciences
   - e.g., Protect patient data (HIPAA compliance) and prevent AI tools from offering unsafe medical diagnoses.

 * Customer Support & E-Commerce
   - e.g., Stop chatbots from making unauthorized refund promises, using offensive language, or discussing competitors.

 * Enterprise SaaS & Software Vendors
   - e.g.,Ensure their product behaves reliably and safely for their business customers

 * Government & Legal Sectors
   - e.g.,Prevent confidential case data from leaking into public AI models and to verify factual accuracy.

c. Technial and Governance Teams

 * AI / Machine Learning Engineers
   - e.g.,Prevent large language models (LLMs) from hallucinating, going off-topic, or producing broken output formats

 * Cybersecurity & AppSec Teams
   - e.g.,Block prompt injections, jailbreaks, and adversarial attacks

 * Data Privacy & Compliance Officers
   - e.g., Automatically detect and redact Personally Identifiable Information (PII), financial data, or trade secrets from user prompts and AI responses

 * Chief Information Security Officers (CISOs) & Risk Leaders
   - e.g., Enforce company-wide AI policies and maintain audit trails for regulators

# Why ICON?

As Agentic AI systems are increasingly integrated into
autonomous workflows and critical infrastructure, these static
measures are proving insufficient for the full operational lifecycle of Autonomous Agents,
e.g.,

   *  Unable to detect, interrupt, and rollover from unanticipated
      behaviors;

   *  Unable to provide continuous monitoring of an AI system's internal
      logic or its long-running execution paths that match the speed and
      scale of the network management Agent applications, e.g., network
      failure or security risk is hard to detect and control, occurring
      at machine speed.

   *  When a violation related to input/output filter is suspected,
      there are currently no standardized interoperable protocols for
      network operation and task intervention (e.g., immediate task
      suspension) and recovery (e.g., reverting to a last known safe
      state or undoing a series of autonomous actions that introduce
      substantial operational risk) mechanisms.

   *  In non-deterministic environments, the lack of human oversight and
      human-AI semantic intent exchange hinder timely risk mitigation
      and state recovery during boundary violations by agents.

# What are the Expected ICON Deliverables?

ICON focus on defining generic building blocks including:

  * Architecture for Agent Observability, Intervention and Control and Human Oversight

  * Agent observability Data model (Not YANG based)

  * Agent intervention protocol  (Policy based Application Protocol)

  * and Agent control protocol (Policy based Application protocol)

which can be applied to various different use cases, not limited to network management cases.
which is similar to what AUDIT did. 

# What are Key Applications of ICON Related Technologies

- AI guardrail Application

- Agent Drift Detection Application

- Quality Gate Application

- Agent Benchmarking and Application

- Human Oversight Application

# Pointers to Relevant Work (I-Ds, Draft Charter, Side meeting materials)

I-Ds:

  * ICON Problem Statement: draft-wnd-opsawg-icon-ps

  * ICON Requirement: draft-mcw-opsawg-icon-requirements

  * ICON Solution Related: draft-pei-opsawg-agentops-observability

Draft charter:

  * https://github.com/billwuqin/Agent-Observability-Intervention-Control/blob/main/ICON-Work-Description.md

Side Meeting Materials:

  * https://github.com/billwuqin/Agent-Observability-Intervention-Control/tree/main/presentation


# Do We Need a Dedicated Mailing List for ICON?

Yes, A Dedicated Mailing List is required for "Agent Observability, Intervention and Control"

The current discussion is on the AINETOPS mailing list <ainetops@ietf.org>

# What is Human oversight/ Human on the Loop?

The practice of delegating authority to autonomous agents with guardaril policies or constraints and keeping humans away from being actively
involved in continuously monitoring of Autonomous agents and provide on demand intervention
or control on the Autonmous Agents if needed. This practice prevent Humans suffering from alert fatigue if forced to watch every routine step.
In the agent trajectory management, it ensures that Autonomous Agents do not go off the rails, violate safety protocols, or waste resources.
It transforms a fully autonomous "black box" into a controllable and collaborative system.

# Human on the Loop vs Human in the Loop

Note that ICON focuses on ***Human on the loop*** instead of human in the loop.
Human-on-the-Loop (HOTL) allows an agent to act autonomously while a human monitors the trajectory and intervenes or control only when
necessary whereas Human-in-the-Loop (HITL) requires explicit human approval before an agent can execute an action or the next action. 

| Difference | HOTL(Human On the Loop)  | HITL (Human in the Loop) | 
|---|---|---|
|Workflow|Asynchronous / Non-Blocking The agent executes independently unless a human steps in|Synchronous / Blocking The Agent execution highly depends on Human Approval|
|Primary Human Role|Supervisor — Monitors live telemetry, handles exceptions, and triggers overrides|Gatekeeper & Approver — Validates each decision or actions|
|Speed&Scalability|High throughput; allows multi-agent workflows to run continuously at machine speed|scales poorly if humans must approve routine steps|
|Delegation Model|Bounded delegation — Authority is pre-delegated with Guardrail policies|Real time continous delegation — Authority is granted per action or short-lived task|

# How is ICON different from Traditonal AI Guardrail?

 Traditional AI guardrails operate at fixed transition points — filtering prompts at the LLM input, validating responses at the LLM
 output, and checking static rules before a tool call. They assume dangerous behaviors can be predicted upfront and blocked with
 static policies.

 ICON governance plane can be break down into Agent Supervisory Plane and Agent Enforcement Plane. The ICON Enforcement Plane
 as policy enforcement point embeds those AI guardrails for fast, local rejection of obvious violations, while adding dynamic
 governance capabilities that static guardrails lack but not limited to:

 * Agent Intervention Signaling

 * Agent Control Signaling

 * Dynamic run time policy adding, deleting, update:
   The Agent Supervisory plane as policy decision point allows dynamic run time policy rules adding, deleting, update based on
   Evaluation results of Agent Observability Data.
 
 * Runtime Intervention:
   The Enforcement Plane listens to live Control and Intervention Signals from the Supervisory Plane—allowing a human operator or the supervisory
   plane to pause, throttle, redirect, or trigger a post-execution rollback mid-workflow when continuous observability detects goal drift.

 * Delegation & Precedence Enforcement:
   When multiple agents collaborate across domains, the Enforcement Plane resolves policy conflicts, enforces authority precedence
   (ensuring a human operator or supervisory policy preempts a sub-agent), and validates delegated scope bounds.
 
 * Distributed Concurrency & Resource Locking:
   The Enforcement Plane prevents multiple autonomous agents from executing conflicting changes on the same shared resource simultaneously.

# What has been observed through ICON Observability Component?

 * Agent Behavior and Execution Paths
   Supervision systems track the patterns of reasoning, decision-making, and actions an autonomous agent takes to achieve a goal, ensuring it
   stays within operational boundaries.
 
 * Trajectory Records
   The system captures audit logs and trace information covering the agent's entire reasoning sequence, tool executions, knowledge retrieval,
    and multi-agent collaborations

 * Performance and Behavioral Drift
   Monitoring evaluates agents in production environments to detect operational anomalies, performance degradation, or deviations from expected
   behavior over time.

# Where ICON Enforcement plane is placed?

Where ICON Enforcement plan is place is implementation specific. One of option is to make ICON Enforcement plane place at the unfied
agent gateway. The unified agent gateway can be part of orchestration layer or network layer or network element layer
and sits on the request path between autonomous agents, LLM providers, LLM consumers
and external tool servers or MCP server and provide the folowing capabilties:

* Provide consistent centralized policy enforcement

* Provide unified HOTL Agent Observability

* Execute cascading kill switches

# Hackathon Implementations

- [AgentOps observability and failure diagnosis prototype](<Hackathon/IETF 127/running code/agentops/README.md>): runtime measurements, normalized trajectories, anomaly detection, evidence-based attribution, reproducible scenarios and tests.
- [Agent Control and Enforcement Plane](<Hackathon/IETF 127/running code/control_plane/README.md>): the component that decides whether a proposed network mutation is permitted or refused
- [A2H (agent to human) protocol](https://github.com/twilio-labs/Agent2Human): Agent to Human communication protocol for multi-channel approvals
- [Agent Control](https://github.com/agentcontrol/agent-control):Enforce runtime guardrails through a centralized control layer; Evaluates inputs and outputs against configurable rules to block prompt injections, PII leakage, and other risks without changing your agent’s code
- [Agent Control for 4K streaming session handover](https://github.com/billwuqin/Agent-Observability-Intervention-Control/tree/main/Hackathon/IETF%20127/running%20code/ietf-icon-agent-handover): Showcase policy-driven observability, automated refusal of unsafe actions, and Test human-in-the-loop rollback and recovery controls
]
