"""
ISM Control Assessment Tool

This module provides functionality to assess Information Security Manual (ISM) controls
against a set of Microsoft 365 DSC policies using Autogen & OpenAI's LLM capabilities.

The tool analyzes policy compliance and provides implementation status along with
relevant policy matches.

Requirements:
    - Python 3.8+
    - UV package manager for dependency management
    - OpenAI API key set in environment variable OPENAI_API_KEY

Setup:
    1. Create virtual environment: uv venv
    2. Activate: source .venv/bin/activate
    3. Install deps: uv pip install -r pyproject.toml

Implementation Statuses:
    - Not Assessed: Control has not yet been evaluated or reviewed.
    - Effective: Control is fully implemented and meets its objective.
    - Alternate Control: A different control is implemented that meets or exceeds the original intent.
    - Not Implemented: Control is absent; no measures have been taken.
    - Partially Implemented: Some components are in place, but full compliance is not achieved.
    - Ineffective: Control exists but fails to meet its intended purpose or mitigate the associated risk.
    - Technically Unfeasible: Control cannot be implemented due to platform limitations or constraints.
    - No Visibility: Unable to verify implementation due to lack of evidence or access.
    - Not Applicable: Control is irrelevant to the system’s scope or architecture.
"""

import asyncio
import os
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from pydantic import BaseModel
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage

@dataclass
class Policy:
    name: str
    description: str
    settings: Dict[str, str]


class AgentResponseJSON(BaseModel):
    """Structured response format for the security assessment agent."""
    status: str
    relevant_policies: List[str]
    explanation: str

    class Config:
        """Pydantic model configuration."""
        allow_extra = False  # Prevent additional fields
        
    @property
    def is_valid_status(self) -> bool:
        """Check if status is one of the valid implementation statuses."""
        valid_statuses = [
            "Not Assessed", "Effective", "Alternate control",
            "not implemented", "implemented", "partial", "ineffective",
            "no usability", "not applicable"
        ]
        return self.status in valid_statuses

class ISMControlAssessor:
    def __init__(self, policy_file_path: str, api_key: Optional[str] = None,
                 azure_endpoint: Optional[str] = None,
                 azure_deployment: Optional[str] = "gpt-5-mini"):
        """
        Initialize the ISM Control Assessor.
        
        Args:
            policy_file_path: Path to the DSC policy file
            api_key: Optional API key for Azure OpenAI. If not provided, will use OPENAI_API_KEY env var
            azure_endpoint: Optional Azure OpenAI endpoint. If not provided, will use default
            azure_deployment: Optional Azure deployment name. Defaults to gpt-5-mini
            
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.policy_file_path = policy_file_path
        self.implementation_statuses = [
            "Not Assessed", "Effective", "Alternate control", 
            "not implemented", "implemented", "ineffective", 
            "no usability", "not applicable"
        ]
        self.model_client: Optional[AzureOpenAIChatCompletionClient] = None
        self.agent: Optional[AssistantAgent] = None
        self.policies: str = ""
        
        # Get configuration from parameters or environment
        self._api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self._api_key:
            raise ValueError("API key must be provided either through constructor or OPENAI_API_KEY environment variable")
            
        self._azure_endpoint = azure_endpoint or os.getenv('AZURE_OPENAI_ENDPOINT') or "https://aihac-mfbwdeld-eastus2.cognitiveservices.azure.com/"
        self._azure_deployment = azure_deployment
        
        # Load policies immediately
        self.load_policies()
        
    async def initialize(self):
        """Initialize the assessor asynchronously."""
        try:
            
            # Initialize Azure OpenAI client
            if not self._api_key:
                raise ValueError("API key is required")
            
            if not self._azure_deployment:
                raise ValueError("Azure deployment name is required")
                
            if not self._azure_endpoint:
                raise ValueError("Azure endpoint is required")
                
            self.model_client = AzureOpenAIChatCompletionClient(
                azure_deployment=str(self._azure_deployment),
                model=str(self._azure_deployment),
                api_version="2024-12-01-preview",
                azure_endpoint=str(self._azure_endpoint),
                api_key=str(self._api_key),
                temperature=1, 
            )
            
            # Initialize the agent with a refined system prompt for ISM/E8 and LLM best practices
            self.agent = AssistantAgent(
                name="security_assessor",
                model_client=self.model_client,
                system_message=(
                    "You are an expert in the Australian Government Information Security Manual (ISM) and Essential Eight (E8) cybersecurity controls, with deep knowledge of securing Microsoft 365 tenancies to meet ISM requirements and Essential Eight maturity levels. \n"
                    "Your task is to: \n"
                    "- Assume that all non entra related controls are effective. \n"
                    "- Evaluate whether the provided Entra desired state configuration read from a tenancy is effective in achieving the specified ISM control, referencing the latest ISM (September 2025) and ASD Blueprint for Secure Cloud examples. \n"
                    "- Identify and cite relevant policy settings, mapping them to ISM and Essential Eight requirements. \n"
                    "- Clearly state the implementation status using only the allowed values: ['Not Assessed', 'Effective', 'Alternate Control', 'Not Implemented', 'Partially Implemented', 'Ineffective', 'Technically Unfeasible', 'No Visibility', 'Not Applicable']. \n"
                    "- Provide a concise, evidence-based explanation, referencing ISM control identifiers and policy titles. Highlight any gaps, partial coverage, or implementation risks. \n"
                    "- Where applicable, suggest improvements or additional controls to achieve full compliance or higher maturity. \n"
                    "- Always respond in the required JSON format. Do not include any text outside the JSON block. \n"
                ),
                model_client_stream=True,
                output_content_type=AgentResponseJSON,  
            )
            
        except Exception as e:
            await self.cleanup()
            raise RuntimeError(f"Failed to initialize Azure OpenAI connection: {str(e)}")
            
    async def cleanup(self):
        """Cleanup resources."""
        if self.model_client:
            try:
                await self.model_client.close()
            except Exception:
                pass  # Best effort cleanup

    def load_policies(self) -> None:
        """Load policies from the policy file.
        
        Raises:
            RuntimeError: If policy file cannot be loaded
        """
        try:
            with open(self.policy_file_path, 'r', encoding='utf-16') as f:
                self.policies = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to load policy file: {str(e)}")


    async def assess_control(self, ism_title: str, ism_description: str) -> Tuple[str, List[str], str]:
        """
        Assess if an ISM control is being met by the policies using LLM.
        
        Args:
            ism_title: The title of the ISM control to assess
            ism_description: The description of the control requirements
            
        Returns:
            Tuple[str, List[str]]: A tuple containing:
                - implementation status (one of the predefined statuses)
                - list of relevant policy names that address the control
                
        Raises:
            ValueError: If the LLM response is not in the expected format
            RuntimeError: If the assessor hasn't been initialized
        """
        if not self.agent or not self.model_client:
            raise RuntimeError("Assessor not initialized. Call initialize() first")
                    
        if not self.policies:
            return "Not Assessed", [], "No policies available for assessment."

        # Build a refined prompt for ISM/E8, referencing ISM/ASD Blueprint, and requiring actionable, evidence-based, improvement-suggesting responses
        prompt = f"""
        
        You are an expert in ISM (Information Security Manual) and Essential Eight (E8) controls, specialising in evaluating whether assigned Microsoft 365 policies meet ISM control requirements and Essential Eight maturity expectations.

        Task: Assuming all non entraID controls are implemented and are satisfactory to ISM and E8, does this entraID report from powershell desired state configuration meet the following ISM control? Does the provided entraId desired state configuration report Effective, Partially Effective, or Ineffective in implementing the the provided Information Security Manual control? Use the latest ISM (September 2025) and ASD Blueprint for Secure Cloud as references.

        Information Security Manual (ISM) Control:
        Title: {ism_title}
        Description: {ism_description}

        Allowed Implementation Statuses:
        - Not Assessed: Control has not yet been evaluated or reviewed.
        - Effective: Control is fully implemented and meets its objective.
        - Alternate Control: A different control is implemented that meets or exceeds the original intent.
        - Not Implemented: Control is absent; no measures have been taken.
        - Partially Implemented: Some components are in place, but full compliance is not achieved.
        - Ineffective: Control exists but fails to meet its intended purpose or mitigate the associated risk.
        - Technically Unfeasible: Control cannot be implemented due to platform limitations or constraints.
        - No Visibility: Unable to verify implementation due to lack of evidence or access.
        - Not Applicable: Control is irrelevant to the system’s scope or architecture.

        EntraID Desired State Configuration policies:\n{self.policies}\n\n

        Assessment Criteria:
        1. If this ISM control is not related to entra, then assess the control as Effective and detail the relevant policies and controls and complete the task.
        2. If all non entra related controls are assumed effective, does the provided entra desired state configuration effectively address the provided ISM control requirements? Reference specific policy settings and control IDs.
        3. If all non entra related controls are assumed effective, is the implementation effective and actionable? Use ISM/E8 terminology and note any maturity level achieved.
        4. If all non entra related controls are assumed effective, are there any gaps or partial implementations? Suggest improvements if needed.
        5. Cite relevant policy titles and settings.

        Respond ONLY in this JSON format:
        {{
        "status": "One of: Not Assessed, Effective, Alternate Control, Not Implemented, Partially Implemented, Ineffective, Technically Unfeasible, No Visibility, Not Applicable",
        "relevant_policies": ["List of policy titles/settings that address this control"],
        "explanation": "Concise, evidence-based reasoning. Reference ISM/E8 language, control IDs, and policy names. Include maturity level context and improvement suggestions if gaps exist."
        }}

        References:
        - ISM Manual (September 2025): https://www.cyber.gov.au/sites/default/files/2025-09/Information%20security%20manual%20%28September%202025%29.pdf
        - ASD Blueprint: https://github.com/ASD-Blueprint/ASD-Blueprint-for-Secure-Cloud/tree/main
        """
        
        parsed_response = AgentResponseJSON(status="Not Assessed", relevant_policies=[], explanation="No response")
        try:
            print("Debug: Starting to process agent response stream")
            # Await the streamed response from the agent
            final_response = await asyncio.create_task(
                self.agent.on_messages([TextMessage(content=prompt, source="user")],cancellation_token=CancellationToken())
            )
            # If final_response is a Response object, get the chat_message/content
            if hasattr(final_response, "chat_message"):
                content = dict(dict(final_response.chat_message)["content"])
                if isinstance(content, dict):
                    parsed_response = AgentResponseJSON(**content)
                elif isinstance(content, str):
                    parsed_response = AgentResponseJSON.model_validate_json(content)
                else:
                    pass
            else:
                pass

            return parsed_response.status, parsed_response.relevant_policies, parsed_response.explanation
        except json.JSONDecodeError:
            print("JSON decode error")
            return "Not Assessed", [], ""
        except (ValueError, KeyError) as e:
            print(f"Invalid LLM response format: {e}")
            return "Not Assessed", [], ""
        except Exception as e:
            print(f"Error during LLM assessment: {str(e)}")
            return "Not Assessed", [], ""

async def assess_ism_control(
    ism_title: str, 
    ism_description: str, 
    policy_file: str = "asdbpsc-dsc-entra.txt"
) -> Tuple[str, List[str], str]:
    """
    Main function to assess an ISM control against policies.
    
    Args:
        ism_title: The title of the ISM control
        ism_description: The description of the ISM control
        policy_file: Path to the policy file (default: asdbpsc-dsc-entra.txt)
        
    Returns:
        Tuple containing:
        - implementation status
        - list of relevant policies
    
    Raises:
        RuntimeError: If initialization fails
    """
    Model = "gpt-5-mini"
    try:
        assessor = ISMControlAssessor(policy_file,azure_deployment=Model)
        await assessor.initialize()
        
        try:
            return await assessor.assess_control(ism_title, ism_description)
        finally:
            await assessor.cleanup()
    except Exception as e:
        print(f"Failed to assess ISM control: {str(e)}")
        return "Not Assessed", [], ""

def run_assessment(
    ism_title: str, 
    ism_description: str, 
    policy_file: str = "asdbpsc-dsc-entra.txt"
) -> Tuple[str, List[str], str]:
    """
    Synchronous wrapper for assess_ism_control.
    
    Args:
        ism_title: The title of the ISM control
        ism_description: The description of the ISM control
        policy_file: Path to the policy file
        
    Returns:
        Tuple containing:
        - implementation status
        - list of relevant policies
    """
    return asyncio.run(assess_ism_control(ism_title, ism_description, policy_file))

