# Loop Engineering Architecture - Skills Engine

## Purpose
Store and retrieve project-specific knowledge, conventions, and instructions for agents.

## Key Interfaces

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml
import json
from datetime import datetime

@dataclass
class Skill:
    name: str
    description: str
    version: str
    instructions: str
    triggers: List[str]
    scripts: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None

class SkillsEngine:
    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = Path(skills_dir)
        self.skill_registry: Dict[str, Skill] = {}
        self._load_all_skills()
    
    def _load_all_skills(self):
        """Load all skills from skills directory"""
        if not self.skills_dir.exists():
            return
        
        for skill_file in self.skills_dir.glob("**/SKILL.md"):
            try:
                skill = self._parse_skill_file(skill_file)
                if skill:
                    self.skill_registry[skill.name] = skill
            except Exception as e:
                print(f"Error loading skill {skill_file}: {e}")
    
    def _parse_skill_file(self, skill_path: Path) -> Optional[Skill]:
        """Parse a skill file (YAML frontmatter + Markdown content)"""
        content = skill_path.read_text()
        
        # Split YAML frontmatter and markdown content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                markdown_content = parts[2].strip()
                
                # Parse YAML
                metadata = yaml.safe_load(yaml_content)
                
                return Skill(
                    name=metadata.get("name", skill_path.parent.name),
                    description=metadata.get("description", ""),
                    version=metadata.get("version", "1.0"),
                    instructions=markdown_content,
                    triggers=metadata.get("triggers", []),
                    scripts=metadata.get("scripts", []),
                    metadata=metadata,
                    created_at=metadata.get("created_at"),
                    updated_at=metadata.get("updated_at")
                )
        
        # If no YAML frontmatter, use filename as name
        return Skill(
            name=skill_path.parent.name,
            description="",
            version="1.0",
            instructions=content,
            triggers=[]
        )
    
    def load_skill(self, skill_name: str) -> Optional[Skill]:
        """Load a skill by name"""
        return self.skill_registry.get(skill_name)
    
    def register_skill(self, skill: Skill):
        """Register a skill in the registry"""
        self.skill_registry[skill.name] = skill
    
    def get_relevant_skills(self, task_description: str) -> List[Skill]:
        """Find skills relevant to a given task"""
        relevant = []
        
        for skill in self.skill_registry.values():
            # Check if any trigger matches the task description
            for trigger in skill.triggers:
                if trigger.lower() in task_description.lower():
                    relevant.append(skill)
                    break
        
        # If no specific matches, return all skills (agent can decide relevance)
        if not relevant:
            return list(self.skill_registry.values())
        
        return relevant
    
    def create_skill_from_template(self, template: Dict[str, Any]) -> Skill:
        """Create a new skill from template"""
        skill = Skill(
            name=template["name"],
            description=template.get("description", ""),
            version=template.get("version", "1.0"),
            instructions=template.get("instructions", ""),
            triggers=template.get("triggers", []),
            scripts=template.get("scripts", []),
            metadata=template,
            created_at=datetime.now()
        )
        
        self.register_skill(skill)
        return skill
    
    def save_skill(self, skill: Skill, skill_dir: Path = None):
        """Save skill to filesystem"""
        if skill_dir is None:
            skill_dir = self.skills_dir / skill.name
        
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Create YAML frontmatter
        yaml_content = yaml.dump({
            "name": skill.name,
            "description": skill.description,
            "version": skill.version,
            "triggers": skill.triggers,
            "scripts": skill.scripts or [],
            "metadata": skill.metadata or {},
            "created_at": skill.created_at.isoformat() if skill.created_at else None,
            "updated_at": datetime.now().isoformat()
        }, default_flow_style=False)
        
        # Write SKILL.md file
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(f"---\n{yaml_content}---\n\n{skill.instructions}")
        
        # Save scripts if any
        if skill.scripts:
            for script in skill.scripts:
                if "content" in script:
                    script_file = skill_dir / script["name"]
                    script_file.write_text(script["content"])
                    script_file.chmod(0o755)  # Make executable
    
    def get_skill_context(self, skill: Skill) -> Dict[str, Any]:
        """Get skill context for agent consumption"""
        return {
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.instructions,
            "triggers": skill.triggers,
            "scripts": [s.get("name") for s in (skill.scripts or [])],
            "metadata": skill.metadata or {}
        }
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills"""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "triggers": skill.triggers,
                "version": skill.version
            }
            for skill in self.skill_registry.values()
        ]

# Example skill templates
SKILL_TEMPLATES = {
    "code_review": {
        "name": "code-review",
        "description": "Automated code review with security and performance checks",
        "version": "1.0",
        "triggers": ["review code", "check PR", "security scan"],
        "instructions": """
## Code Review Process

1. **Security Analysis**
   - Check for SQL injection vulnerabilities
   - Look for XSS vulnerabilities
   - Verify authentication and authorization
   - Check for sensitive data exposure

2. **Performance Review**
   - Identify N+1 query problems
   - Check for unnecessary database calls
   - Review algorithm complexity
   - Look for memory leaks

3. **Code Quality**
   - Verify naming conventions
   - Check for code duplication
   - Review error handling
   - Validate test coverage

4. **Best Practices**
   - Follow project coding standards
   - Check for proper documentation
   - Verify dependency management
        """,
        "scripts": [
            {
                "name": "security_scan",
                "command": "python scripts/security_scan.py",
                "timeout": 300
            }
        ]
    },
    
    "bug_fix": {
        "name": "bug-fix",
        "description": "Systematic bug detection and fixing",
        "version": "1.0",
        "triggers": ["fix bug", "debug issue", "resolve error"],
        "instructions": """
## Bug Fix Process

1. **Reproduce the Issue**
   - Understand the reported problem
   - Create minimal reproduction case
   - Identify affected components

2. **Root Cause Analysis**
   - Trace execution flow
   - Check recent changes
   - Review logs and error messages
   - Identify related issues

3. **Implement Fix**
   - Create targeted solution
   - Maintain backward compatibility
   - Add proper error handling
   - Update related documentation

4. **Verify Fix**
   - Run existing tests
   - Add new test cases
   - Perform regression testing
   - Check edge cases
        """,
        "scripts": []
    }
}
```

## Skill File Format

```yaml
# skills/code-review/SKILL.md
---
name: code-review
description: "Automated code review with security and performance checks"
version: 1.0
triggers:
  - "review code"
  - "check PR"
  - "security scan"
scripts:
  - name: security_scan
    command: "python scripts/security_scan.py"
    timeout: 300
  - name: lint_check
    command: "eslint ."
    timeout: 60
metadata:
  author: "loop-engineering"
  category: "code-quality"
  complexity: "intermediate"
---

## Code Review Process

1. **Security Analysis**
   - Check for SQL injection vulnerabilities
   - Look for XSS vulnerabilities
   - Verify authentication and authorization

2. **Performance Review**
   - Identify N+1 query problems
   - Check for unnecessary database calls
   - Review algorithm complexity

3. **Code Quality**
   - Verify naming conventions
   - Check for code duplication
   - Review error handling

4. **Best Practices**
   - Follow project coding standards
   - Check for proper documentation
   - Verify dependency management
```

## Implementation Notes

1. **Skill Discovery**: Skills are automatically loaded from the skills directory
2. **Trigger Matching**: Simple substring matching for trigger identification
3. **Versioning**: Skills support versioning for backward compatibility
4. **Extensibility**: Skills can include scripts for automated execution
5. **Context**: Skills provide context to agents for informed decision making

## Example Usage

```python
# Initialize skills engine
skills_engine = SkillsEngine("./skills")

# Load a specific skill
code_review_skill = skills_engine.load_skill("code-review")

# Get relevant skills for a task
skills = skills_engine.get_relevant_skills("review this pull request")

# Create a new skill
new_skill = skills_engine.create_skill_from_template({
    "name": "deployment-check",
    "description": "Pre-deployment validation",
    "triggers": ["deploy", "release"],
    "instructions": "## Deployment Checklist\n1. Run tests\n2. Check dependencies\n3. Verify configuration"
})

# Save skill to filesystem
skills_engine.save_skill(new_skill)
```
