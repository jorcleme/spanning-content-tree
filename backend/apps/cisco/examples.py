from apps.webui.models.articles import Search
from typing import List


def create_decomposition_search_examples() -> List[Search]:
    questions_subtopics = {
        "How do I create VLAN's on a Catalyst 1300?": [
            "How do I create VLAN's?",
            "How do I edit VLAN's?",
            "How do I delete VLAN's?",
        ],
        "How do I configure System Time Settings on a Catalyst 1300?": [
            "View System Time Settings",
            "Adjust System Time Settings",
            "Set System Time Settings",
            "Automate System Time Settings",
        ],
        "How do I configure MAC-Based VLAN Groups on a Catalyst 1300?": [
            "Create MAC-Based VLAN Groups",
            "Delete MAC-Based VLAN Groups",
        ],
        "How do I configure DHCP Image Upgrade Features?": [
            "Configure DHCP Auto Configuration Settings",
            "Configure DHCP Image Auto Update",
            "Configure SSH Settings for SCP",
            "Configure Backup Server Settings",
        ],
        "How do I configure LAG Settings through the CLI?": [
            "Configure LAG Settings",
            "What are the Link Aggregation Control Protocol (LACP) Commands",
            "What are the commands to verify Link Aggregation Group (LAG) is working?",
        ],
        "How do I enable Loopback Detection?": [
            "Enable Loopback Detection",
            "Enable Loopback Detection on a Port",
        ],
    }

    examples = [
        {
            "question": question,
            "tool_calls": [Search(query=question, subtopics=subtopics)],
        }
        for question, subtopics in questions_subtopics.items()
    ]

    return examples
