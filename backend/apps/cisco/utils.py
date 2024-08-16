import itertools
import uuid
import json
import logging
import os
import re
import string
from typing import Any, Dict, Union
from tqdm import tqdm

from apps.webui.models.datatype import DataType


def sort_devices(device_name):
    """This function sorts the devices based on device_name and returns the proper device name in its stead to be used in other functions"""

    device_name_upper_str = device_name.upper()
    all_devices_List = {
        "Catalyst 1200 Series": [
            "CATALYST 1200",
            "Catalyst 1200",
            "Cat 1200",
            "C1200-8T-D",
            "C1200-8T-E-2G",
            "C1200-8P-E-2G",
            "C1200-8FP-E-2G",
            "C1200-16T-2G",
            "C1200-16P-2G",
            "C1200-24T-4G",
            "C1200-24P-4G",
            "C1200-24FP-4G",
            "C1200-24T-4X",
            "C1200-24P-4X",
            "C1200-24FP-4X",
            "C1200-48T-4G",
            "C1200-48P-4G",
            "C1200-48FP-4X",
            "C1200-48T-4X",
            "C1200-48P-4X",
            "C1200-48FP-4X",
        ],
        "Catalyst 1300 Series": [
            "Catalyst 1300",
            "C1300-8T-D",
            "Cat 1300",
            "C1300-8T-E-2G",
            "C1300-8P-E-2G",
            "C1300-8FP-2G",
            "C1300-16T-2G",
            "C1300-16P-2G",
            "C1300-16FP-2G",
            "C1300-16P-4X",
            "C1300-24T-4G",
            "C1300-24P-4G",
            "C1300-24FP-4G",
            "C1300-24T-4X",
            "C1300-24P-4X",
            "C1300-24FP-4X",
            "C1300-48T-4X",
            "C1300-48P-4X",
            "C1300-48FP-4X",
        ],
        "Cisco Business 110 Series Unmanaged Switches": [
            "CBS110-5T-D",
            "CBS110-8T-D",
            "CBS110-8PP-D",
            "CBS110-16T",
            "CBS110-16PP",
            "CBS110-24T",
            "CBS110-24PP",
            "CBS110-8PP-D",
            "CBS110-16PP",
            "CBS110-24PP",
        ],
        "Cisco Business 220 Series Smart Switches": [
            "CBS220",
            "Cisco Business 220 Series Smart Switches",
            "CBS220-8T-E-2G",
            "CBS220-8P-E-2G",
            "CBS220-8FP-E-2G",
            "CBS220-16T-2G",
            "CBS220-16P-2G",
            "CBS220-24T-4G",
            "CBS220-24P-4G",
            "CBS220-24FP-4G",
            "CBS220-48T-4G",
            "CBS220-48P-4G",
            "CBS220-24T-4X",
            "CBS220-24P-4X",
            "CBS220-24FP-4X",
            "CBS220-48T-4X",
            "CBS220-48P-4X",
            "CBS220-48FP-4X",
        ],
        "Cisco Business 250 Series Smart Switches": [
            "CBS250",
            "Cisco Business 250 Series Smart Switches",
            "cbs250",
            " CBS250-8T-D",
            "CBS250-8PP-D",
            "CBS250-8T-E-2G",
            "CBS250-8PP-E-2G",
            "CBS250-8P-E-2G",
            "CBS250-8FP-E-2G",
            "CBS250-16T-2G",
            "CBS250-16P-2G",
            "CBS250-24T-4G",
            "CBS250-24PP-4G",
            "CBS250-24P-4G",
            "CBS250-24FP-4G",
            "CBS250-48T-4G",
            "CBS250-48PP-4G",
            "CBS250-48P-4G",
            "CBS250-24T-4X",
            "CBS250-24P-4X",
            "CBS250-24FP-4X",
            "CBS250-48T-4X",
            "CBS250-48P-4X",
        ],
        "Cisco Business 350 Series Managed Switches": [
            "CBS350",
            "Cisco Business 350 Series Managed Switches",
            " CBS350-8T-E-2G",
            "CBS350-8P-2G",
            "CBS350-8P-E-2G",
            "CBS350-8FP-2G",
            "CBS350-8FP-E-2G",
            "CBS350-8S-E-2G",
            "CBS350-16T-2G",
            "CBS350-16T-E-2G",
            "CBS350-16P-2G",
            "CBS350-16P-E-2G",
            "CBS350-16FP-2G",
            "CBS350-24T-4G",
            "CBS350-24P-4G",
            "CBS350-24FP-4G",
            "CBS350-24S-4G",
            "CBS350-48T-4G",
            "CBS350-48P-4G",
            "CBS350-48FP-4G",
            "CBS350-24T-4X",
            "CBS350-24P-4X",
            "CBS350-24FP-4X",
            "CBS350-48T-4X",
            "CBS350-48P-4X",
            "CBS350-48FP-4X",
            "CBS350-8MGP-2X",
            "CBS350-8MP-2X",
            "CBS350-24MGP-4X",
            "CBS350-12NP-4X",
            "CBS350-24NGP-4X",
            "CBS350-48NGP-4X",
            "CBS350-8XT",
            "CBS350-12XS",
            "CBS350-12XT",
            "CBS350-16XTS",
            "CBS350-24XS",
            "CBS350-24XT",
            "CBS350-24XTS",
            "CBS350-48XT-4X",
            "Cisco Business Switch",
        ],
        "Cisco Small Business 200 Series Smart Switches": [
            "200",
            "Cisco Small Business 200 Series Smart Switches",
            "sf250",
            "SG200",
            "SF200",
            "SG200-50",
            "SG200-50P",
            "SG200-50FP",
            "SG200-26",
            "SG200-26P",
            "SG200-26FP",
            "SG200-18",
            "SG200-10FP",
            "SG200-08",
            "SG200-08P",
            "SF200-24",
            "SF200-24P",
            "SF200-24FP",
            "SF200-48",
            "SF200-48P",
        ],
        "Cisco 220 Series Smart Switches": [
            "220",
            "SG220",
            "Cisco 220 Series Smart Switches",
            " SF220-48P",
            "SF220-48",
            "SF220-24P",
            "SF220-24",
            "SG220-50P",
            "SG220-50",
            "SG220-26P",
            "SG220-26",
        ],
        "Cisco 250 Series Smart Switches": [
            "250",
            "Cisco 250 Series Smart Switches",
            "SG250",
            "SF250",
            "SF250-24",
            "SF250-24P",
            "SF250-48",
            "SF250-48HP",
            "SG250X-24",
            "SG250X-24P",
            "SG250X-48",
            "SG250X-48P",
            "SG250-08",
            "SG250-08HP",
            "SG250-10P",
            "SG250-18",
            "SG250-26",
            "SG250-26HP",
            "SG250-26P",
            "SG250-50",
            "SG250-50HP",
            "SG250-50P",
        ],
        "Cisco Small Business 300 Series Managed Switches": [
            "300",
            "SF302",
            "SG302",
            "SF300",
            "SG300",
            "Cisco Small Business 300 Series Managed Switches",
            "SRW208-K9-NA",
            "SRW208-K9-G5",
            "SG300-10SFPK9UK-RF",
            "SRW208-K9-NA-RF",
            "SRW208-K9-AU",
            "SRW208-K9-G5-WS",
            "SRW208-K9-NA-WS",
            "SRW208-K9-G5-RF",
            "SRW208-K9-CN",
            "SRW208-K9-CN-RF",
            "SRW208-K9-AU-RF",
            "SG300-10SFP-K9-UK",
            "SRW208-K9-JP",
            " SF302-08PP",
            "SF302-08MPP",
            "SG300-10PP",
            "SG300-10MPP",
            "SF300-24PP",
            "SF300-48PP",
            "SG300-28PP",
            "SF300-08",
            "SF300-48P",
            "SG300-10MP",
            "SG300-10P",
            "SG300-10",
            "SG300-28P",
            "SF300-24P",
            "SF302-08MP",
            "SG300-28",
            "SF300-48",
            "SG300-20",
            "SF302-08P",
            "SG300-52",
            "SF300-24",
            "SF302-08",
            "SF300-24MP",
            "SG300-10SFP",
            "SG300-28MP",
            "SG300-52P",
            "SG300-52MP",
        ],
        "Cisco 350 Series Managed Switches": [
            "350",
            "SG350-8PD",
            "SG355",
            "SF350",
            "SG350",
            "Cisco 350 Series Managed Switches",
            "SF350-48",
            "SF350-48P",
            "SF350-48MP",
            "SG350-10",
            "SG350-10P",
            "SG350-10MP",
            "SG355-10P",
            "SG350-28",
            "SG350-28P",
            "SG350-28MP",
        ],
        "Cisco 350X Series Stackable Managed Switches": [
            "350X",
            "Cisco 350X Series Stackable Managed Switches",
            "SG350X",
            "SG350XG",
            "SG350XG-2F10",
            "SG350XG-24F",
            "SG350XG-24T",
            "SG350XG-48T",
            "SG350X-24",
            "SG350X-24P",
            "SG350X-24MP",
            "SG350X-48",
            "SG350X-48P",
            "SG350X-48MP",
            "SX350X-12",
        ],
        "Cisco 500 Series Stackable Managed Switches": [
            "SG500",
            "sg500",
            "Cisco 500 Series Managed Switches",
            "SG500X",
            "SG500X-24MPP",
        ],
        "Cisco 550 Series Stackable Managed Switches": [
            "sg550x",
            "Cisco 550 Series Managed Switches",
        ],
        "Cisco 550X Series Stackable Managed Switches": [
            "SG550",
            "550x",
            "550X",
            "Cisco 550X Series Stackable Managed Switches",
            "SG550XG",
            "SG550X",
            "SG550XG-8F8T",
            "SG550XG-24F",
            "SG550XG-24T",
            "SG550X-48T",
            "SG550X-24",
            "SG550X-24P",
            "SG550X-24MP",
            "SG550X-24MPP",
            "SG550X-48",
            "SG550X-48P",
            "SG550X-48MP",
            "SF550X-24",
            "SF550X-24P",
            "SF550X-24MP",
            "SF550X-48",
            "SF550X-48P",
            "SF550X-48MP",
            "SX550X-24",
        ],
        "RV100 Product Family": [
            "RV100",
            "RV110W",
            "RV110W-A-NA-K9",
            "RV110W-A-NA-K9-RF",
            "RV110W-E-G5-K9-RF",
            "RV110W-E-G5-K9",
            "RV110W-A-NA-K9-WS",
            "RV110W-E-G5-K9-WS",
            "RV110W-A-CA-K9",
            "RV110W-A-AU-K9",
            "RV110W-A-AR-K9",
            "RV110W-A-NA",
            "RFSW-ADVUSSWTCH-WS",
            "RV110W-E-CN-K9",
            "RV134W",
            "RV132W",
        ],
        "Cisco RV160 VPN Router": [
            "RV160W",
            "RV160W Wireless-AC VPN Router",
            "RV160",
            "Cisco RV160 VPN Router",
            "Small Business RV160 VPN Routers",
            "RV160-K9-NA",
            "RV160-K9-G5",
            "RV160-K9-AU",
            "RV160-K9-AR",
            "RV160-K9-BR",
            "RV160-K9-CN",
            "RV160-K9-IN",
            "RV160-K9-JP",
            "RV160-K9-KR",
            "RV160-K8-RU",
            "RV160W",
            "RV160W-A-K9-NA",
            "RV160W-E-K9-G5",
            "RV160W-A-K9-AU",
            "RV160W-A-K9-AR",
            "RV160W-A-K9-BR",
            "RV160W-C-K9-CN",
            "RV160W-I-K9-IN",
            "RV160W-E-K9-JP",
            "RV160W-R-K8-RU",
        ],
        "Cisco RV260 VPN Router": [
            "Cisco RV260 VPN Router",
            "RV260W VPN router",
            "RV260P",
            "RV260 VPN Router",
            "RV260W",
            "RV260",
            "RV260-K9-NA",
            "RV260P-K9-NA",
            "RV260-K9-G5",
            "RV260P-K9-G5",
            "RV260-K9-AU",
            "RV260P-K9-AU",
            "RV260-K9-AR",
            "RV260P-K9-AR",
            "RV260-K9-BR",
            "RV260P-K9-BR",
            "RV260-K9-CN",
            "RV260P-K9-CN",
            "RV260-K9-IN",
            "RV260P-K9-IN",
            "RV260-K9-JP",
            "RV260P-K9-JP",
            "R260-K9-KR",
            "R260P-K9-KR",
            "RV260-K8-RU",
            "RV260P-K8-RU",
            "RV260W-A-K9-NA",
            "RV260W-E-K9-G5",
            "RV260W-A-K9-AU",
            "RV260W-A-K9-AR",
            "RV260W-A-K9-BR",
            "RV260W-C-K9-CN",
            "RV260W-I-K9-IN",
            "RV260W-E-K9-JP",
            "RV260W-R-K8-RU",
        ],
        "RV320 Product Family": [
            "RV320",
            "RV320-K9-NA",
            "RV320 Dual WAN VPN Router",
            "RV320-K9-G5",
            "RV320-K9-AU",
            "RV320-K9-CN",
            "RV320-K9-AR",
            "RV320",
            "RV325",
            "RV320 WF",
            "RV325 WF",
            " RV320-WB-K9-NA-WS",
            "RV320-CN-K9",
            "RV320-K9-G5-RF",
            "RV320-K9-NA",
            "RV320-K9-AU",
            "RV320-K9-AR",
            "RV320-G5-K9",
            "RV320-K9-NA-WS",
            "RV320-K9-CN",
            "RV320-3YRBUN",
            "RV320-K9-AR-RF",
            "RV320-K8-RU",
            "RV320-K9-CN-WS",
            "RV320-AU-K9",
            "RV320-K9-IN",
            "RV320-NA-K9",
            "RV320-WB-K9-NA",
            "RV320-K9-IN-RF",
            "RV320-K9-AU-RF",
            "RV320-3YRBUN-K9-NA",
            "RV320-K9-G5-WS",
            "RV320-WB-K8-RU",
            "RV320-K9-CN-RF",
            "RV320-AR-K9",
            "RV320-K9-NA-RF",
            "RV320-K9-G5",
            "RV320-WB-K9-NA",
            "RV320-WB-K8-RU",
            "RV320-WB-K9-G5-RF",
            "RV320-WB-K8-RU-RF",
            "RV320-K9-AR-RF",
            "RV320-K8-RU",
            "RV320-WB-K9-G5",
            "RV320-WB-K9-NA-RF",
            "RV325-K9-AU",
            "RV325-K9-NA-RF",
            "RV325-CN-K9",
            "RV325-WB-K9-NA",
            "RV325-K9-AR",
            "RV325-K9-NA",
            "RV325-K9-IN",
            "RV325-K8-RU",
            "RV325-K9-AR-RF",
            "RV325-AU-K9",
            "RV325-K9-CN",
            "RV325-K9-G5-WS",
            "RV325-K9-CN-RF",
            "RV325-NA-K9",
            "RV325-K9-G5",
            "RV325-K9-AR-WS",
            "RV325-G5-K9",
            "RV325-K9-G5-RF",
            "RV325-K9-AU-RF",
            "RV325-WB-K9-NA-WS",
            "RV325-AR-K9",
            "RV325-K9-NA-WS",
            "RV325-WB-K8-RU",
            "RV325-K9-IN",
            "RV325-K8-RU",
            "RV325-WB-K9-G5",
            "RV325-WB-K9-G5-RF",
            "RV325-WB-K9-NA",
            "RV325-WB-K8-RU",
            "RV325-WB-K9-NA-RF",
        ],
        "RV340 Product Family": [
            "RV340 Product Family",
            "RV340",
            "RV345",
            "RV345P",
            "RV340W",
            "LS-RV34X-SEC-1YR=",
            "RV340W-A-K9-NA",
            "RV340-K9-NA",
            "RV345-K9-NA",
            "RV345P-K9-N",
            "RV340W-E-K9-G5",
            "RV340W-E-K9-AU",
            "RV340-K9-AU",
            "RV345-K9-AU",
            "RV345P-K9-AU",
            "RV340-K9-G5",
            "RV345-K9-G5",
            "RV345P-K9-G5",
            "RV340-K9-CN",
            "RV345-K9-CN",
            "RV345P-K9-CN",
            "RV340W-C-K9-IN",
            "RV340-K9-IN",
            "RV345-K9-IN",
            "RV345P-K9-IN",
            "RV340-K9-AR",
            "RV345-K9-AR",
            "RV345P-K9-AR",
            "RV340-K9-BR",
            "RV345-K9-BR",
            "RV345P-K9-BR",
            "RV340-K8-RU",
            "RV345-K8-RU",
            "RV345P-K8-RU",
        ],
        "Cisco Business Wireless AX": [
            "CBW AX",
            "Wifi6",
            "802.11AX",
            "CBW150",
            "CBW150AX",
            "CBW 150",
            "CBW151AXM",
            "CBW151",
            "cbw 151",
            "CBW150AXM",
        ],
        "Cisco Business Wireless AC": [
            "CBW",
            "CBW",
            "CBW100",
            "5-CBW240AC-Q",
            "5-CBW240AC-R",
            "5-CBW240AC-S",
            "5-CBW240AC-T",
            "5-CBW240AC-Z",
            "5-CBW240AC-A",
            "5-CBW240AC-B",
            "5-CBW240AC-D",
            "5-CBW240AC-A-CA",
            "5-CBW240AC-I",
            "5-CBW240AC-K",
            "5-CBW240AC-E",
            "5-CBW240AC-F",
            "3-CBW240AC-A-CA",
            "5-CBW240AC-G",
            "5-CBW240AC-H",
            "3-CBW240AC-K",
            "3-CBW240AC-R",
            "3-CBW240AC-Q",
            "3-CBW240AC-T",
            "3-CBW240AC-S",
            "3-CBW240AC-Z",
            "CBW240AC-A-CA",
            "3-CBW240AC-B",
            "3-CBW240AC-A",
            "3-CBW240AC-D",
            "3-CBW240AC-F",
            "3-CBW240AC-E",
            "3-CBW240AC-H",
            "3-CBW240AC-G",
            "3-CBW240AC-I",
            "CBW145AC-A-CA",
            "CBW140AC-I",
            "CBW140AC-H",
            "CBW140AC-G",
            "CBW140AC-F",
            "CBW140MXS-F-EU",
            "CBW140AC-K",
            "CBW140AC-Q",
            "CBW140MXS-B-NA",
            "CBW140MXS-E-UK",
            "CBW140AC-T",
            "CBW140AC-S",
            "CBW140AC-R",
            "CBW140MXS-R-EU",
            "CBW140AC-E",
            "CBW140MXS-Z-AU",
            "CBW140AC-D",
            "CBW140AC-B",
            "CBW140MXS-H-CN",
            "CBW140MXS-E-EU",
            "5-CBW140AC-A-CA",
            "CBW140MXS-A-NA",
            "3-CBW140-A-CA",
            "CBW140MXS-I-EU",
            "3-CBW140AC-G",
            "3-CBW140AC-F",
            "3-CBW141ACM-E-EU",
            "3-CBW140AC-E",
            "3-CBW140AC-D",
            "3-CBW140AC-K",
            "CBW140MXS-K-UK",
            "3-CBW140AC-I",
            "3-CBW140AC-H",
            "CBW141ACM-A-CA",
            "3-CBW140AC-B",
            "3-CBW140AC-A",
            "CBW140MXS-S-UK",
            "3-CBW140AC-T",
            "3-CBW140AC-Z",
            "CBW140MXS-D-IN",
            "3-CBW140AC-S",
            "3-CBW140AC-R",
            "3-CBW140AC-Q",
            "CBW140AC-A-CA",
            "5-CBW140AC-K",
            "5-CBW140AC-H",
            "5-CBW140AC-I",
            "5-CBW140AC-F",
            "5-CBW140AC-G",
            "5-CBW140AC-D",
            "5-CBW140AC-E",
            "5-CBW140AC-B",
            "5-CBW140AC-A",
            "5-CBW140AC-Z",
            "3-CBW140AC-A-CA",
            "CBW140MXS-A-CA",
            "CBW140AC-Z",
            "5-CBW140AC-T",
            "5-CBW140AC-R",
            "5-CBW140AC-S",
            "5-CBW140AC-Q",
            "CBW140MXS-S-EU",
            "CISCO BUSINESS WIRELESS 240 ACCESS POINT",
            "CBW 240AC",
            "240AC",
            "CISCO BUSINESS WIRELESS 240",
            "BUSINESS WIRELESS 240 ",
            "CBW240",
            "CBW 240",
            "CBW-240",
            "CISCO BUSINESS 240AC WI-FI ACCESS POINT",
            "CBW240AC ACCESS POINT",
            "CISCO BUSINESS 200 SERIES",
            "CBW240AC",
            "CISCO BUSINESS 240AC ACCESS POINT",
            "CISCO BUSINESS WIRELESS 141 MESH EXTENDER",
            "CBW 141ACM",
            "CISCO BUSINESS WIRELESS 141",
            "BUSINESS WIRELESS 141 ",
            "CBW141",
            "CBW 141",
            "CBW-141",
            "CISCO BUSINESS 141ACM WI-FI MESH EXTENDER",
            "CBW141ACM MESH EXTENDER",
            "CISCO BUSINESS 100 SERIES",
            "CBW141ACM",
            "CISCO BUSINESS 141ACM MESH EXTENDER",
            "CISCO BUSINESS 100 SERIES MESH EXTENDERS",
            "CISCO BUSINESS WIRELESS 142 MESH EXTENDER",
            "CBW 142ACM",
            "CISCO BUSINESS WIRELESS 142",
            "BUSINESS WIRELESS 142 ",
            "CBW142",
            "CBW 142",
            "CBW-142",
            "CISCO BUSINESS 142ACM WI-FI MESH EXTENDER",
            "CBW142ACM MESH EXTENDER",
            "CISCO BUSINESS 100 SERIES",
            "CBW142ACM",
            "CISCO BUSINESS 142ACM MESH EXTENDER",
            "CISCO BUSINESS 100 SERIES MESH EXTENDERS",
            "CISCO BUSINESS WIRELESS 143 MESH EXTENDER",
            "CBW 143ACM",
            "CISCO BUSINESS WIRELESS 143",
            "BUSINESS WIRELESS 143",
            "CBW143",
            "CBW 143",
            "CBW-143",
            "CISCO BUSINESS 143ACM WI-FI MESH EXTENDER",
            "CBW143ACM MESH EXTENDER",
            "CISCO BUSINESS 100 SERIES",
            "CBW143ACM",
            "CISCO BUSINESS 143ACM MESH EXTENDER",
            "CISCO BUSINESS 100 SERIES MESH EXTENDERS",
            "CISCO BUSINESS WIRELESS 140 ACCESS POINT",
            "CBW 140AC",
            "CISCO BUSINESS WIRELESS 140",
            "BUSINESS WIRELESS 140",
            "CBW140",
            "CBW 140",
            "CBW-140",
            "CISCO BUSINESS 140AC WI-FI ACCESS POINT",
            "CBW140AC ACCESS POINT",
            "CISCO BUSINESS 100 SERIES",
            "CBW140AC",
            "CISCO BUSINESS 140AC ACCESS POINT",
            "CISCO BUSINESS WIRELESS 145 ACCESS POINT",
            "CBW 145AC",
            "CISCO BUSINESS WIRELESS 145",
            "BUSINESS WIRELESS 145",
            "CBW145",
            "CBW 145",
            "CBW-145",
            "CISCO BUSINESS 145AC WI-FI ACCESS POINT",
            "CBW145AC ACCESS POINT",
            "CISCO BUSINESS 100 SERIES",
            "CBW145AC",
            "CISCO BUSINESS 145AC ACCESS POINT",
        ],
        "Cisco Small Business 500 Series Wireless Access Points": [
            "WAP500",
            "WAP571",
            "WAP571E",
            "WAP581",
            "Cisco WAP581 Wireless-AC Dual Radio Wave 2 Access Point with 2.5GbE LAN",
            "WAP571-I-K9-WS",
            "WAP571E-A-K9-WS",
            "WAP571E-R-K9",
            "WAP571-I-K9",
            "WAP571E-A-K9-RF",
            "WAP571E-A-K9",
            "WAP571E-E-K9",
            "WAP571E-E-K9-RF",
            "WAP551-A-K9",
            "WAP551-E-K9-WS",
            "WAP551-N-K9",
            "WAP551-R-K9",
            "WAP551-C-K9-RF",
            "WAP551-A-K9-WS",
            "WAP551-K-K9",
            "WAP551-E-K9",
            "WAP551-C-K9",
            "WAP551-A-K9-RF",
            "WAP551-E-K9-RF",
            "WAP561-R-K9",
            "WAP561-A-K9-RF",
            "WAP561-E-K9-RF",
            "WAP561-A-K9-WS",
            "WAP561-E-K9-WS",
            "WAP561-C-K9-RF",
            "WAP561-A-K9",
            "CP-HS-WL-561NEU-RF",
            "WAP561-K-K9",
            "WAP561-N-K9",
            "WAP561-C-K9",
            "WAP561-E-K9",
            "WAP581-J-K9",
            "WAP581-I-K9",
            "WAP581-B-K9-RF",
            "WAP581-K-K9",
            "WAP581-E-K9-RF",
            "WAP581-N-K9",
            "WAP581-B-K9",
            "WAP581-A-K9",
            "WAP581-C-K9",
            "WAP581-E-K9",
        ],
        "Cisco Small Business 300 Series Wireless Access Points": [
            "WAP300",
            "WAP351",
            "WAP361",
            "WAP371",
            "WAP321",
            "WAP351-C-K9",
            "WAP351-A-K9",
            "WAP321-E-K9-WS",
            "WAP351-C-K9-RF",
            "WAP351-E-K9",
            "WAP351-E-K9-RF",
            "WAP321-C-K9-RF",
            "WAP321-A-K9",
            "WAP321-C-K9",
            "WAP321-A-K9-WS",
            "WAP351-A-K9-RF",
            "WAP321-E-K9-RF",
            "WAP321-E-K9",
            "WAP321-A-K9-RF",
            "WAP371-C-K9-RF",
            "WAP371-C-K9",
            "WAP371-E-K9-RF",
            "WAP371-E-K9",
            "WAP371-K-K9",
            "WAP371-A-K9",
            "WAP371-E-K9-WS",
            "WAP371-K-K9-RF",
        ],
        "Cisco Small Business 100 Series Wireless Access Points": [
            "WAP125",
            "WAP150",
            "WAP100",
            "WAP125-A-K9-BR",
            "WAP125-E-K9-IN",
            "WAP125-A-K9-AR",
            "WAP125-A-K9-NA",
            "WAP125-A-K9-AU",
            "WAP125-C-K9-G5",
            "WAP125-C-K9-CN",
            "WAP125-A-K9-NA-RF",
            "WAP125-E-K9-UK-RF",
            "WAP125-E-K9-EU",
            "WAP125-C-K9-IN",
            "WAP125-E-K9-UK",
            "WAP125-K-K9-KR",
            "WAP125-J-K9-JP",
            "WAP125-E-K9-EU-RF",
            "WAP121-A-K9-CA",
            "WAP121-E-K9-AR",
            "WAP121-E-K9-G5",
            "WAP121-A-K9-AU",
            "WAP121-E-K9-G5-WS",
            "WAP121-A-K9-NA",
            "WAP121-A-K9-AR",
            "WAP121-A-K9-NA-RF",
            "WAP121-E-K9-G5-RF",
            "WAP121-E-K9-CN",
            "WAP121-A-K9-AU-RF",
            "WAP121-E-K9-IN-RF",
            "WAP121-E-K9-IN",
        ],
        "Cisco Small Business SPA300 Series IP Phones": [
            "SPA300",
            "SPA301",
            "SPA303",
            " SPA301-G1",
            "SPA301-G1-WS",
            "TRD-CISCO-SPA3XX",
            "SPA301-G3",
            "SPA301-G3-WS",
            "SPA301-G2-WS",
            "SPA301-G2",
            "SPA301-G4",
            "SPA301-G1-RF",
            "SPA301-G3-RF",
            "SPA301-G2-RF",
        ],
        "Cisco Small Business SPA500 Series IP Phones": [
            "SPA500",
            "SPA500S",
            "SPA500DS",
            "SPA501G",
            "SPA502G",
            "SPA504G",
            "SPA508G",
            "SPA509G",
            "SPA512G",
            "SPA514G",
            "SPA525G2",
            " SPA525G2-RF",
            "SPA525G2-RC-WS",
            "SPA525G",
            "SPA525G2-TLS",
            "SPA525G2-XU",
            "SPA500S",
            "SPA525G2-EU-RF",
            "SPA500DS-WS",
            "SPA525G2-EU-RC",
            "SPA525G2",
            "SPA500DS",
            "CP-500-HANDSET=",
            "TRD-CISCO-SPA-5XX",
            "SPA500S-RF",
            "SPA525G2-WS",
            "SPA525G2-RC-RF",
            "CP-500-HANDSET",
            "CP-500-WALLMOUNT=",
            "SPA525G-WS",
            "SPA500DS-RF",
            "SPA525G2-EU-WS",
            "SPA500-HANDSET=",
            "CP-500-PWRSUPPLY",
            "CP-500-WALLMOUNT",
            "SPA500S-WS",
            "SPA525G2-EU",
            "SPA525G2-RC",
        ],
        "Cisco IP Phone 6800 Series with Multiplatform Firmware": [
            "CP6800",
            "CP6821",
            "CP6841",
            "CP6851",
            "6821",
            "6841",
            "6851",
            "6851 Key Expansion Module",
        ],
        "Cisco IP Phone 7800 Series": [
            "CP7800",
            "Cisco IP Phone 7811",
            "Cisco IP Phone 7821",
            "Cisco IP Phone 7832 ",
            "Cisco IP Phone 7841",
            "Cisco IP Phone 7861",
            " EA-UC-PHASE-UPG",
            "LIC-UWL-STD-C",
            "CP-7811-3PW-K9=",
            "CP-7811-K9",
            "EA-UC-FULL-MIG-USR",
            "CP-7811-3PW-UK-K9=",
            "CP-7811-ATT-RC-K9=",
            "EA-UC-PROD-MIG-USR",
            "CP-DX-HS=",
            "CP-7800-HS-HOOK=",
            "CP-7800-B-BEZEL=",
            "CP-7811-K9++=",
            "CP-7811-K9-RF",
            "CP-7811-3PCC-K9++=",
            "R-EA-UC-K9-BUNDLE",
            "CP-7811-3PWNAK9-RF",
            "CP-7811-FS=",
            "CP-7811-ATT-NA-K9=",
            "CP-7811-3PCC-K9-RF",
            "CP-7800-S-BEZEL=",
            "CP-7811-3PW-RW-K9=",
            "CP-7811-3PCC-K9-WS",
            "CP-7811-3PCC-K9=",
            "EA-UC-SUB-MIG-USR",
            "CP-7811-3PW-NA-K9=",
            "R-CBE6K-K9",
            "CP-7800-HS-CORD=",
            "CP-DX-HS-NB=",
            "CP-7811-3PC-RC-K9=",
            "CP-DX-W-HS=",
            "CP-7800-FS=",
            "CP-7811-3PW-CE-K9=",
            "CP-7811-WMK=",
            "CP-7800-HS=",
            "CP-7811-NC-K9=",
            "LIC-UWL-PRO-A",
            "LIC-CUCM-11X-ENH-A",
            "EA-UC-NEW-USR",
            "CP-7811-K9=",
            "CP-7811-3PW-AU-K9=",
            "CP-7811-K9-WS",
            "CP-7800-WMK=",
            "CP-7811-3PW-RC-K9=",
        ],
        "Cisco IP Phone 8800 Series": [
            "CP8800",
            "Cisco IP Phone 8811",
            "Cisco IP Phone 8841",
            "Cisco IP Phone 8845",
            "Cisco IP Phone 8851",
            "Cisco IP Phone 8861",
            "Cisco IP Phone 8865",
            "CP-8811-3PW-CE-K9=",
            "CP-DX-HS=",
            "CP-8811-3PWNAK9-WS",
            "CP-8811-3PCC-K9-WS",
            "CP-8811-K9-WS",
            "CP-8811-3PC-RC-K9=",
            "CP-8811-ATT-RC-K9=",
            "CP-8800-VIDEO-WMK=",
            "CP-8811-ATT-NA-K9=",
            "CP-8800-A-KEM-WMK=",
            "CP-8800-S-VID-BZL=",
            "EA-UC-SUB-MIG-USR",
            "CP-8811-3PCC-K9=",
            "ECRR-FCC-NA",
            "CP-8811-3PW-K9=",
            "EA-UC-SUITE-K9",
            "CP-BEKEM-RF",
            "CP-DX-CORD=",
            "CP-8800-FS=",
            "CP-8800-B-VID-BZL=",
            "LIC-CUCM-11X-ENH-A",
            "CP-8800-WMK=",
            "A-FLEX-P-UCM-11X",
            "CP-8811-K9=",
            "CP-8811-A-K9-WS",
            "CP-8811-K9-RF",
            "CP-8811-3PCC-K9-RF",
            "CP-8800-BEKEM-WMK=",
            "CP-8811-A-K9=",
            "LIC-UWL-STD-C",
            "CP-8811-3PW-RW-K9=",
            "CP-BEKEM-WS",
            "EA-UC-FULL-MIG-USR",
            "LIC-CUCM-12X-ENH",
            "CP-8811-3PW-NA-K9=",
            "R-UCL-UCM-LIC-K9",
            "CP-8811-3PW-AU-K9=",
            "ISR4331-V/K9-WS",
            "CP-8800-S-BEZEL=",
            "CP-8811-3PW-RC-K9=",
            "ISR4331-V/K9",
            "CP-BEKEM",
            "CP-8811-K9",
            "CP-8811-NC-K9=",
            "CP-8811-W-K9-WS",
            "CP-8811-3PW-UK-K9=",
            "CP-8811-3PCC-K9++=",
            "CP-8811-A-K9-RF",
            "HCS-UC-K9-BUNDLE",
            "CP-DX-W-CORD=",
            "CP-8800-B-AGBEZEL=",
            "CP-DX-W-HS=",
            "CP-8811-W-K9=",
            "LIC-UWL-PRO-A",
            "CP-8811-W-K9-RF",
            "CP-8811-K9++=",
            "CP-8811-3PWNAK9-RF",
            "TRD-CISCO-CP-88XX",
            "CP-8800-S-AGBEZEL=",
        ],
        "Cisco Business Dashboard": [
            "CBD",
            "Cisco Business Dashboard",
            "Business Dashboard",
            "CISCO BUSINESS DASHBOARD",
        ],
        "Cisco Business Mobile App": [
            "CISCO BUSINESS MOBILE APP",
            "Cisco Business Mobile App",
            "CB Mobile app",
            "CB app",
            "Business Mobile App",
            "BUSINESS MOBILE APP",
        ],
        "Cisco FindIT Network Management": [
            "findit",
            "FindIt",
            "FindIT",
            "Manager",
            "MANAGER",
            "FindIT Network Management",
            "FINDIT",
        ],
    }
    print("device_name_upper_str from first for loop is:", device_name_upper_str)
    # Use the proper cisco name as a key to reference user input for device_name

    for device_key_proper_cisco_name in all_devices_List.keys():

        for item in all_devices_List[device_key_proper_cisco_name]:

            if device_name_upper_str in item:

                device_name = device_key_proper_cisco_name

                return device_name


def sort_families(device_name):
    """This function takes device_name as input to parse which family it belongs to"""
    device_family = ""
    switch_family_list = [
        "Cisco Business 110 Series Unmanaged Switches",
        "Cisco Business 220 Series Smart Switches",
        "Cisco Business 250 Series Smart Switches",
        "Cisco Business 350 Series Managed Switches",
        "Cisco Small Business 200 Series Smart Switches",
        "Cisco 220 Series Smart Switches",
        "Cisco 250 Series Smart Switches",
        "Cisco Small Business 300 Series Managed Switches",
        "Cisco 350 Series Managed Switches",
        "Cisco 350X Series Stackable Managed Switches",
        "Cisco 550X Series Stackable Managed Switches",
        "Catalyst 1200 Series",
        "Catalyst 1300 Series",
    ]
    router_family_list = [
        "RV100 Product Family",
        "Cisco RV160 VPN Router",
        "Cisco RV260 VPN Router",
        "RV320 Product Family",
        "RV340 Product Family",
    ]
    wireless_family_list = [
        "Cisco Business Wireless AC",
        "Cisco Business Wireless AX",
        "Cisco Business 100 Series Access Points",
        "Cisco Small Business Wireless",
        "Cisco Small Business 500 Series Wireless Access Points",
        "Cisco Small Business 300 Series Wireless Access Points",
        "Cisco Small Business 100 Series Wireless Access Points",
    ]
    voice_family_list = [
        "Cisco Small Business SPA300 Series IP Phones",
        "Cisco Small Business SPA500 Series IP Phones",
        "Cisco IP Phone 6800 Series with Multiplatform Firmware",
        "Cisco IP Phone 7800 Series",
        "Cisco IP Phone 8800 Series",
    ]
    network_management_list = [
        "Cisco Business Dashboard",
        "Cisco Business Mobile App",
        "Cisco FindIT Network Management",
    ]

    if device_name in switch_family_list:
        device_family = "Switch"
    elif device_name in router_family_list:
        device_family = "Router"
    elif device_name in wireless_family_list:
        device_family = "Wireless"
    elif device_name in voice_family_list:
        device_family = "Voice"
    elif device_name in network_management_list:
        device_family = "Network Management"

    return device_family


def remove_props_from_dict(mapp: Dict[str, Any], *props: str):
    for prop in props:
        mapp.pop(prop, None)
    return mapp


def format_source(source: str, limit: int = 20) -> str:
    """
    Format a string to only take the first x and last x letters.
    This makes it easier to display a URL, keeping familiarity while ensuring a consistent length.
    If the string is too short, it is not sliced.
    """
    if len(source) > 2 * limit:
        return source[:limit] + "..." + source[-limit:]
    return source


def is_readable(s):
    """
    Heuristic to determine if a string is "readable" (mostly contains printable characters and forms meaningful words)
    :param s: string
    :return: True if the string is more than 95% printable.
    """
    len_s = len(s)
    if len_s == 0:
        return False
    printable_chars = set(string.printable)
    printable_ratio = sum(c in printable_chars for c in s) / len_s
    return printable_ratio > 0.95  # 95% of characters are printable


def detect_datatype(source: Any) -> DataType:
    """
    Automatically detect the datatype of the given source.
    :param source: the source to base the detection on
    :return: data_type string
    """
    from urllib.parse import urlparse

    import requests
    import yaml

    def is_openapi_yaml(yaml_content):
        # currently the following two fields are required in openapi spec yaml config
        """Refer to https://swagger.io/specification/#schema
        openapi: 3.1.0
        Args:
            yaml_content: Valid yaml content
        Returns:
            bool: True if the yaml content contains all the required fields of OpenAPI yaml
        """
        return "openapi" in yaml_content and "info" in yaml_content

    def is_google_drive_folder(url):
        # checks if url is a Google Drive folder url against a regex
        regex = r"^drive\.google\.com\/drive\/(?:u\/\d+\/)folders\/([a-zA-Z0-9_-]+)$"
        return re.match(regex, url)

    try:
        if not isinstance(source, str):
            raise ValueError("Source is not a string and thus cannot be a URL.")
        url = urlparse(source)
        # Check if both scheme and netloc are present. Local file system URIs are acceptable too.
        if not all([url.scheme, url.netloc]) and url.scheme != "file":
            raise ValueError("Not a valid URL.")
    except ValueError:
        url = False

    formatted_source = format_source(str(source), 30)

    if url:
        YOUTUBE_ALLOWED_NETLOCKS = {
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "youtube.com",
            "vid.plus",
            "www.youtube-nocookie.com",
        }

        if url.netloc in YOUTUBE_ALLOWED_NETLOCKS:
            logging.debug(
                f"Source of `{formatted_source}` detected as `youtube_video`."
            )
            return DataType.YOUTUBE_VIDEO

        if url.path.endswith(".pdf"):
            logging.debug(f"Source of `{formatted_source}` detected as `pdf`.")
            return DataType.PDF

        if url.path.endswith(".xml"):
            logging.debug(f"Source of `{formatted_source}` detected as `sitemap`.")
            return DataType.SITEMAP

        if url.path.endswith(".csv"):
            logging.debug(f"Source of `{formatted_source}` detected as `csv`.")
            return DataType.CSV

        if url.path.endswith(".mdx") or url.path.endswith(".md"):
            logging.debug(f"Source of `{formatted_source}` detected as `mdx`.")
            return DataType.MDX

        if url.path.endswith(".docx"):
            logging.debug(f"Source of `{formatted_source}` detected as `docx`.")
            return DataType.DOCX

        if url.path.endswith(".yaml"):
            try:
                response = requests.get(source)
                response.raise_for_status()
                try:
                    yaml_content = yaml.safe_load(response.text)
                except yaml.YAMLError as exc:
                    logging.error(f"Error parsing YAML: {exc}")
                    raise TypeError(f"Not a valid data type. Error loading YAML: {exc}")

                if is_openapi_yaml(yaml_content):
                    logging.debug(
                        f"Source of `{formatted_source}` detected as `openapi`."
                    )
                    return DataType.OPENAPI
                else:
                    logging.error(
                        f"Source of `{formatted_source}` does not contain all the required \
                        fields of OpenAPI yaml. Check 'https://spec.openapis.org/oas/v3.1.0'"
                    )
                    raise TypeError(
                        "Not a valid data type. Check 'https://spec.openapis.org/oas/v3.1.0', \
                        make sure you have all the required fields in YAML config data"
                    )
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching URL {formatted_source}: {e}")

        if url.path.endswith(".json"):
            logging.debug(f"Source of `{formatted_source}` detected as `json`.")
            return DataType.JSON

        if is_google_drive_folder(url.netloc + url.path):
            logging.debug(f"Source of `{formatted_source}` detected as `google drive`.")
            return DataType.GOOGLE_DRIVE

        # If none of the above conditions are met, it's a general web page
        logging.debug(f"Source of `{formatted_source}` detected as `web_page`.")
        return DataType.WEB_PAGE

    elif not isinstance(source, str):
        # For datatypes where source is not a string.

        if (
            isinstance(source, tuple)
            and len(source) == 2
            and isinstance(source[0], str)
            and isinstance(source[1], str)
        ):
            logging.debug(f"Source of `{formatted_source}` detected as `qna_pair`.")
            return DataType.QNA_PAIR

        # Raise an error if it isn't a string and also not a valid non-string type (one of the previous).
        # We could stringify it, but it is better to raise an error and let the user decide how they want to do that.
        raise TypeError(
            "Source is not a string and a valid non-string type could not be detected. If you want to embed it, please stringify it, for instance by using `str(source)` or `(', ').join(source)`."  # noqa: E501
        )

    elif os.path.isfile(source):
        # For datatypes that support conventional file references.
        # Note: checking for string is not necessary anymore.

        if source.endswith(".docx"):
            logging.debug(f"Source of `{formatted_source}` detected as `docx`.")
            return DataType.DOCX

        if source.endswith(".csv"):
            logging.debug(f"Source of `{formatted_source}` detected as `csv`.")
            return DataType.CSV

        if source.endswith(".xml"):
            logging.debug(f"Source of `{formatted_source}` detected as `xml`.")
            return DataType.XML

        if source.endswith(".mdx") or source.endswith(".md"):
            logging.debug(f"Source of `{formatted_source}` detected as `mdx`.")
            return DataType.MDX

        if source.endswith(".txt"):
            logging.debug(f"Source of `{formatted_source}` detected as `text`.")
            return DataType.TEXT_FILE

        if source.endswith(".pdf"):
            logging.debug(f"Source of `{formatted_source}` detected as `pdf`.")
            return DataType.PDF

        if source.endswith(".yaml"):
            with open(source, "r") as file:
                yaml_content = yaml.safe_load(file)
                if is_openapi_yaml(yaml_content):
                    logging.debug(
                        f"Source of `{formatted_source}` detected as `openapi`."
                    )
                    return DataType.OPENAPI
                else:
                    logging.error(
                        f"Source of `{formatted_source}` does not contain all the required \
                                  fields of OpenAPI yaml. Check 'https://spec.openapis.org/oas/v3.1.0'"
                    )
                    raise ValueError(
                        "Invalid YAML data. Check 'https://spec.openapis.org/oas/v3.1.0', \
                        make sure to add all the required params"
                    )

        if source.endswith(".json"):
            logging.debug(f"Source of `{formatted_source}` detected as `json`.")
            return DataType.JSON

        if os.path.exists(source) and is_readable(open(source).read()):
            logging.debug(f"Source of `{formatted_source}` detected as `text_file`.")
            return DataType.TEXT_FILE

        # If the source is a valid file, that's not detectable as a type, an error is raised.
        # It does not fall back to text.
        raise ValueError(
            "Source points to a valid file, but based on the filename, no `data_type` can be detected. Please be aware, that not all data_types allow conventional file references, some require the use of the `file URI scheme`. Please refer to the embedchain documentation (https://docs.embedchain.ai/advanced/data_types#remote-data-types)."  # noqa: E501
        )

    else:
        # Source is not a URL.

        # TODO: check if source is gmail query

        # check if the source is valid json string
        if is_valid_json_string(source):
            logging.debug(f"Source of `{formatted_source}` detected as `json`.")
            return DataType.JSON

        # Use text as final fallback.
        logging.debug(f"Source of `{formatted_source}` detected as `text`.")
        return DataType.TEXT


# check if the source is valid json string
def is_valid_json_string(source: str):
    try:
        _ = json.loads(source)
        return True
    except json.JSONDecodeError:
        return False


def use_pysqlite3():
    """
    Swap std-lib sqlite3 with pysqlite3.
    """
    import platform
    import sqlite3

    if platform.system() == "Linux" and sqlite3.sqlite_version_info < (3, 35, 0):
        try:
            # According to the Chroma team, this patch only works on Linux
            import datetime
            import subprocess
            import sys

            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "pysqlite3-binary",
                    "--quiet",
                    "--disable-pip-version-check",
                ]
            )

            __import__("pysqlite3")
            sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

            # Let the user know what happened.
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            print(
                f"{current_time} [smbdevs] [INFO]",
                "Swapped std-lib sqlite3 with pysqlite3 for ChromaDb compatibility.",
                f"Your original version was {sqlite3.sqlite_version}.",
            )
        except Exception as e:
            # Escape all exceptions
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            print(
                f"{current_time} [smbdevs] [ERROR]",
                "Failed to swap std-lib sqlite3 with pysqlite3 for ChromaDb compatibility.",
                "Error:",
                e,
            )


from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from typing import List, Dict, Any


def tool_example_to_messages_helper(example: Dict[str, Any]) -> List[BaseMessage]:
    messages: List[BaseMessage] = [HumanMessage(content=example["question"])]
    openai_tool_calls = [
        {
            "id": str(uuid.uuid4()),
            "type": "function",
            "function": {
                "name": tool_call.__class__.__name__,
                "arguments": tool_call.json(),
            },
        }
        for tool_call in example["tool_calls"]
    ]
    messages.append(
        AIMessage(content="", additional_kwargs={"tool_calls": openai_tool_calls})
    )
    outputs = example.get("tool_outputs") or [
        "This is an example of a correct usage of this tool. Make sure to continue using the tool this way."
    ] * len(openai_tool_calls)

    messages.extend(
        ToolMessage(content=output, tool_call_id=tool_call["id"], name="Search")
        for output, tool_call in zip(outputs, openai_tool_calls)
    )

    return messages
