"""
Skill Registry — wraps ToolRegistry with structured skill definitions.

Skills are advanced tools that Agent can invoke. Unlike simple query tools,
skills may involve multi-step analysis, code generation, or cross-module
data aggregation.

Usage:
    from infra.skills.registry import skill_registry
    skill_registry.register("project_status", ProjectStatusSkill)
    result = skill_registry.execute("project_status", user=request.user)
"""
from tools.tools import _registry as tool_registry, Tool


class BaseSkill:
    """Base class for all skills."""
    
    name = ""
    description = ""
    parameters = {}
    
    def run(self, user, **kwargs):
        """Execute the skill. Override in subclasses."""
        raise NotImplementedError


class SkillRegistry:
    """Registry wrapping ToolRegistry with class-based skills."""
    
    def __init__(self):
        self._skills = {}
    
    def register(self, skill_cls):
        """Register a skill class into both SkillRegistry and ToolRegistry."""
        instance = skill_cls()
        self._skills[skill_cls.name] = instance
        
        # Create a Tool that wraps the skill's run method
        tool = Tool(
            name=skill_cls.name,
            description=skill_cls.description,
            parameters=skill_cls.parameters,
            execute=instance.run,
        )
        tool_registry.register(tool)
        return skill_cls
    
    def execute(self, name, user=None, **kwargs):
        """Execute a skill by name."""
        skill = self._skills.get(name)
        if not skill:
            return {"error": f"Skill '{name}' not found"}
        return skill.run(user=user, **kwargs)
    
    def list_skills(self):
        """List all registered skills."""
        return {name: {
            "description": cls.description,
            "parameters": cls.parameters,
        } for name, cls in self._skills.items()}


# Global instance
skill_registry = SkillRegistry()
