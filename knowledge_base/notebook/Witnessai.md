Licenses by user and by chatbot. Enterprises can license to have visibility (discover) or license to have control (guardrails).




Applications, internal chatbot for employees to use, azure open ai or other
	External facing chatbots
	
	
Model protection and prompt injection
	Guard rails around model identity protection - behaving in the way you expect
	
	
"who's the best car provider?" - twitter embarrassment

Thick clients 
Browser based
	Visibility into the apps
		Notion.ai
Discovery - how are people using AI?
	Who's using these projects and what the risk on the data
	
	
Visibility into the endpoint - beta 
	June of last year and GA in October 2024
	
A lot of orgs are wanting to know how users are using public models 
Visibility on the local machine > looking into 
	Today witness is agentless; 
	
	
	Architecture :
		Proxy chaining
			Integrate with palo on prem URL filtering
			Netskope, Zscaler
			
	Config on the endpoint to collect the telemetry with Crowdstrike (RTR?)
	
	Flexibility with deployment
		Leverage existing tools, proxy chaining and only visibility into AI traffic they are interested in
		
	190,000 employees Opp  - enterprise ready and scalable
		Zscaler to proxy chaining
		2700 employees - deployment in under and hour
		
		
	Architecture side - deploy in AWS 
		Any region 
			BYO keys 
		Single tenant instance - dedicated to customer
			Isolated for just their instance
			
	_______________________________________________________
	
	
	Data protection - guardrail > evolving this guardrail to be more context aware
		Not looking at data labels today
			
			
	Understand the intention behind the prompt 
	Re-route data based on intention to internal model 
	
	Co-pilot 
		Data leakage > instead of finding out everything you have access to 
		
	Runtime - airlines
		Use case : anytime we see an employee use 3rd apps
			Don’t want AI to give answers for proprietary info 
				Re-route to internal LLM based on intent
				
	Ability to control the topics and how the employees are interacting with the LLMs
	
	
	Integrate with directory services - narrow down to HR groups, etc
		Looks at the dashboard for each 
		
	Discovery : 
		- On the network layer - can block high risk AI apps
	- Block some sort of splash page - custom
	
	Can leverage through endpoint - can block on domain level 
		With palo firewall (URL filtering)
		
	- Can block and approve apps 
		- 
Policies: Not keywords - looking at intent
	
	
	- Data protection
		- Tokenize the data (all ssn numbers0
			§ When it comes back - gives numbers back to user
			§ No sensitive data goes to LLM
				□ Protect the company and allows the customer to use the AI
		- Redacted data 


Harmful responses (beta)
Co-pilot
	If someone over permissioned docs - 
	
	
	
	
	At the network layer - will work with the MS apps as well
		Where's the user accessing?
		
		
	
		Apply warns/blocks by group
		
		
		
	
_____________________________________________


Not  a browser extension - will do the proxy chaining /config on the endpoint
	Browser related activity 
		Vs code 
		

Discovery - discover any AI app out there
	4000 apps today
	
	Will give a list of users that are accessing and then block in the platform as well
	Block page - customizable
	
	Deeper - policies : guardrails 
		Different types of guardrails for flexible and granular groups going to different destinations
		
	If they are attempting to put PII / ChatGPT > can tokenize data as its going out
		
	


Witness - going to be the prompts
	Will be multi -modal - file uploads
		
		
API first - browser, thick client, chatbot
	All API based
		Doesn’t matter on the app or on the chatbot
		Same protections 
		
	When data makes it into their chatbot, they want to make sure that the sensitive data doesn't go into their own LLM
	Not processing sensitive data
	
	Routing and re-directing 
		Witness is re-route the prompt the any llm that they are integrated with 
		
		
		Others - block access to ChatGPT and re-direct to a pre-approved 
			Witness is re-direct based on the intent of the prompt, not just al up blocking
			
		
	
	Development (2 ways):
		1. Wrapper API - prompts and responses go through Witness
			Check it, send to LLM and send it back
		
	2. Input API
		Complete API
			Send input prompt to witness > score it and send scoring back to internal app
			Then you decide if it gets sent back to the LLM
			Then call complete API call to assess the response from the LLM and back to the LLM
			

	Can monitor conversations through API as well in the UI
	Same guardrails
		Monitoring harmful responses
		
	
	Shows efficacy and testing model against other tools
		Testing is at 97% 
		
	
	Mostly on usage - no model scanning
	
	Fairly easy  for deployment
		Just sending the prompt to us 
			Everything on the customer side is the same
				Just checking the response for you
				Just a checker
				
	
	In AWS - can be installed in any AWS region
		Private cloud - in own AWS VPC
			Protect source code <> language in the contract for witness safeguards
				Needs access for patches/updates to VPC - doesn’t advertise
				
	Mostly SaaS solution
	
	No red teaming yet - looking into it
	
	Compliance > 
	- Discovery
	- Compliance guardrails are coming
		○ Starting with PCI
		○ Use the product the way it is - behavioral guardrails for compliance
		○ Make sure prompts are re-routed to internal
			§ Ensuring the answers are what you are supposed to be getting



Spotlight - service
	How many shadow AI apps are there 
		What does that look like
		
	
		
	Ai assessment - visibility into proxy logs
		What AI services that discover in a shorter report
		Export from SIEM, proxy logs
		User, time and domain 
		
		
		Free assessment you can run or run for them
		
		
	For Cisco, since Cisco Umbrella doesn't support proxy chaining, we would deploy using our Witness Anywhere deployment method.
	 
	Witness Anywhere can be deployed using Crowdstrike, SentinelOne, Windows GPO, Intune, or JAMF. WIth this method, we are able to deploy Witness Anywhere, which is a proxy configuration script for the endpoints, allowing us to configure the endpoints to send AI traffic to the customer's WitnessAI tenant.    >>>>>via PAC Fille>>>>>>
	
	
	
	
	___________________________________________________
	Updates 3/30/26
	
	SOC II Compliant
	Not iso 27001 compliant
		Fedramp is next on the docket
		
	