#!/usr/bin/env python3
"""
简化的S3隔离配置管理脚本
专为测试设计，提供常用配置模板和快速上传功能
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import s3


class ConfigHelper:
    """配置管理助手"""
    
    def __init__(self, config_key: str = "isolation/config.json"):
        self.config_key = config_key
    
    def get_current_config(self):
        """获取当前S3配置"""
        try:
            config_content = s3.get_file_text_content(self.config_key)
            config = json.loads(config_content)
            print("📥 当前S3配置:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return config
        except Exception as e:
            print(f"❌ 获取配置失败: {e}")
            print("💡 可能是配置文件不存在，可以先上传一个配置")
            return None
    
    def _get_current_config_silent(self):
        """静默获取当前配置（不打印输出）"""
        try:
            config_content = s3.get_file_text_content(self.config_key)
            return json.loads(config_content)
        except:
            return None
    
    def upload_config(self, config: Dict):
        """上传配置到S3"""
        try:
            # 先获取当前版本号
            current_version = "1.0.0"  # 默认版本
            try:
                current_config = self._get_current_config_silent()
                if current_config and "version" in current_config:
                    current_version = current_config["version"]
                    print(f"📊 当前版本: {current_version}")
            except:
                print("🆕 未找到现有配置，使用默认版本")
            
            # 生成新版本号
            version_parts = current_version.split(".")
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            new_version = ".".join(version_parts)
            
            # 设置新版本和时间戳
            config["version"] = new_version
            config["last_updated"] = datetime.now().isoformat()
            
            # 上传到S3
            s3.upload_dict_content(config, self.config_key)
            print(f"✅ 配置已上传到S3，新版本: {new_version}")
            print(f"📤 上传的配置:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"❌ 上传配置失败: {e}")
    
    def upload_from_file(self, file_path: str):
        """从文件上传配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"📁 从文件加载配置: {file_path}")
            self.upload_config(config)
            
        except Exception as e:
            print(f"❌ 从文件上传失败: {e}")
    
    def get_empty_config(self) -> Dict:
        """空配置 - 清空所有隔离"""
        return {
            "spaces": {},
            "default_config": {
                "max_workers": 3,
                "callback_timeout": 300,
                "task_types": ["short", "long", "image", "docx"]
            }
        }
    
    def get_single_test_config(self) -> Dict:
        """单业务测试配置"""
        return {
            "spaces": {
                "test_space_001": {
                    "task_types": ["short", "long"],
                    "max_workers": 2,
                    "callback_timeout": 180
                }
            },
            "default_config": {
                "max_workers": 3,
                "callback_timeout": 300,
                "task_types": ["short", "long", "image", "docx"]
            }
        }
    
    def get_multi_test_config(self) -> Dict:
        """多业务测试配置"""
        return {
            "spaces": {
                "business_001": {
                    "task_types": ["short", "long"],
                    "max_workers": 2,
                    "callback_timeout": 180
                },
                "business_002": {
                    "task_types": ["image", "docx"],
                    "max_workers": 4,
                    "callback_timeout": 240
                },
                "high_priority": {
                    "task_types": ["short", "long", "image", "docx"],
                    "max_workers": 6,
                    "callback_timeout": 120
                }
            },
            "default_config": {
                "max_workers": 3,
                "callback_timeout": 300,
                "task_types": ["short", "long", "image", "docx"]
            }
        }
    
    def get_emergency_config(self) -> Dict:
        """紧急隔离配置 - 大流量业务隔离"""
        return {
            "spaces": {
                "emergency_business": {
                    "task_types": ["short", "long", "image", "docx"],
                    "max_workers": 8,
                    "callback_timeout": 600
                }
            },
            "default_config": {
                "max_workers": 3,
                "callback_timeout": 300,
                "task_types": ["short", "long", "image", "docx"]
            }
        }


def main():
    if len(sys.argv) < 2:
        print("🔧 S3隔离配置管理助手")
        print("\n用法:")
        print("  python scripts/config_helper.py show                # 查看当前配置")
        print("  python scripts/config_helper.py upload empty        # 上传空配置(清空隔离)")
        print("  python scripts/config_helper.py upload single       # 上传单业务测试配置")
        print("  python scripts/config_helper.py upload multi        # 上传多业务测试配置")
        print("  python scripts/config_helper.py upload emergency    # 上传紧急隔离配置")
        print("  python scripts/config_helper.py upload-file <file>  # 从文件上传配置")
        print("\n配置模板:")
        print("  empty     - 清空所有业务隔离")
        print("  single    - 隔离一个测试业务(test_space_001)")
        print("  multi     - 隔离多个业务进行测试")
        print("  emergency - 紧急大流量业务隔离")
        return
    
    helper = ConfigHelper()
    command = sys.argv[1]
    
    if command == "show":
        helper.get_current_config()
    
    elif command == "upload":
        if len(sys.argv) < 3:
            print("❌ 请指定配置模板: empty, single, multi, emergency")
            return
        
        template = sys.argv[2]
        config_map = {
            "empty": helper.get_empty_config(),
            "single": helper.get_single_test_config(),
            "multi": helper.get_multi_test_config(),
            "emergency": helper.get_emergency_config()
        }
        
        if template not in config_map:
            print(f"❌ 未知的配置模板: {template}")
            print("💡 可用模板: empty, single, multi, emergency")
            return
        
        config = config_map[template]
        print(f"🚀 上传配置模板: {template}")
        helper.upload_config(config)
    
    elif command == "upload-file":
        if len(sys.argv) < 3:
            print("❌ 请指定配置文件路径")
            return
        
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return
        
        helper.upload_from_file(file_path)
    
    else:
        print(f"❌ 未知命令: {command}")
        print("💡 使用 'python scripts/config_helper.py' 查看帮助")


if __name__ == "__main__":
    main()