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
import re
import os
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient


@dataclass
class Policy:
    name: str
    description: str
    settings: Dict[str, str]

class ISMControlAssessor:
    def __init__(self, policy_file_path: str, api_key: Optional[str] = None):
        """
        Initialize the ISM Control Assessor.
        
        Args:
            policy_file_path: Path to the DSC policy file
            api_key: Optional API key for Azure OpenAI. If not provided, will use OPENAI_API_KEY env var
            
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
        # self.policies: List[Policy] = []
        self.policies: str = ""
        
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("API key must be provided either through constructor or OPENAI_API_KEY environment variable")
        self._api_key: str = api_key
        
    async def initialize(self):
        """Initialize the assessor asynchronously."""
        try:
        #     # Load policies first
        #     # self.policies = await self._load_policies()
        #     self.policies = str(self._read_file("utf-8"))
            
            # Initialize Azure OpenAI client
            self.model_client = AzureOpenAIChatCompletionClient(
                azure_deployment="gpt-5-mini",
                model="gpt-5-mini",
                api_version="2024-12-01-preview",
                azure_endpoint="https://aihac-mfbwdeld-eastus2.cognitiveservices.azure.com/",
                api_key=self._api_key,
            )
            
            # Initialize the agent
            self.agent = AssistantAgent(
                name="security_assessor",
                model_client=self.model_client,
                system_message="You are a security policy assessment expert. Provide precise, evidence-based evaluations.",
                model_client_stream=True,
            )
            
        #     # Test the connection
        #     await Console(self.agent.run_stream(task="test"))
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

    # async def _load_policies(self) -> List[Policy]:
    #     """Load and parse policies from the DSC configuration file asynchronously."""
    #     policies = []
    #     encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
    #     content = None

    #     # Use asyncio.to_thread for file I/O to prevent blocking
    #     for encoding in encodings:
    #         try:
    #             content = await asyncio.to_thread(self._read_file, encoding)
    #             if content is not None:
    #                 break
    #         except UnicodeDecodeError:
    #             continue

    #     if content is None:
    #         raise ValueError(f"Could not read file with any of the attempted encodings: {encodings}")

    #     try:
    #         # Process the content
    #         return await asyncio.to_thread(self._parse_policies, content)
    #     except Exception as e:
    #         print(f"Error loading policies: {str(e)}")
    #         return []

    def _read_file(self, encoding: str) -> Optional[str]:
        """Helper method to read file with given encoding."""
        try:
            with open(self.policy_file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            return None

    # def _parse_policies(self, content: str) -> List[Policy]:
    #     """Helper method to parse policies from content."""
    #     policies = []
    #     # Extract policy configurations using regex
    #     config_blocks = re.findall(r'(?s)(\w+)\s*{[^{]*?(?:{[^}]*}[^{]*)*}', content)
        
    #     for block in config_blocks:
    #         if block.strip() and not block.startswith(('Configuration', 'param')):
    #             # Parse settings within the block
    #             settings = {}
    #             settings_match = re.findall(r'(\w+)\s*=\s*["\']([^"\']*)["\']', block)
    #             for key, value in settings_match:
    #                 settings[key] = value
                
    #             policies.append(Policy(
    #                 name=block.split('{')[0].strip(),
    #                 description=settings.get('Description', ''),
    #                 settings=settings
    #             ))
    #     return policies

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
            
        # Prepare context for LLM
        # policies_context = "\n".join([
        #     f"Policy: {p.name}\nDescription: {p.description}\nSettings: {p.settings}"
        #     for p in self.policies
        # ])

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
            # Process the stream and get final result
            last_event = None
            async for event in self.agent.run_stream(task=prompt):
                last_event = event
                
            if not last_event:
                raise ValueError("No response received from agent")

            # Try to extract content from the event
            response_content = None
            if isinstance(last_event, dict):
                response_content = last_event.get('content')
            elif isinstance(last_event, str):
                response_content = last_event

            if not response_content:
                raise ValueError("No valid response content received from agent")

            # Parse and validate the response
            result = json.loads(response_content)
            
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

