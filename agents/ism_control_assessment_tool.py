# Sub agent (autogen) that receives ism title and description and asdbpsc-dsc-entra.txt
# It then checks to see if ism is being met by policies asdbpsc-dsc-entra.txt
# output implementation status: ["Not Assessed" , "Effective",  "Alternate control", "not implemented", "implemented", "ineffective", "no usability", "not applicable"] , Policies: [list of policies]

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Policy:
    name: str
    description: str
    settings: Dict[str, str]

class ISMControlAssessor:
    def __init__(self, policy_file_path: str):
        self.policy_file_path = policy_file_path
        self.implementation_statuses = [
            "Not Assessed", "Effective", "Alternate control", 
            "not implemented", "implemented", "ineffective", 
            "no usability", "not applicable"
        ]
        self.policies = self._load_policies()

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
        Assess if an ISM control is being met by the policies.
        
        Args:
            ism_title: The title of the ISM control
            ism_description: The description of the ISM control
            
        Returns:
            Tuple containing:
            - implementation status
            - list of relevant policy names
        """
        relevant_policies = []
        keywords = self._extract_keywords(ism_title, ism_description)
        
        # Search for relevant policies based on keywords
        for policy in self.policies:
            policy_text = f"{policy.name} {policy.description} {' '.join(policy.settings.values())}"
            if any(keyword.lower() in policy_text.lower() for keyword in keywords):
                relevant_policies.append(policy.name)
        
        # Determine implementation status based on findings
        status = self._determine_status(relevant_policies, keywords)
        
        return status, relevant_policies

    def _extract_keywords(self, title: str, description: str) -> List[str]:
        """Extract important keywords from the ISM control title and description."""
        # Combine title and description
        text = f"{title} {description}"
        
        # Remove common words and split into keywords
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        keywords = [word for word in text.split() 
                   if word.lower() not in common_words and len(word) > 2]
        
        return keywords

    def _determine_status(self, relevant_policies: List[str], keywords: List[str]) -> str:
        """Determine the implementation status based on the findings."""
        if not relevant_policies:
            return "Not Assessed"
        
        # Count how many keywords are covered by the policies
        covered_keywords = set()
        for policy in self.policies:
            if policy.name in relevant_policies:
                policy_text = f"{policy.name} {policy.description} {' '.join(policy.settings.values())}"
                for keyword in keywords:
                    if keyword.lower() in policy_text.lower():
                        covered_keywords.add(keyword)
        
        coverage_ratio = len(covered_keywords) / len(keywords) if keywords else 0
        
        if coverage_ratio >= 0.8:
            return "Effective"
        elif coverage_ratio >= 0.5:
            return "implemented"
        elif coverage_ratio > 0:
            return "ineffective"
        else:
            return "not implemented"

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
