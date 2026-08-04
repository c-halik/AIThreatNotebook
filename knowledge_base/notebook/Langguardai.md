Discovery and control plane

Provision and see it, monitor later as well


Manage he assets and use policies to send to tools to orchestrate the policies

This agent can not move to prod because it hasn’t 


Orchestration effort and work with existing toolsets


Webhooks today

Collect through observe data - 
Wiz, zscaler, crowdstrike, 
	For assets seen on that 
Open telemetry for observe data
	
	OPA policy and context forge
	
	
Tool calls, RAG calls, vector data bases

Deep context of what the model call is 
	Apply a policy to it and look at 



Every run is captured into a database

Are these approved data sources and tools?

Enriching deep telemetry 



__________________________________________

Arbitur - human in the loop controls via the security tool ***
	Last mile 
		After all the reasoning is done
			I'm going to delete the database, 
				Block you or give back to human control
				
	Pre reasoning - guardrails, check
	Post reasoning - when they are actually doing something
		Classify actions across more than 300 MCPs
		
	Early traction
	
	

Llm guardrails - 
	Using policy as code - deterministic policies to help bypassing the guardrails
	
	Workflow policies - check the workflow lifecycle to map to config policy
	
	Eval step or set it up to 
	
	
	Set up budget policies at the workflow level to block token at a certain threshold
	
	
	
	Set up a policy to stop agents approving own uses
	
	Ai code policy generation
	
	Policy library - to import to check for the agent reaching out to malicious domain, etc
	
	3 use cases - cost : token maxxing
	2. Guardrails of agents - excessive agency, over priv agents
Compliance focused - touching fin systems
	Confident that the agents are not going to change fin 
		Audit logs, sox compliance
		
		
		

	Use case: 
		Controller has copilot and quickbooks 
			Builds an agent with their creds for quickbooks to do email, etc
				Langguard its in the middle
				
				
	Google: 
		- No template to set policies
			§ You should not use prod data
				□ Up to the between google and the data
	

MCP 
	Exposing MCP from internal to 3rd parties
		- Their agents wanting data from the 3rd party
			§ Just give me a 
		- Langguard in between from external to internal access
	Exposing mcp 
		
	
	
	Arbiter is the enforcer -0 inside the gateway 
		Claude code is 
		
		Dist policy enforcement layer - as a plug in 
	
	
