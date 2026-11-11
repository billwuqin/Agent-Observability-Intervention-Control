-   What is ICON
    ICON focuses on addressing non deterministic behaivor exhibiting by AI Agent,
    -	it is built on top of continuous observability of AI agent behavior;
    -	introduce the ability of human operators to intervene when an agent goes wrong (e.g., task
      suspension, rollback to a last known safe state, or termination),
   -	and enable the control of what an agent is permitted to do before and during action execution.

-   How we are negotiating with AINETOPS on the division of the topics

   -	AINETOPS and ICON focus on different use case, take different architecture, use different protocol, data model, AINETOPS is more YANG data model specific while ICON is not.

         ICON focus on defining generic building blocks including
         1) Agent observability Data model (Not YANG based)
         2) Agent intervention protocol  (Application Protocol)
         3)and Agent control protocol (Application protocol)
         which can be applied to various different use cases, not limited to network management cases.

   -  ICON focus on defining generic building blocks including
      1) Agent observability Data model (Not YANG based)
      2) Agent intervention protocol  (Application Protocol)
      3)and Agent control protocol (Application protocol)
        which can be applied to various different use cases, not limited to network management cases.   
  -	  AINETOPS can be one of use cases which consume ICON building block. 
      1) It can be built on top of building blocks developed by ICON
      2) and focus on network management specific use cases, e.g.,
        - task management protocol and data model
        - Agent lifecycle
         
   -	but AINETOPS focused task management targets to intent close loop 
      1) while ICON focused agent intervention and control target to
         different agent governance close loop separately, two close loop can be decoupled.

  -	 AINETOPS focused task management can work without ICON developed building block.

-   Objective of ICON follow up meeting:
    1). Reach agreement on ICON work description scope and key work items
    2). Have sufficient supports for ICON
         
-   How you hope to work toward a BoF at IETF-128
    1). Kick off mailing list discussion on key discussion points
    2).Create a separate ICON mailing list
    3). Set up a weekly call to cook Charter Proposal and BOF proposal
         
-   Pointers to relevant work (I-Ds, draft charter, side meeting materials)
    I-Ds:
    - ICON Problem Statement: draft-wnd-opsawg-icon-ps
    - ICON Requirement: draft-mcw-opsawg-icon-requirements
    - ICON Solution Related: draft-pei-opsawg-agentops-observability
   Draft charter:
    - https://github.com/billwuqin/Agent-Observability-Intervention-Control/blob/main/ICON-Work-Description.md
   Side meeting materials:
    - https://github.com/billwuqin/Agent-Observability-Intervention-Control/tree/main/presentation/IETF%20127
