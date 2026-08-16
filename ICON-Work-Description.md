# Observability, Intervention, and Control of Network Management Agents (ICON)

This page provides a short description of a proposed IETF work-item to address Observability, 
Intervention, and Control of Network Management Agents (ICON). The ICON work explores how an
automated Network Management Agent (such as one that is utilising AI function) can be 
continuously monitored, and how operators can intervene to control a Network Management Agent
that has gone wrong or is performing actions that are not what the operator wants. 

The intention of this page is to capture the scope of the ICON work, identify which parts are 
in scope for the IETF, and to serve as a focal point for collating all related work. As
discussions progress, this page will be updated to record new Internet-Drafts, and it is
anticipated that existing Internet-Drafts will continue to be refined.

One further purpose of this page is to aid the Area Directors (specifically the OPS ADs) in
dispatching this work to:

- a simple work item in an existing working group
- a specially commissioned design team within or across existing working groups
- a new working group

## Problem Statement and Work Scope

There has been a steady growth in the use of Network Management Agent applications used both at the network level and at the service level. This
has allowed network operations to become increasingly autonomous, but the use of AI-based agents in network management means that the behavior of
network management applications may be non-deterministic.

To help protect against AI-based Network Management Agents misbehaving or deviating from what from the operator expected them to do, AI safety
technologies, often referred to as "AI guardrails", can be to constrain the behavior of the AI agents to within operational and compliance
boundaries, to prevent the AI-based agents from producing harmful results or taking wrong actions, or to defend against malicious attacks. For
example, a decision for a high-risk network operation may be escalated to a human, defend against malicious attacks. These guardrails typically
operate at the input/output/pre-action filter level, or through static boundary alignment.

As Network Management AI systems are integrated into autonomous workflows and critical infrastructure, these static guardrail measures are proving
insufficient for the full operational lifecycle: they often cannot detect, interrupt, and rollback from unanticipated behaviors. Network operators
usually lack an equivalent automated infrastructure for human oversight or to provide continuous monitoring of an AI-based Network Managementt Agent’s 
internal logic or its long-running execution paths that match the speed and scale of the Network Management Agent applications. For example, it can 
be hard to detect and control network failures or security risks that are happening at machine speed.

When a violation of the guardrails is suspected, there are currently no standardized protocols for intervention (e.g., immediate task suspension) or
recovery (e.g., reverting to a last known safe state or undoing a series of autonomous actions that introduce substantial operational risk). In 
non-deterministic environments, the lack of human oversight and human-AI semantic intent exchange hinder timely risk mitigation and state recovery during
boundary violations by agents, yet the use of human oversight can introduce delays which may be relatively large compared to the speed of operation of the automated tools.

The goal of this ICON work is to explore use cases, derive requirements, and provide solutions for:
- identifying and characterizing trajectory records related to agent behavior or workflow operation
- facilitating continuous monitoring and evaluation
- enabling human oversight
- providing human and agent interaction for agent intervention and control at the service level and network level.

Where possible, any solutions work will be built in a modular way using existing IETF protocols. However, no protocol solution
choices will be made until the functional requirements have been agreed, and then this will require an analysis
of the capabilities of existing protocols and identify gaps that need to be filled.

## Terminology

The terms defined here are specifically within the ICON context. Thus, for example, any mention of an "AI agent" is in the context of that agent being used as part of a Network Management Agent or in support of its functionality.

- Human to Agent Communication: The interaction between human users and Network Management Agents designed to perform tasks, solve problems,
                                 or provide information. Unlike standard human-to-machine interactions where a human drives every step of a
                                 task, human to agent communication involves delegation, where the human provides a goal and the agent
                                 autonomously figures out how to achieve it and then acts to achieve it.
- Observability: Enabling network behavioral assessment through analysis of observed operational network data (logs, metrics, traces, etc.)
                with the aim of detecting symptoms of network behavior, and to identify anomalies and their causes.
- Intervention: Operates when something has gone wrong, is going wrong, or is about to go wrong to provide humans with the
                ability to detect, interrupt, correct, and recover from Network Management Agent behavior that is not anticipated by control mechanism.
- Control: Operates before and during actions executed by Network Management Agents. Defines what an agent is permitted to do, enforcing boundaries,
           and structuring the environment so that harmful or unauthorized actions are difficult or impossible to execute.
- Evaluation: Using Trajectory Records to assess the performance of agents and to understand how an agent solves a problem. For example, checking if
              the agent took the shortest sequence of actions or wasted resources on redundant tools, or analyzing specific segments of the trajectory to
              see if the agent excels at information retrieval, but struggles with mathematical synthesis.
- Human Oversight: The practice of keeping humans actively involved in continuous monitoring of AI agents. In agent trajectory management,
                   it ensures that Network Management Agents do not go wrong, violate safety protocols, or waste resources. It transforms
                   a fully autonomous "black box" into a controllable and collaborative system.
- Behavior: A Pattern of reasoning, decisions, and actions that an AI agent takes to achieve a specific goal such as a reasoning sequence, the sequence
            and logic of execution paths.
- Trajectory Record: A log or other data storage record that captures the data from Trajectory Recording.
- Trajectory Recording: Keeping track of agent behaviour to produce audit logs or trace information to capture the entire "flight path" or reasoning
                        sequence that an agent followed in reaching its conclusions using using a structured Thought / Action / Observation loop.

## Functional Requirements

The questions listed below drive the functional requirements for ICON.

- What are the typical scenarios for Observability, Intervention, and Control of Network Management Agents?
  - Which are specific for Agent Observability?
  - Which are specific for Agent Intervention and Control?
  - What component, function, application, or human does the Observation?
  - What elements of the system are Observed and Evaluated?
- What information needs to be collected and recorded to enable Observation and Evaluation?
  - Which performance metrics are used to charaterize the operational state of the Network Management Agent?
  - What Log information is collected?
  - What Trace information is used to charaterize the trajectory record of the Network Management Agent?
- How is Observability,Intervention and Control realized?
  - What components are responsible for Intervention and Control?
  - What information are used for Intervention and Control?
- Where does Observability, Intervention, and Control fit in the overall workflow?

## Out Of Scope

While the following topics are very important to the construction of an autonomous network management that uses Network Management Agents that comprise AI-based components, they are out of scope of the ICON work. It is hoped that other IETF work efforts will capture these topics for the general application of AI agents and the resulting output will be available to implementers and operators building AI-enabled network management systems.

- Agent Discovery. How individual Ai agents (or instances of AI agents) are discovered so that they can be used by the network management system is out of scope, but may be captured by the DAWN work effort.
- Agent-to-Agent Communication. How applications or AI agents communicate with other AI agents to exchange and negotiate capabilities and to perform tasks is not in scope, but may be captured by the AgentProto work effort.
- Trust, Authentication, and Authorisation of Agents is critically important to ensure that only legitimate AI agents are allowed to process the network data and to issue commands to control the network. This is out of scope for ICON, but may form part of the AgentProto effort or may be a separate IETF topic.
  
## Implementations and Interoperability

Implementation and interoperability are essential cornerstones of IETF work. It is important to understand which elements need to be built to interoperate.
- Input Guardrails
- Output Guardrails
- Interaction-Level Guardrails

### What are implementable components?

- Observability Component
- Evaluation Component
- Intervention Component
- Control Component

### What needs to be standardised?

**Protocols**
- Human and Agent Interaction interface for Intervention and Control;
- Telemetry Protocol Extension for Agent Behavior Observability;

**Protocol Properties**
- Trace, Log and Metric for Agent Observability
- Policy Element for Intervention 
- Policy Element for Control

### What are the interoperability interfaces?

Telemetry Interface
Human and Agent Interaction Interface

## Coordination with other organisations

This work is closely related to work done in other organisations and bodies. This work effort will seek to take input from other experts while attempting to bring them together to coordinate on this issue.

Outreach should take place to at least:
- TMF ANP
- OpenGuardrails
- OpenTelemetry
- Harness Engineering


## Proponents

This is a list of people who contributed to the discussions that led to this work description. Draw no conclusions from the ordering of people in this list.
- Qin Wu <billwu@huawei.com>
- Qiufang Ma <maqiufang1@huawei.com>
- Daniele Ceccarelli <dceccare@cisco.com>
- Daniel King <d.king@lancaster.ac.uk>
- Adrian Farrel <adrian@olddog.co.uk>
- Luis M. Contreras <luismiguel.contrerasmurillo@telefonica.com>
- Laurent Ciavaglia <Laurent.Ciavaglia@nokia.com>
- Reza Rokui <rrokui@ciena.com>
- Benoit Claise <Benoit@everything-ops.net>

## Deliverables

**A list of deliverables will be added here**

## Relevant ICON Internet-Drafts

Several Internet-Drafts are directly related to the ICON work:

- "Problem Statement for Observability, Intervention and Control (I&C) in Multi-Agent Autonomous Networks" <https://datatracker.ietf.org/doc/draft-wnd-opsawg-icon-ps/>
- "Architecture and Requirements for Observability, Control and Intervention of Network Management Agents" <https://datatracker.ietf.org/doc/draft-mcw-opsawg-icon-requirements/>

## Related Internet-Drafts or Documents

This section lists related Internet-Drafts, and work that is relevant to the ICON scope:

- "Network Digital Twin and Agentic AI based Architecture for AI driven Network Operations" <https://datatracker.ietf.org/doc/draft-wmz-nmrg-agent-ndt-arch/>
- "Use of Natural Language for Agent Communication" <https://datatracker.ietf.org/doc/draft-verma-dmsc-nlip-notes/>
- "Agentic AI Architectural Principles for Autonomous Computer Networks" <https://datatracker.ietf.org/doc/draft-jadoon-nmrg-agentic-ai-autonomous-networks/>
- "IG1548 Intervention and Control for Agentic Operation V1.0.0 DRAFT" <https://projects.tmforum.org/wiki/pages/viewpage.action?pageId=411641744>
- "IG1251G IP Network AN Level 4 Agentic Architecture for Multi-Scenario Autonomy" <https://projects.tmforum.org/wiki/pages/viewpage.action?pageId=401824956>
- ITU-T Focus Group on Artificial Intelligence Native for Telecommunication Networks (FG-AINN) working documents as liaised to the IETF at <https://datatracker.ietf.org/liaison/2277/>
