import unittest
import asyncio
import os

from agents.ism_control_assessment_tool import assess_ism_control, ISMControlAssessor

class TestISMControlAssessment(unittest.TestCase):
    def setUp(self):
        self.policy_file = "agents/asdbpsc-dsc-entra.txt"
        # Ensure test environment has required variables
        os.environ['OPENAI_API_KEY'] = 'test_key'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'

    async def async_test_basic_assessment(self):
        """Test basic assessment functionality"""
        status, policies = await assess_ism_control(
            "Password Policy",
            "Ensure strong password requirements are enforced",
            self.policy_file
        )
        self.assertIn(status, ISMControlAssessor(self.policy_file).implementation_statuses)
        self.assertIsInstance(policies, list)

    def test_basic_assessment(self):
        """Wrapper for async test"""
        asyncio.run(self.async_test_basic_assessment())

    async def async_test_no_relevant_policies(self):
        """Test assessment when no relevant policies exist"""
        status, policies = await assess_ism_control(
            "Nonexistent Control",
            "This control does not match any policies",
            self.policy_file
        )
        self.assertEqual(status, "Not Assessed")
        self.assertEqual(len(policies), 0)

    def test_no_relevant_policies(self):
        """Wrapper for async test"""
        asyncio.run(self.async_test_no_relevant_policies())

    def test_initialization(self):
        """Test assessor initialization with custom parameters"""
        assessor = ISMControlAssessor(
            self.policy_file,
            api_key="custom_key",
            azure_endpoint="https://custom.endpoint",
            azure_deployment="custom-model"
        )
        self.assertEqual(assessor._api_key, "custom_key")
        self.assertEqual(assessor._azure_endpoint, "https://custom.endpoint")
        self.assertEqual(assessor._azure_deployment, "custom-model")

if __name__ == '__main__':
    unittest.main()
