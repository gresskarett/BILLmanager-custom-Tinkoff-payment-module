"""
Базовая функциональность для реализации платежного модуля.
"""

from abc import ABC, abstractmethod
import os
import sys
import typing as t
import xml.etree.ElementTree as ET

import billmgr.db
import billmgr.exception
from billmgr.misc import MgrctlXml
