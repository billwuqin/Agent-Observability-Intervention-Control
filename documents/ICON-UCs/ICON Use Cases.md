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
  
6.2   
  