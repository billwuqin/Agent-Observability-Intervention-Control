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

# How ICON is different from AUDIT?

Based on its defined charter and design constraints, AUDIT more focuses on
post event audit record and evidence exchange and verification. However AUDIT
cannot provide comprehensive operational control or real-time risk mitigation
within autonomous network environments. The gaps include but not limite to:

   *  Post-mortem Rather than Pre-Event Interceptive Control

   *  Absence of In-Event Active State Recovery & Rollback

   *  Exclusion of Internal Reasoning Evaluation

# Do we need a dedicated mailing list for ICON?
Yes, A Dedicated Mailing List is required for "Agent Observability, Intervention and Control"
The current discussion is on the AINETOPS mailing list <ainetops@ietf.org>

# Hackathon implementations

- [AgentOps observability and failure diagnosis prototype](<Hackathon/IETF 127/running code/agentops/README.md>): runtime measurements, normalized trajectories, anomaly detection, evidence-based attribution, reproducible scenarios and tests.
