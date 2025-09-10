"""
ISM Control Assessment Tool

This module provides functionality to assess Information Security Manual (ISM) controls
against a set of Microsoft 365 DSC policies using OpenAI's LLM capabilities.

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
    - Not Assessed: Control has not yet been evaluated or reviewed for applicability or effectiveness.
    - Fully Implemented: Control is completely in place and operating effectively as intended.
    - Alternate Control: A different control is implemented that meets the intent and risk mitigation of the original.
    - Not Implemented: Control is absent; no measures have been taken to address the requirement.
    - Implemented (Needs Review): Control is in place but requires validation, testing, or periodic reassessment.
    - Partially Implemented: Some components of the control are in place, but full compliance is not achieved.
    - Ineffective Control: Control exists but fails to meet its intended purpose or mitigate the associated risk.
    - Technically Unfeasible: Control cannot be implemented due to system limitations, incompatibility, or other constraints.
    - Not Applicable: Control is irrelevant to the system's scope, architecture, or operational context.
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
                    "You are an expert in Australian Government Information Security Manual (ISM) and Essential Eight (E8) controls, "
                    "with deep knowledge of secure a microsoft tendancy to essential 8 level.\n"
                    "Your task is to:\n"
                    "- Evaluate if provided policies fully and effectively implement the specified ISM control, referencing the latest ISM (September 2025) and ASD Blueprint examples.\n"
                    "- Identify and cite relevant policy settings, mapping them to ISM/E8 requirements.\n"
                    "- Clearly state the implementation status using only the allowed statuses: [\"Not Assessed\", \"Effective\", \"Alternate control\", \"Not implemented\", \"Implemented\", \"Partial\", \"Ineffective\", \"No usability\", \"Not applicable\"].\n"
                    "- Provide a concise, evidence-based explanation, highlighting any gaps or partial coverage.\n"
                    "- If possible, suggest improvements or additional controls for full compliance.\n"
                    "Always respond in the required JSON format."
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
        You are an expert in ISM (Information Security Manual) and Essential Eight (E8) controls, specializing evaluating assigned policies and if they meet E8 criteria.\n\n
        
        Task: Assess whether the following ISM control is fully, partially, or not implemented by the provided policies. Use the latest ISM (September 2025) and ASD Blueprint for Secure Cloud as references.\n\n
        
        ISM Control:\nTitle: {ism_title}\nDescription: {ism_description}\n\n
        
        ISM Implementation Statuses:
            - Not Assessed: Control has not yet been evaluated or reviewed for applicability or effectiveness.
            - Fully Implemented: Control is completely in place and operating effectively as intended.
            - Alternate Control: A different control is implemented that meets the intent and risk mitigation of the original.
            - Not Implemented: Control is absent; no measures have been taken to address the requirement.
            - Implemented (Needs Review): Control is in place but requires validation, testing, or periodic reassessment.
            - Partially Implemented: Some components of the control are in place, but full compliance is not achieved.
            - Ineffective Control: Control exists but fails to meet its intended purpose or mitigate the associated risk.
            - Technically Unfeasible: Control cannot be implemented due to system limitations, incompatibility, or other constraints.
            - Not Applicable: Control is irrelevant to the system's scope, architecture, or operational context.
        
        Available Policies:\n{self.policies}\n\n
        
        Assessment Criteria:\n1. Does the policy fully address the ISM control requirements? Reference specific policy settings.\n2. Is the implementation effective and actionable? Use ISM/E8 terminology.\n3. Are there any gaps or partial implementations? Suggest improvements if needed.\n4. Cite relevant policy titles and settings.\n\n
        Respond ONLY in this JSON format:\n{{\n    "status": "One of: Not Assessed, Effective, Alternate control, Not implemented, Implemented, Partial, Ineffective, No usability, Not applicable",\n    "relevant_policies": ["List of policy titles/settings that address this control"],\n    "explanation": "Concise, evidence-based reasoning. Reference ISM/E8 language. Suggest improvements if gaps exist."\n}}\n\n
        References:\n- ISM Manual (September 2025): https://www.cyber.gov.au/sites/default/files/2025-09/Information%20security%20manual%20%28September%202025%29.pdf\n- ASD Blueprint: https://github.com/ASD-Blueprint/ASD-Blueprint-for-Secure-Cloud/tree/main
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

