# Challenge

## 4. Agent for Assessing ICT Systems for DISP/IRAP Accreditation
An AI agent that reviews ICT system configurations and documentation, compares them against DISP/IRAP standards, and generates IRAP company policy document and compliance reports or remediation plans. Undertakes a preliminary IRAP assessment based on controls documentation. It helps organisations prepare for accreditation audits.
ISM and Policy documentation is provided, the exemplar tenancy is the ASD Secure Cloud Blueprint, which includes a repository for further config information GitHub - ASD-Blueprint/ASD-Blueprint-for-Secure-Cloud: Website for ASD's Blueprint for Secure Cloud
Engineering Goal: Build a tool that can assess a system’s compliance and generate a remediation plan within 1 hour.

## Scenario Description:
This scenario is about providing an Agent based analysis of an existing tenancy or infrastructure, company documentation to conduct a pre-qualification IRAP assessment. Where documentation doesn’t current exist, the agent should produce draft documentation based on best practice.

The agent should then be able to interrogate the current system, documentation and regulatory framework to enable the user to interrogate policy and be provided guidance.
### Team Process Guidance:
• Ingest DISP/IRAP standards and map them to system configurations.
• Create a checklist and scoring system.
• Use telemetry data to assess real-time compliance.
• Output must enable the analysis to be validated with security and compliance experts.

Azure Services:
• Azure Policy – to enforce and assess compliance.
• Azure Security Center – for security posture evaluation.
• Azure OpenAI Service – to interpret standards and generate reports.
• Azure AI Studio – for developing the agent.
• Azure AI Foundry – for more granularity in processing document.
• Azure Defender for Cloud – to assess infrastructure security.
• Azure Monitor – for system telemetry and audit trails.
• Azure Migrate – to map existing systems structure and applications

# ASD Blueprint Desired State Configuration files

https://github.com/ASD-Blueprint/ASD-Blueprint-for-Secure-Cloud/tree/main/static/content/files/automation/dsc
https://github.com/ASD-Blueprint/ASD-Blueprint-for-Secure-Cloud/tree/main/static/content/files/configscripts
https://github.com/ASD-Blueprint/ASD-Blueprint-for-Secure-Cloud/tree/main/static/content/files/intune-config-policies

# Useful Files

https://github.com/ASD-Blueprint/ASD-Blueprint-for-Secure-Cloud/blob/main/static/content/files/Blueprint%20System%20Security%20Plan%20Annex%20Template%20(June%202025).xlsx

./Information Security Controls and Policy/Implementing a Governance Compliance Tool with Microsoft Graph and Essential Eight 

# Useful Websites

https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/essential-eight/essential-eight-maturity-model

https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/essential-eight/essential-eight-maturity-model-ism-mapping




