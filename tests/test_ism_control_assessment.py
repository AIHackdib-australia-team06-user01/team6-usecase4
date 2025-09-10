import unittest
from agents.ism_control_assessment_tool import assess_ism_control, ISMControlAssessor

class TestISMControlAssessment(unittest.TestCase):
    def setUp(self):
        self.policy_file = "agents/asdbpsc-dsc-entra.txt"

    def test_basic_assessment(self):
        """Test basic assessment functionality"""
        status, policies = assess_ism_control(
            "Password Policy",
            "Ensure strong password requirements are enforced",
            self.policy_file
        )
        self.assertIn(status, ISMControlAssessor(self.policy_file).implementation_statuses)
        self.assertIsInstance(policies, list)

    def test_no_relevant_policies(self):
        """Test assessment when no relevant policies exist"""
        status, policies = assess_ism_control(
            "Nonexistent Control",
            "This control does not match any policies",
            self.policy_file
        )
        self.assertEqual(status, "Not Assessed")
        self.assertEqual(len(policies), 0)

if __name__ == '__main__':
    unittest.main()
