from django.db import models


class GraphNode(models.Model):
    NODE_TYPES = [
        ('goal', 'Goal'),
        ('skill', 'Skill'),
        ('interest', 'Interest'),
        ('memory', 'Memory'),
    ]
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='graph_nodes')
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    importance = models.FloatField(default=1.0)
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'graph_node'
        verbose_name = 'Graph Node'
        indexes = [
            models.Index(fields=['user', 'node_type']),
        ]
    
    def __str__(self):
        return f'[{self.node_type}] {self.title[:40]}'
