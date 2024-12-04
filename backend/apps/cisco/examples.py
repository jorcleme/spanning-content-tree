from apps.webui.models.articles import Search
from typing import List


def create_decomposition_search_examples() -> List[Search]:
    questions_subtopics = {
        "How do I create VLAN's on a Catalyst 1300?": [
            "Create VLANs",
            "Edit VLANs",
            "Delete VLANs",
        ],
        "I want to setup onboard packet capture on a Catalyst 1200": [
            "Commands for Configuring Capture Points",
            "Commands for Configuring Capture Buffer",
            "Capture Point Source Interface Settings",
            "Capture Filter Settings",
            "Starting and Stopping the Capture",
            "Saving the Packet Capture Data",
        ],
        "How do I Configure Simple Network Management Protocol (SNMP) Communities?": [
            "Configure SNMP Community on a Switch",
            "Manage SNMP Community",
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
            "LAG Settings",
            "Link Aggregation Control Protocol (LACP) Commands",
            "LAG Interface Settings",
            "LACP Port Priority",
        ],
        "How do I enable Loopback Detection?": [
            "Enable Loopback Detection",
            "Enable Loopback Detection on a Port",
        ],
        "How do I configure Radius Server?": [
            "Radius Server Global Settings",
            "Radius Client Settings",
            "Radius Server Keys",
            "Radius Server Groups",
            "Radius Server Users",
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
