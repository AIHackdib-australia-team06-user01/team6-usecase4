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

import re
import os
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from autogen import OpenAIWrapper, config_list_from_json
from autogen.oai.openai_api import OpenAIError

@dataclass
class Policy:
    name: str
    description: str
    settings: Dict[str, str]

class ISMControlAssessor:
    def __init__(self, policy_file_path: str, config_path: Optional[str] = None):
        self.policy_file_path = policy_file_path
        self.implementation_statuses = [
            "Not Assessed", "Effective", "Alternate control", 
            "not implemented", "implemented", "ineffective", 
            "no usability", "not applicable"
        ]
        self.policies = self._load_policies()
        
        # Initialize OpenAI configuration
        if config_path and os.path.exists(config_path):
            config_list = config_list_from_json(config_path)
        else:
            # Default configuration using environment variable
            config_list = [
                {
                    'model': 'gpt-4',
                    'api_key': os.getenv('OPENAI_API_KEY'),
                }
            ]
        
        self.llm = OpenAIWrapper(config_list=config_list)

    def _load_policies(self) -> List[Policy]:
        """Load and parse policies from the DSC configuration file."""
        policies = []
        try:
            with open(self.policy_file_path, 'r') as f:
                content = f.read()
                # Extract policy configurations using regex
                # Look for configuration blocks in the DSC file
                config_blocks = re.findall(r'(?s)(\w+)\s*{[^{]*?(?:{[^}]*}[^{]*)*}', content)
                
                for block in config_blocks:
                    if block.strip() and not block.startswith(('Configuration', 'param')):
                        # Parse settings within the block
                        settings = {}
                        settings_match = re.findall(r'(\w+)\s*=\s*["\']([^"\']*)["\']', block)
                        for key, value in settings_match:
                            settings[key] = value
                        
                        policies.append(Policy(
                            name=block.split('{')[0].strip(),
                            description=settings.get('Description', ''),
                            settings=settings
                        ))
        except Exception as e:
            print(f"Error loading policies: {str(e)}")
            return []
        return policies

    def assess_control(self, ism_title: str, ism_description: str) -> Tuple[str, List[str]]:
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
            OpenAIError: If there's an issue with the OpenAI API call
        """
        if not self.policies:
            return "Not Assessed", []
            
        # Prepare context for LLM
        policies_context = "\n".join([
            f"Policy: {p.name}\nDescription: {p.description}\nSettings: {p.settings}"
            for p in self.policies
        ])
        
        # Build a precise prompt with clear instructions
        prompt = f"""
        Task: Analyze if the following ISM (Information Security Manual) control is adequately addressed by the provided policies.
        
        ISM Control:
        Title: {ism_title}
        Description: {ism_description}
        
        Available Policies:
        {policies_context}
        
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
            # Call OpenAI API with specific parameters for reliability
            response = self.llm.create(
                messages=[{
                    "role": "system",
                    "content": "You are a security policy assessment expert. Provide precise, evidence-based evaluations."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for more consistent responses
                max_tokens=1000
            )
            
            if not isinstance(response.choices[0].message.content, str):
                raise ValueError("Unexpected response format from OpenAI API")
                
            # Parse and validate the response
            assessment = json.loads(response.choices[0].message.content)
            
            if "status" not in assessment or "relevant_policies" not in assessment:
                raise ValueError("Missing required fields in LLM response")
                
            if assessment["status"] not in self.implementation_statuses:
                raise ValueError(f"Invalid status: {assessment['status']}")
                
            return assessment["status"], assessment["relevant_policies"]
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response: {e}")
            return "Not Assessed", []
        except (ValueError, KeyError) as e:
            print(f"Invalid LLM response format: {e}")
            return "Not Assessed", []
        except Exception as e:
            print(f"Error during LLM assessment: {str(e)}")
            return "Not Assessed", []

def assess_ism_control(ism_title: str, ism_description: str, policy_file: str = "asdbpsc-dsc-entra.txt") -> Tuple[str, List[str]]:
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
    """
    assessor = ISMControlAssessor(policy_file)
    return assessor.assess_control(ism_title, ism_description)
