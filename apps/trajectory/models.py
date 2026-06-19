from django.db import models


class TrajectoryEvent(models.Model):
    """成长轨迹事件."""
    EVENT_TYPES = [
        ('learning', '学习'),
        ('achievement', '成就'),
        ('reflection', '反思'),
        ('milestone', '里程碑'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='trajectory_events'
    )
    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPES, verbose_name='事件类型'
    )
    title = models.CharField(max_length=300, verbose_name='事件标题')
    description = models.TextField(blank=True, verbose_name='事件描述')
    happened_at = models.DateTimeField(verbose_name='发生时间')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trajectory_event'
        verbose_name = '成长轨迹'
        verbose_name_plural = '成长轨迹'
        ordering = ['-happened_at']

    def __str__(self):
        return f"{self.user} - {self.event_type} - {self.created_at}"


class SkillNode(models.Model):
    """技能节点（预置图谱）."""

    DIFFICULTY_CHOICES = [
        (1, '入门'),
        (2, '初级'),
        (3, '中级'),
        (4, '高级'),
        (5, '专家'),
    ]

    name = models.CharField(max_length=200, unique=True, verbose_name='技能名称')
    category = models.CharField(max_length=50, verbose_name='技能分类')
    difficulty = models.IntegerField(
        choices=DIFFICULTY_CHOICES, verbose_name='难度等级'
    )
    estimated_hours = models.IntegerField(verbose_name='预估学习时长(小时)')
    prerequisites = models.ManyToManyField(
        'self', symmetrical=False, blank=True, verbose_name='前置技能'
    )
    recommended_content = models.ManyToManyField(
        'content.ProcessedContent', blank=True, verbose_name='推荐内容'
    )
    learner_count = models.IntegerField(default=0, verbose_name='学习人数')
    avg_completion_rate = models.FloatField(
        null=True, blank=True, verbose_name='平均完成率'
    )

    class Meta:
        db_table = 'trajectory_skill_node'
        verbose_name = '技能节点'
        verbose_name_plural = '技能节点'
        ordering = ['category', 'difficulty', 'name']

    def __str__(self):
        return self.name


class UserLearningProgress(models.Model):
    """用户技能进度."""

    STATUS_CHOICES = [
        ('not_started', '未开始'),
        ('learning', '学习中'),
        ('completed', '已完成'),
        ('struggling', '有困难'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='learning_progress',
        verbose_name='用户',
    )
    skill = models.ForeignKey(
        SkillNode,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name='技能',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name='学习状态',
    )
    predicted_completion_days = models.FloatField(
        null=True, blank=True, verbose_name='预计完成天数'
    )

    class Meta:
        db_table = 'trajectory_user_learning_progress'
        verbose_name = '用户技能进度'
        verbose_name_plural = '用户技能进度'
        ordering = ['user', 'skill']
        unique_together = ['user', 'skill']
        indexes = [
            models.Index(fields=['user', 'status'], name='traj_progress_user_status'),
        ]

    def __str__(self):
        return f"{self.user} - {self.skill} ({self.get_status_display()})"


class LearningPath(models.Model):
    """个性化路径."""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='learning_paths',
        verbose_name='用户',
    )
    title = models.CharField(max_length=200, verbose_name='路径标题')
    goal_description = models.TextField(blank=True, verbose_name='目标描述')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'trajectory_learning_path'
        verbose_name = '学习路径'
        verbose_name_plural = '学习路径'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active'], name='traj_path_user_active'),
        ]

    def __str__(self):
        return self.title


class PathNode(models.Model):
    """路径节点."""

    STATUS_CHOICES = [
        ('pending', '待开始'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
    ]

    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='nodes',
        verbose_name='所属路径',
    )
    skill = models.ForeignKey(
        SkillNode,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='关联技能',
    )
    order = models.IntegerField(verbose_name='排序序号')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='完成状态',
    )
    estimated_minutes = models.IntegerField(default=0, verbose_name='预估耗时(分钟)')

    class Meta:
        db_table = 'trajectory_path_node'
        verbose_name = '路径节点'
        verbose_name_plural = '路径节点'
        ordering = ['path', 'order']

    def __str__(self):
        skill_name = self.skill.name if self.skill else '(已删除)'
        return f"{self.path} - {skill_name} (#{self.order})"


class UserInterest(models.Model):
    """用户兴趣标签 — 从行为事件聚合而来."""
    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='interests',
        verbose_name='用户'
    )
    tag = models.CharField(max_length=50, verbose_name='兴趣标签')
    weight = models.FloatField(default=1.0, verbose_name='兴趣权重(0-10)')
    source = models.CharField(
        max_length=30, blank=True,
        choices=[
            ('goal', '学习目标'), ('session', '学习记录'),
            ('content', '内容交互'), ('chat', '对话'),
            ('manual', '手动设置'),
        ],
        verbose_name='来源'
    )
    last_updated = models.DateTimeField(auto_now=True, verbose_name='最后更新')

    class Meta:
        db_table = 'trajectory_user_interest'
        verbose_name = '用户兴趣'
        verbose_name_plural = '用户兴趣'
        unique_together = ['user', 'tag']
        ordering = ['-weight']

    def __str__(self):
        return f"{self.user} - {self.tag} ({self.weight})"


class UserContentInteraction(models.Model):
    """用户内容交互记录 — 用于构建内容偏好."""
    ACTION_CHOICES = [
        ('bookmark', '收藏'),
        ('read', '已读'),
        ('block', '不感兴趣'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='content_interactions',
        verbose_name='用户'
    )
    content = models.ForeignKey(
        'content.ProcessedContent', on_delete=models.CASCADE, related_name='user_interactions',
        verbose_name='内容'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='交互动作')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='交互时间')

    class Meta:
        db_table = 'trajectory_content_interaction'
        verbose_name = '内容交互'
        verbose_name_plural = '内容交互'
        unique_together = ['user', 'content', 'action']

    def __str__(self):
        return f"{self.user} - {self.content} ({self.get_action_display()})"
