# 动态消费者系统

## 概述

动态消费者系统是基于S3的业务隔离解决方案，能够为特定业务空间创建专属的Kafka消费者，实现流量隔离和资源独立管理。

### 核心价值

- **业务隔离**: 防止某个业务的突发流量影响其他业务
- **动态配置**: 基于S3的热配置更新，无需重启服务
- **多实例同步**: 所有服务实例自动同步最新配置
- **弹性扩容**: 根据业务需要动态调整消费者资源

## 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   S3 配置中心   │────│  配置轮询检测    │────│  消费者管理器  │
│ isolation/      │    │ (30秒间隔)       │    │ 创建/停止/更新  │
│ config.json     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  配置变更回调    │    │ 隔离消费者实例  │
                       │ 版本检测/增量更新│    │ 专属线程池      │
                       └──────────────────┘    └─────────────────┘
```

### 核心组件

#### 1. IsolationConfigManager (isolation_config.py)
- **S3配置管理**: 配置上传/下载/验证
- **定时轮询**: 每30秒检查配置变更
- **版本管理**: 基于版本号的变更检测
- **回调机制**: 配置变更时触发消费者同步

#### 2. DynamicConsumerManager (dynamic_manager.py)
- **消费者生命周期**: 动态创建/停止/更新消费者
- **增量同步**: 智能对比配置，只更新变化部分
- **状态管理**: 维护隔离消费者的运行状态
- **线程池管理**: 独立的消费者线程池

## 配置格式

### S3配置文件结构

存储位置: `s3://bucket/isolation/config.json`

```json
{
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
    }
  },
  "default_config": {
    "max_workers": 3,
    "callback_timeout": 300,
    "task_types": ["short", "long", "image", "docx"]
  },
  "version": "1.0.3",
  "last_updated": "2024-01-01T12:00:00Z"
}
```

### 配置字段说明

#### spaces (业务空间配置)
- `task_types`: 处理的任务类型
  - `short`: 短文档任务
  - `long`: 长文档任务  
  - `image`: 图片处理任务
  - `docx`: Word文档转PDF任务
- `max_workers`: 最大工作线程数
- `callback_timeout`: 回调超时时间(秒)

#### 系统字段
- `default_config`: 默认配置模板
- `version`: 配置版本号 (变更检测关键)
- `last_updated`: 最后更新时间

## 使用指南

### 配置管理工具

使用 `scripts/config_helper.py` 进行配置管理：

#### 1. 查看当前配置
```bash
python scripts/config_helper.py show
```

#### 2. 快速配置模板
```bash
# 清空所有隔离
python scripts/config_helper.py upload empty

# 单业务测试
python scripts/config_helper.py upload single

# 多业务测试  
python scripts/config_helper.py upload multi

# 紧急大流量隔离
python scripts/config_helper.py upload emergency
```

#### 3. 自定义配置
```bash
# 从文件上传
python scripts/config_helper.py upload-file my_config.json
```

### 预设配置模板

#### empty - 清空隔离
```json
{
  "spaces": {},
  "default_config": {...}
}
```

#### single - 单业务测试
```json  
{
  "spaces": {
    "test_space_001": {
      "task_types": ["short", "long"],
      "max_workers": 2,
      "callback_timeout": 180
    }
  }
}
```

#### multi - 多业务测试
```json
{
  "spaces": {
    "business_001": {...},
    "business_002": {...},
    "high_priority": {...}
  }
}
```

#### emergency - 紧急隔离
```json
{
  "spaces": {
    "emergency_business": {
      "task_types": ["short", "long", "image", "docx"],
      "max_workers": 8,
      "callback_timeout": 600
    }
  }
}
```

## 运维操作

### 紧急业务隔离

当某个业务出现流量激增需要紧急隔离时：

1. **快速隔离**
   ```bash
   # 使用紧急模板
   python scripts/config_helper.py upload emergency
   
   # 或者自定义配置
   python scripts/config_helper.py upload-file emergency_config.json
   ```

2. **验证生效**
   - 查看服务日志确认配置更新
   - 观察隔离消费者创建成功
   ```
   S3 configuration changed, syncing consumers...
   Created isolated consumer for space=emergency_business, task_type=short
   ```

3. **流量恢复**
   ```bash
   # 恢复正常配置
   python scripts/config_helper.py upload empty
   ```

### 配置变更流程

1. **准备配置**: 创建或修改配置文件
2. **上传配置**: 使用工具上传到S3
3. **自动检测**: 系统30秒内检测到变更
4. **增量更新**: 自动创建/停止相关消费者
5. **验证结果**: 检查日志确认更新成功

### 配置回滚

```bash
# 方法1: 上传之前的配置文件
python scripts/config_helper.py upload-file backup_config.json

# 方法2: 使用预设模板回滚
python scripts/config_helper.py upload empty
```

## 开发接口

### 核心API

#### IsolationConfigManager
```python
from server.workers.dynamic.isolation_config import isolation_config_manager

# 获取隔离空间列表
spaces = isolation_config_manager.get_isolated_spaces()

# 获取空间配置
config = isolation_config_manager.get_space_config("business_001")

# 检查空间是否隔离
is_isolated = isolation_config_manager.is_space_isolated("business_001")

# 添加配置变更回调
def on_config_change(old_config, new_config):
    print(f"配置变更: {old_config} -> {new_config}")

isolation_config_manager.add_change_callback(on_config_change)
```

#### DynamicConsumerManager
```python
from server.workers.dynamic.dynamic_manager import dynamic_manager

# 创建隔离消费者
success = dynamic_manager.isolate_business(
    space_code="business_001",
    task_type="short", 
    max_workers=3,
    callback_timeout=300
)

# 停止隔离消费者  
success = dynamic_manager.stop_isolated_consumer("business_001")

# 获取消费者状态
status = dynamic_manager.get_status()

# 配置同步
from server.workers.dynamic.dynamic_manager import sync_with_s3_config
results = sync_with_s3_config(isolation_config_manager)
```

### 集成方式

系统在服务启动时自动初始化，无需手动调用：

```python
# 在 server/workers/__init__.py 中
def start_workers():
    # 启动动态消费者管理器
    dynamic_manager.initialize()
    
    # 启动S3配置管理器
    _start_config_manager()
```

### 扩展钩子

```python
# 添加自定义配置变更处理
def custom_config_handler(old_config, new_config):
    # 自定义处理逻辑
    pass

isolation_config_manager.add_change_callback(custom_config_handler)
```

## 监控和故障排查

### 关键日志

#### 配置更新日志
```
S3 configuration changed, syncing consumers...
Config changes detected: {'added': {'business_001'}, 'removed': set(), 'modified': set()}
Consumer sync results: {'add_business_001': True}
```

#### 消费者管理日志  
```
Created isolated consumer for space=business_001, task_type=short
Started isolated consumer topic=bella_file_api group_id=isolated_business_001_short
Stopped 2 isolated consumers for space: business_001
```

#### 错误日志
```
Error loading initial config: [Errno 2] No such file or directory
Failed to create consumer for space=business_001 task_type=invalid
Error checking config update: Invalid JSON format
```

### 常见问题

#### 1. 配置不生效
**症状**: 上传配置后没有看到消费者创建/停止日志

**排查步骤**:
1. 确认版本号是否更新
   ```bash
   python scripts/config_helper.py show
   ```
2. 检查S3连接和权限
3. 查看服务启动日志确认配置管理器已启动
4. 确认配置格式正确

#### 2. 轮询失败
**症状**: 日志显示 "Error checking config update"

**排查步骤**:
1. 检查S3访问权限
2. 验证配置文件JSON格式
3. 检查网络连接
4. 查看详细错误信息

#### 3. 消费者创建失败  
**症状**: "Failed to create consumer" 错误

**排查步骤**:
1. 检查任务类型是否有效 (short/long/image/docx)
2. 验证配置参数范围 (max_workers > 0)
3. 检查Kafka连接状态
4. 确认消费者类是否正确初始化

### 性能监控

#### 配置轮询性能
- 轮询间隔: 30秒 (可调整)
- S3请求频率: 每个实例每30秒1次请求
- 配置文件大小: 建议 < 1MB

#### 消费者资源使用
- 每个隔离空间独立线程池
- max_workers 建议范围: 1-10
- callback_timeout 建议范围: 60-600秒

## 最佳实践

### 配置管理
1. **版本控制**: 配置变更前备份当前版本
2. **渐进发布**: 先在测试环境验证配置
3. **监控观察**: 配置变更后观察系统表现
4. **快速回滚**: 准备应急配置文件

### 性能优化  
1. **合理配置**: 根据业务负载调整max_workers
2. **超时设置**: 根据任务复杂度设置callback_timeout
3. **资源监控**: 监控隔离消费者的CPU和内存使用
4. **定期清理**: 及时清理不再需要的隔离配置

### 安全注意事项
1. **访问控制**: 限制S3配置文件的访问权限
2. **配置验证**: 上传前验证配置格式和参数
3. **审计日志**: 记录配置变更的操作者和时间
4. **敏感信息**: 避免在配置中包含敏感数据

### 运维建议
1. **监控告警**: 设置配置更新失败的告警
2. **文档维护**: 保持配置变更记录
3. **培训普及**: 确保运维人员熟悉操作流程
4. **应急预案**: 准备系统异常时的应急配置

---

## 快速开始

1. **查看当前状态**
   ```bash
   python scripts/config_helper.py show
   ```

2. **测试基本功能**  
   ```bash
   python scripts/config_helper.py upload single
   ```

3. **观察系统日志**
   ```
   tail -f /applogs/app.log | grep "isolation\|consumer"
   ```

4. **清理测试配置**
   ```bash
   python scripts/config_helper.py upload empty
   ```

更多问题请参考项目文档或联系开发团队。