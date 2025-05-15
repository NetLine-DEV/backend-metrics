from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

PERMISSOES_DASHBNOARDS = [
    ("admin", "Pode gerenciar grupos e usuários"),
    ("atendimento", "Acesso ao dashboard de atendimento"),
    ("direcao", "Acesso ao dashboard da direção"),
    ("faturamento", "Acesso ao dashboard de faturamento"),
    ("financeiro", "Acesso ao dashboard financeiro"),
    ("infraestrutura", "Acesso ao dashboard da infraestrutura"),
    ("instalacao", "Acesso ao dashboard da instalação"),
    ("marketing", "Acesso ao dashboard de marketing"),
    ("vendas", "Pode vizualizar dashboard de vendas"),
    ("ti", "Pode vizualizar dashboards de ti"),
]

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    groups = models.ManyToManyField(
        'CustomGroup',
        related_name="custom_user_groups",
        blank=True
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True
    )

    def __str__(self):
        return self.email

    class Meta:
        permissions = (
            PERMISSOES_DASHBNOARDS
        )

class CustomGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, primary_key=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.group.name