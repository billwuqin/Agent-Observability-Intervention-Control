# What is ICON:

ICON focuses on addressing non deterministic behaivor exhibiting by AI Agent,
-	it is built on top of continuous observability of AI agent behavior;

-	introduce the ability of human operators to intervene when an agent goes wrong (e.g., task suspension, rollback to a last known safe state, or termination),

-	and enable the control of what an agent is permitted to do before and during action execution.

# Why ICON?

As Agentic AI systems are increasingly integrated into
autonomous workflows and critical infrastructure, these static
measures are proving insufficient for the full operational lifecycle,
e.g.,

   *  Unable to detect, interrupt, and rollover from unanticipated
      behaviors;

   *  Network operators usually lack an equivalent infrastructure or
      platform for human oversight;

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

  * Agent observability Data model (Not YANG based)

  * Agent intervention protocol  (Application Protocol)

  * and Agent control protocol (Application protocol)

which can be applied to various different use cases, not limited to network management cases.
which is similar to what AUDIT did. 

# Pointers to Relevant Work (I-Ds, Draft Charter, Side meeting materials)

I-Ds:

  * ICON Problem Statement: draft-wnd-opsawg-icon-ps

  * ICON Requirement: draft-mcw-opsawg-icon-requirements

  * ICON Solution Related: draft-pei-opsawg-agentops-observability

Draft charter:

  * https://github.com/billwuqin/Agent-Observability-Intervention-Control/blob/main/ICON-Work-Description.md

Side Meeting Materials:

  * https://github.com/billwuqin/Agent-Observability-Intervention-Control/tree/main/presentation


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

# What are Key Applications of ICON Related Technologies

- AI guardrail Application

- Agent Drift Detection Application

- Quality Gate Application


# Do We Need a Dedicated Mailing List for ICON?

Yes, A Dedicated Mailing List is required for "Agent Observability, Intervention and Control"

The current discussion is on the AINETOPS mailing list <ainetops@ietf.org>

# Hackathon Implementations

- [AgentOps observability and failure diagnosis prototype](<Hackathon/IETF 127/running code/agentops/README.md>): runtime measurements, normalized trajectories, anomaly detection, evidence-based attribution, reproducible scenarios and tests.
