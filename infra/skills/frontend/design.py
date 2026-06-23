from ..registry import BaseSkill, skill_registry

class FrontendDesignSkill(BaseSkill):
    name = "frontend_design"
    description = "审查前端 UI 设计一致性、组件复用性、用户体验。返回改进建议。"
    parameters = {"type":"object","properties":{"target":{"type":"string","description":"审查目标: template/CSS/page"}}}
    def run(self, user, **kwargs):
        return {"status":"placeholder","message":"Frontend design skill - not yet implemented"}
skill_registry.register(FrontendDesignSkill)
