6.1.  Network Active Assurance with Network AI Agent and AI Guardrail Support

   Network active and reactive assurance, both at the single- layer (IP
   or Optical) and multi-layer (IP over Optical), are critical
   components in maintaining the health and stability of modern IP,
   Optical, and IPoDWDM networks.  This process involves the
   identification and resolution of network issues as they arise,
   ensuring that any disruptions or degradations are promptly addressed.
   By employing AINetOps techniques, network engineers can quickly
   pinpoint the root cause of problems, whether they originate in the IP
   layer, the optical layer, or across both.  This reactive approach is
   essential for minimizing downtime and maintaining the quality of
   service expected by network users.

   In single-layer troubleshooting, the focus is on isolating and
   resolving issues within a specific layer of the network.  Multi-layer
   troubleshooting, on the other hand, requires a more integrated
   approach, as it involves identifying and resolving issues that span
   across multiple layers of the network.  This could include problems
   where an issue in the optical layer affects the IP layer.

   In active assurance, network faults have already occurred.  These
   faults may include impairments such as optical fiber
   cuts, IP packet drops, IP link latency issues, or Threshold Crossing
   Alarms (TCA), among others.

   As illustrated in Figure 3, active assurance assumes that a fault
   occurs in the IP/Optical network (Step A) and is subsequently
   detected automatically by higher-layer controllers (Step B). These
   controllers may employ detection methods that include monitoring
   alarms, analyzing performance telemetry data, or processing customer
   reports indicating service disruptions. To initiate troubleshooting,
   the detection logic launches the AIOps-Assistant, which serves as the
   front-end interface for AINetOps (Step C).  The assistant then utilizes
   the backend assurance and troubleshooting mechanisms, leveraging a
   Gen-AI multi-agent framework.  In Step D, a dynamic workflow is executed
   to diagnose the issue and identify potential root causes.  Optionally,
   at Step E, the Gen-AI dynamic workflow can recommend remedial actions
   to resolve the issue and implement these actions in a closed-loop fashion,
   ensuring automated network recovery. In Step F, higher-layer controllers
   as Agent Fabric Gateway Collect log, trace, metric information and report
   them to the Observabiltiy process to establish Agent behavior visibility.
   In step G, these information will be further fed into evaluation process
   to operational anomalies or performance drifts.

	|------------|   |-------------------|
	|    AIOps   |(C)|  Domain Specific  | (I)|------------|
	| Assistant  +--->  Network Agent    <----+AI Guardrail|
	|-----^------|   |    (D)            |    | Assistant  |
	   |             |-------------------|    |---^--------|
	   |                    |                     |(H)
	   |                    |               |-----+------|
	   |                    |               | Evaluation |
	   |                    |(E)            | Process    |
	   | (B)                |               |-----^------|
	   |                    |                     |(G)
	   |            |-------v-------|             |
	   |            |   P-PNC(s),   |  (F)  |-----+-----|
	   +------------+   O-PNC(s),   |------>Observabiltiy
					|   MDSC        |       | Process   |
					|---------------|       |-----------|
						(A) ^
							|
				  +---------+-----------+
				  |                     |
				  |  IP/Optical Network |
				  |                     |
				  +---------------------+


     Legend:
     (A) A fault happened in the network
         (e.g., Fiber cut, IP packet drop, TCA crossing etc.)
     (B) The higher layer Controller notifies Operator
     (C) To start troubleshooting, AIOps-Assistant starts automatically
     (D) Start troubleshooting using Gen-AI multi-agent dynamic workflow
     (E) Optional remedial actions
	 (F) Telemetry for agent behavior visibility
	 (G) Evaluate operational anomalies or performance drifts
	 (H) The Agent management plane notifies Human Operator 
	 (I) The human Operator uses AI guardrail Assistant to intervene or control Network Agent.

  Figure 4: Multi-layer Active Assurance Using Network Agent and AI Guardrail
  
6.2.   Network Anomaly Detection with AI Guardrail Support

   Network anomaly detection is a critical component of modern network
   security and management, aimed at identifying deviations from normal
   network behavior that may indicate potential threats or operational
   issues.  With the increasing complexity of networks and the growing
   sophistication of cyber threats, traditional rule-based detection
   methods are often insufficient.  The integration of machine learning techniques
   into network anomaly detection system offers a more
   dynamic and adaptive approach to detecting anomalies in real-time.
   
   The lifecycle of a network anomaly can be articulated in three
   stages, structured as a loop: Detection, Validation, Refinement.
   The Network Anomaly Detection stage is performed by the Agent while
   Network Anomaly Validation and refinement is performed by Agent
   Observability module and AI Guardrail Assistant. The Network Anomaly
   Detection stage is about the continuous monitoring of the network
   through Network Telemetry {{?RFC9232}} and the identification of Symptoms.
   The key objective for the validation and refinement stage is clearly to decide if
   the detected Symptoms are signaling a real problem (a.k.a. requires
   action) or if they are to be treated as false positives (a.k.a.
   suppressing the alarm),perform detailed postmortem analysis of Problems
   with the objective to identify useful adjustments to the prevention and detection
   mechanisms.
   
   After the adjustments are generated, it will be sent to AI Guardrail  Assistant and
   the AI Guardrail  Assistant apply adjustments to the Network Anomaly Detection Agent,
   the cycle starts again. Alternatively,  Any remediation action flagged as "high-impact"
   by the Network Anomaly Detection Agent is put into a correction queue and escalated to
   AI Guardrail Assistant, requiring manual administrative approval via an external management
   console before execution.
   
   If consecutive-point monitoring in the Agent Observability Module flags that the AI baseline
   has drifted or been poisoned by bad telemetry, the AI guardrail can switch the network back to
   traditional, static threshold-based detection.


+----------------------------+
|     Agent Observability    |(D)Optimization
|+----------+   +----------+ |
||  Network |   | Network  | |       +------------+
||  Anomaly +---> Anomaly  |<+------->AI Guardrail|
||Validation|   |Refinement| |       | Assistant  |
|+-----^----+   +----------+ |       +----^-------+
+------+---------------------+            |
       |                                (E)Invention&
       |(C)Evaluation                     |  Control
       |  &Refinement    +----------------V--+
       +-----------------+                   |
                         |  Network Anomaly (B)Network Policy
           |----------->|  Detection Agent  |------------|
           | A)Network  |                   |            |
           | Telemetry  +-------------------+            |
           |                                             |
+----------+---------------------------------------------+--------+
| +--------|----------+       MCP Server      +----------|------+ |
| |                   |                       |                 | |
| |  Data Collection  |                       |    Response     | |
| |      Layer        |<------|       |-------|      Layer      | |
| |                   |       |       |       |                 | |
| +-------------------+       |       |       +-----------------+ |
+-----------------------------+-------+---------------------------+
            Southbound API    |       | Southbound API
 (NETCONF, IPFIX,BGP-LS, etc) |       v (NETCONF, PCEP, BGP, etc)
                      +-------------------+
                      |  Network Devices  |
                      | (Routers, Switches|
                      | Endpoints, etc.)  |
                      +-------------------+



     Legend:
     (A) Network Telemetry Information Collection
	 (B) Resolve the problem with the Network Policy
	 (C) Evaluate the network anomalies and identify useful adjustments
	 (D) Generate adjustments to the Network Anomaly Detection Agent
	 (E) AI Guardrail Assistant optimizes the Detection Agent based on Adjustment policy
	     or Detection Agent requests Human-in-the-Loop Escalation from AI Guardrail Assistant
		
    Figure 4: network anomaly detection optimization using AI Guardrail

6.3.  AI-Driven Policy Enforcement and Compliance Auditing using AI Guardrail

   This use case leverages Network Change AI Agent to automate the enforcement of network
   policies and auditing of compliance with regulatory standards,ethical, and organizational boundaries and
   internal guidelines.  By continuously monitoring network AI Agent Behavior, AI
   Guardrail ensures that policies are consistently applied and compliance requirements are
   met.  This use case addresses both single-layer (e.g., IP) and multi-
   layer (e.g., IP over optical) scenarios, as well as cross-domain
   environments.

   The AI Guardrail system analyzes real-time telemetry (e.g., trace, logs, metrics, audit information),
   historical data, and external inputs (e.g., regulatory updates, threat intelligence) to enforce
   policies and audit compliance.  For example, AI Guardrail can detect
   unauthorized changes to firewall rules, enforce encryption standards
   for sensitive data, or ensure that network configurations align with
   GDPR requirements. If violations are detected, AI Guardrail can automatically
   remediate issues or alert operators for manual intervention.
   
   AI Guardrails generally operate at three distinct operational levels to enforce
   policy and ensure :
   - Input Guardrails (Prompt Shielding)
      - Goal: Detect and block malicious user behavior from the intent request before it reaches the network AI Agent.
	  - Key Enforcements: Preventing prompt injections, filtering out Personally Identifiable Information (PII),
      	                  blocking hate speech, and stopping jailbreak attempts.
   - Output Guardrails (Response Validation)
     - Goal: Verify that the generated configurations or policy is accurate, compliant, and safe for the end-user.
	 - Key Enforcements: Preventing hallucinations (fact-checking against internal knowledge bases), blocking
    	                 toxic or biased outputs, and ensuring intellectual property (IP) compliance.
  - Continuous Auditing (Logging & Analytics)
     - Goal: Provide a transparent audit trail for compliance officers and regulators.
	 - Key Enforcements: Maintaining detailed logs of inputs, safety violations, system interventions, and Agent Behavior drift over time.
   
         +-----------+       +-------------+
         | Evaluation+-------> AI Guardrail|
         | Process   |       |  Assistant  |
         +-----------+       +-------------+

               ^                |
           (B) |                | (C)
               |                v
     |------------------------------------|
     |     Domain Specific Network        |
     | Policy Enforcement&Compliance Agent|
     |----------------^-------------------|
                   (A)|
  |-------------------v---------------------|
  |  packet controller (P-PNC),             |
  |  optical controller (O-PNC),            |
  |  and/or higher layer controllers (MDSC) |
  |-----------------------------------------|
                      ^
                 (A)  |
                      v
        |-----------------------------|
        |                             |
        |       IP/Optical Network    |
        |                             |
        |-----------------------------|

   Legend:
   (A) Policy enforcement commands (e.g., block traffic, adjust QoS)
   (B) Agent Observability Information Feedback
   (C) Compliance reports and alerts
   
   Figure 5: AI-Driven Policy Enforcement and Compliance Auditing using AI Guardrail
