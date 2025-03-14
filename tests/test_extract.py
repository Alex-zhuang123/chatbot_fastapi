import os
import sys
import unittest
from unittest.mock import MagicMock
from graph import extract_key_developments


# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestExtractKeyDevelopments(unittest.TestCase):
    def test_extract_key_developments(self):
        # 测试 extract_key_developments 函数
        test_text = ["材料：碳钢，零件名称：法兰盘，图号：B-5678",
            "材质_不锈钢#图纸编号_X9Y9Z",
            "--- 零件组1 ---\n材料规格: 青铜; 零件号: 垫片-001\n*** 零件组2 ***\n部件名称：齿轮组"]
        # 调用被测试函数
        result = extract_key_developments(test_text)

        # 验证结果
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

if __name__ == "__main__":
    unittest.main()