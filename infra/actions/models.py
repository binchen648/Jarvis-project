from django.db import models


class RelationEdge(models.Model):
    RELATION_TYPES = [
        ('related', '相关'),
        ('prerequisite', '前置'),
        ('inspires', '启发'),
        ('contradicts', '矛盾'),
        ('custom', '自定义'),
    ]
    
    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='relation_edges', verbose_name='用户'
    )
    source_type = models.CharField(max_length=50, verbose_name='源类型')
    source_id = models.IntegerField(verbose_name='源ID')
    target_type = models.CharField(max_length=50, verbose_name='目标类型')
    target_id = models.IntegerField(verbose_name='目标ID')
    relation_type = models.CharField(
        max_length=20, choices=RELATION_TYPES, default='related', verbose_name='关系类型'
    )
    note = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'actions_relation_edge'
        verbose_name = '关联边'
        verbose_name_plural = '关联边'
        indexes = [
            models.Index(fields=['user', 'source_type', 'source_id']),
            models.Index(fields=['user', 'target_type', 'target_id']),
        ]
    
    def __str__(self):
        return f"{self.source_type}[{self.source_id}] → {self.target_type}[{self.target_id}]"
