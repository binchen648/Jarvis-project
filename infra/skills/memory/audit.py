from ..registry import BaseSkill, skill_registry

class MemoryAuditSkill(BaseSkill):
    name = "memory_audit"
    description = "审计用户记忆系统：检查记忆分布、过期记忆、缺失类型。帮助 Agent 理解记忆覆盖面。"
    parameters = {"type":"object","properties":{}}
    def run(self, user, **kwargs):
        return {"status":"placeholder","message":"Memory audit skill - not yet implemented"}
skill_registry.register(MemoryAuditSkill)
