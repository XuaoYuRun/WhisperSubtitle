#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境测试脚本：检查 PyQt5 是否能正常初始化"""
import sys
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    print("OK")
except Exception as e:
    print("ERROR: " + str(e))
    sys.exit(1)
