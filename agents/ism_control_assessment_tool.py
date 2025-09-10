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
    - Not Assessed: Control has not been evaluated
    - Effective: Control is fully implemented and effective
    - Alternate control: Different but acceptable control is in place
    - Not implemented: Control is missing
    - Implemented: Control is in place but may need review
    - Ineffective: Control exists but doesn't meet requirements
    - No usability: Control cannot be implemented as specified
    - Not applicable: Control is not relevant to the environment
"""

import asyncio
import os
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from pydantic import BaseModel


@dataclass
class Policy:
    name: str
    description: str
    settings: Dict[str, str]


class AgentResponseJSON(BaseModel):
 status: str
 # list of policy names that address this control
 relevant_policies: List[str]
 # "Brief explanation of assessment reasoning and any gaps identified"
 explanation: str

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
                response_format=AgentResponseJSON   
            )
            
            # Initialize the agent
            self.agent = AssistantAgent(
                name="security_assessor",
                model_client=self.model_client,
                system_message="You are a security policy assessment expert. Provide precise, evidence-based evaluations.",
                model_client_stream=True,
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


    async def assess_control(self, ism_title: str, ism_description: str) -> Tuple[str, List[str]]:
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
            return "Not Assessed", []

        # Build a precise prompt with clear instructions
        prompt = f"""
        Task: Analyze if the following ISM (Information Security Manual) control is adequately addressed by the provided policies.
        
        ISM Control:
        Title: {ism_title}
        Description: {ism_description}
        
        Available Policies:
        {self.policies}
        
        Assessment Criteria:
        1. Coverage - Do the policies fully address the control requirements?
        2. Implementation - Are the policy settings specific and actionable?
        3. Effectiveness - Do the policies provide adequate security measures?
        4. Gaps - Are there any missing elements or concerns?
        
        Response Format (JSON):
        {{
            "status": "one of: {', '.join(self.implementation_statuses)}",
            "relevant_policies": ["list of policy names that address this control"],
            "explanation": "Brief explanation of assessment reasoning and any gaps identified"
        }}
        """
        
        try:
            # Process the stream and accumulate the response
            response_chunks = []
            try:
                from autogen_agentchat.messages import TextMessage
                async for event in self.agent.run_stream(task=prompt):
                    if isinstance(event, TextMessage):
                        if event.content and event.content.strip():
                            response_chunks.append(event.content)
                    elif isinstance(event, dict) and 'content' in event and event['content']:
                        response_chunks.append(event['content'])
                    elif isinstance(event, str) and event.strip():
                        response_chunks.append(event)

            except Exception as e:
                print(f"Error during stream processing: {str(e)}")
                raise
                    
            if not response_chunks:
                print("Debug: No chunks collected")  # Debug print
                raise ValueError("No response received from agent")

            # Combine all chunks into a complete response
            response_content = ' '.join(response_chunks)
            print(f"Debug: Full response: {response_content}")  # Debug print
            
            if not response_content:
                raise ValueError("No valid response content received from agent")

            # Find the JSON content within the response
            # Look for content between curly braces as the response might include additional text
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No valid JSON found in response")
                
            json_content = response_content[start_idx:end_idx + 1]
            
            # Parse and validate the response
            result = json.loads(json_content)
            
            if "status" not in result or "relevant_policies" not in result:
                raise ValueError("Missing required fields in API response")
                
            if result["status"] not in self.implementation_statuses:
                raise ValueError(f"Invalid status: {result['status']}")
                
            return result["status"], result["relevant_policies"]
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response: {e}")
            return "Not Assessed", []
        except (ValueError, KeyError) as e:
            print(f"Invalid LLM response format: {e}")
            return "Not Assessed", []
        except Exception as e:
            print(f"Error during LLM assessment: {str(e)}")
            return "Not Assessed", []

async def assess_ism_control(
    ism_title: str, 
    ism_description: str, 
    policy_file: str = "asdbpsc-dsc-entra.txt"
) -> Tuple[str, List[str]]:
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
    try:
        assessor = ISMControlAssessor(policy_file)
        await assessor.initialize()
        
        try:
            return await assessor.assess_control(ism_title, ism_description)
        finally:
            await assessor.cleanup()
    except Exception as e:
        print(f"Failed to assess ISM control: {str(e)}")
        return "Not Assessed", []

def run_assessment(
    ism_title: str, 
    ism_description: str, 
    policy_file: str = "asdbpsc-dsc-entra.txt"
) -> Tuple[str, List[str]]:
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

